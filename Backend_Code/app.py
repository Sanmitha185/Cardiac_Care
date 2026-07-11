import os
import json
import re
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv

# --- CONFIGURATION & LOGGING ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# --- INITIALIZE SERVICES ---
try:
    # Aggressively strip spaces and quotes to prevent DNS (getaddrinfo) errors
    raw_supabase_url = os.environ.get("SUPABASE_URL", "").strip().strip('"').strip("'")
    raw_supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip().strip('"').strip("'")
    raw_nvidia_key = os.environ.get("NVIDIA_API_KEY", "").strip().strip('"').strip("'")

    if not raw_supabase_url or not raw_supabase_key:
        logger.critical("🚨 SUPABASE CREDENTIALS MISSING FROM .env")

    supabase: Client = create_client(raw_supabase_url, raw_supabase_key)

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=raw_nvidia_key
    )

    logger.info("✅ Core services initialized successfully.")
except Exception as e:
    logger.critical(f"🚨 FATAL ERROR initializing services: {e}")


def extract_json_from_text(text: str) -> dict:
    """Robust fallback to extract JSON and strip markdown backticks without breaking the UI regex."""
    try:
        clean_text = text.replace('```json', '').replace('```', '').strip()
        match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON Parsing Error: {e} | Raw text: {text[:100]}...")
        return None


def validate_ai_response(data: dict) -> bool:
    """Strict validation to ensure the AI gives us exactly what we need."""
    if not isinstance(data, dict):
        return False
    if "action" not in data or "message_to_patient" not in data:
        return False
    if data["action"] not in ["ASK_QUESTION", "GENERATE_REPORT"]:
        return False
    if data["action"] == "GENERATE_REPORT" and "report_data" not in data:
        return False
    return True


def call_ai_with_retry(messages, max_retries=3):
    """Retry system for AI reliability."""
    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model="meta/llama-3.3-70b-instruct",
                messages=messages,
                temperature=0.1,
                max_tokens=1500
            )

            raw_response = completion.choices[0].message.content.strip()
            parsed_data = extract_json_from_text(raw_response)

            if parsed_data and validate_ai_response(parsed_data):
                return parsed_data

            logger.warning(f"⚠️ Retry {attempt+1}: Invalid AI format. Forcing correction.")
            
            messages.append({
                "role": "user",
                "content": "SYSTEM NOTIFICATION: Your previous response was not a valid JSON object matching the exact schema. Try again and output ONLY pure JSON."
            })

        except Exception as e:
            logger.error(f"Retry API error: {e}")

    return None


# --- API ROUTES ---
@app.route('/api/patients', methods=['POST'])
def create_patient():
    try:
        res = supabase.table('patients').insert(request.json).execute()
        return jsonify({"status": "SUCCESS", "patient_id": res.data[0]['id']}), 201
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)}), 500


@app.route('/api/metrics', methods=['POST'])
def create_metrics():
    try:
        res = supabase.table('patient_health_metrics').insert(request.json).execute()
        return jsonify({"status": "SUCCESS", "metrics_id": res.data[0]['id']}), 201
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)}), 500


@app.route('/api/assessments/init', methods=['POST'])
def init_assessment():
    try:
        data = request.json

        payload = {
            "patient_id": data.get("patient_id"),
            "metrics_id": data.get("metrics_id"),
            "full_chat_transcript": [],
            "is_complete": False
        }

        res = supabase.table('assessments').insert(payload).execute()

        return jsonify({
            "status": "SUCCESS",
            "assessment_id": res.data[0]['id']
        }), 201

    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)}), 500


@app.route('/api/assessments/chat', methods=['POST'])
def chat_engine():
    try:
        body = request.json
        assessment_id = body.get('assessment_id')
        user_message = body.get('user_message', '').strip()

        # --- FETCH DB ---
        res = supabase.table('assessments') \
            .select('*, patients(*), patient_health_metrics(*)') \
            .eq('id', assessment_id).execute()

        if not res.data:
            return jsonify({"error": "Assessment not found"}), 404

        assessment = res.data[0]
        transcript = assessment.get('full_chat_transcript') or []

        # --- TURN LOGIC ---
        turn_count = len(transcript) // 2
        force_report = turn_count >= 10

        # --- THE MASTER SYSTEM PROMPT ---
        system_prompt = f"""You are an elite clinical triage AI engine operating inside a professional EMR system.
Patient Name: {assessment['patients'].get('full_name')}
Age: {assessment['patients'].get('age')}

YOUR INSTRUCTIONS:
You must conduct a human-like, empathetic triage interview. 
CRITICAL ANTI-DOUBLE-BARREL RULE: You are mathematically forbidden from asking multiple clinical concepts in a single sentence. You may only ask ONE specific question per turn. 

[CLINICAL PACING RULES - STRICT STATE SEPARATION]
You must progress through the interview in 5 distinct phases, UNLESS a life-threatening emergency is detected.

PHASE 1 (Severity & Quality State): You MUST begin your very first response with a highly empathetic statement (e.g., "I am so sorry to hear you are experiencing this..."). Validate their pain. Clarify the Quality (sharp/heavy/pressure) and explicitly ask for a 1-10 severity rating. WAIT FOR THE USER TO REPLY.
PHASE 2 (Isolated ASK_RADIATION State): ONLY ask if the pain moves or radiates anywhere (e.g., jaw, arm, neck). WAIT FOR THE USER TO REPLY.
PHASE 3 (Isolated ASK_PROVOCATION State): ONLY ask what makes the pain worse or better (e.g., exertion, breathing). WAIT FOR THE USER TO REPLY.
PHASE 4 (The SAMPLE History State): Ask about Past Medical History, Medications, AND Family History. 
PHASE 5 (Closing State): Politely close the interview and generate the report.

[DATA INTEGRITY PROTOCOLS & SAFETY LOCKS]
1. DYNAMIC ACUITY ESCALATION (Category A EMERGENCY): You possess the clinical autonomy of a senior cardiologist. Do NOT rely solely on the 1-10 severity score. You must autonomously escalate the triage_category_level to 'Category A (EMERGENCY)' and route to 'Emergency Room' if you detect a synergy of highly suspicious ACS indicators, such as:
   - Exertional worsening (Hallmark of Unstable Angina)
   - Heavy/Pressure-like pain
   - Radiation to jaw/arm/neck
   - New-onset pain combined with major risk factors (heavy smoking, past major surgeries)
   If ANY of these life-threatening indicators are detected, drop the checklist, skip remaining questions, and instantly trigger "GENERATE_REPORT" to save time.
2. THE NORMAL SAMPLE LOCK: If no Category A emergency is detected, you cannot trigger "GENERATE_REPORT" until Phase 4 is explicitly completed.
3. EXHAUSTIVE RISK EXTRACTION: When generating 'dynamic_risk_factors', you MUST meticulously extract EVERY single past surgery, chronic illness, and lifestyle factor (smoking/alcohol) mentioned by the patient. Do not drop surgical history.
4. ANTI-HALLUCINATION: For 'rating_1_to_10', ONLY output a number if the patient explicitly typed a digit. If they give a range, extract the maximum number.

[OUTPUT FORMATTING]
If you are continuing the interview (Phases 1-4), output a JSON object exactly like this:
{{
    "action": "ASK_QUESTION",
    "message_to_patient": "Your single, isolated, non-double-barreled follow-up question here."
}}

If you are generating the report (either normal completion OR emergency abort), output a JSON object exactly like this:
CRITICAL ACUITY-LINKED MESSAGE RULE:
- IF your triage_category_level is 'Category A (EMERGENCY)', set message_to_patient to EXACTLY: "Thank you for sharing. Due to the symptoms you described, I am immediately compiling your report for urgent review. Please prepare to seek emergency medical attention."
- IF your triage_category_level is 'Category B' or 'Category C', set message_to_patient to EXACTLY: "Thank you for sharing this crucial information. I am securely compiling your clinical summary now."

{{
    "action": "GENERATE_REPORT",
    "message_to_patient": "[Insert the EXACT message from the rule above based on your Category]",
    "report_data": {{
        "chest_pain_current": "Yes or No",
        "pain_duration": "Duration described by patient",
        "dynamic_symptoms_and_ratings": {{"symptom_name": {{"presence": "Yes", "rating_1_to_10": null}}}},
        "dynamic_risk_factors": {{"lifestyle_factor_or_past_surgery": "value"}},
        "triage_category_level": "Category A (EMERGENCY) / B / C",
        "calculated_risk_score_100": 85,
        "confidence_percentage": 90.5,
        "primary_suspected_pattern": "Specific Medical Diagnosis",
        "secondary_suspected_pattern": "Specific Medical Diagnosis",
        "critical_red_flags_identified": {{"flag": "clinical reason"}},
        "doctor_clinical_summary_text": "Patient reports... This pattern suggests...",
        "prognosis_risk_statement": "Probability statement...",
        "triage_routing_recommendation": "Emergency Room / Urgent Care / Outpatient"
    }}
}}

CRITICAL RULE: OUTPUT ONLY RAW, VALID JSON. DO NOT WRAP THE JSON IN MARKDOWN FORMATTING. NO OTHER TEXT."""

        messages = [{"role": "system", "content": system_prompt}]

        for msg in transcript:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })

        if force_report:
            messages.append({
                "role": "system",
                "content": "TURN LIMIT REACHED. FORCE ACTION: GENERATE_REPORT."
            })

        messages.append({"role": "user", "content": user_message})

        # 🔥 AI CALL WITH RETRY
        parsed_data = call_ai_with_retry(messages)

        # 🔥 FAIL SAFE
        if not parsed_data:
            logger.critical("🚨 AI FAILED TO RETURN VALID JSON AFTER 3 RETRIES")
            fallback_msg = "I'm sorry, I encountered a brief system error processing that. Could you please confirm how long you've been experiencing these symptoms?"
            return jsonify({"status": "SUCCESS", "ai_response": fallback_msg, "is_report": False}), 200

        # --- TRANSCRIPT UPDATE ---
        new_transcript = transcript.copy()
        new_transcript.append({"role": "user", "content": user_message})
        new_transcript.append({"role": "assistant", "content": parsed_data.get("message_to_patient", "Acknowledged.")})

        update_payload = {"full_chat_transcript": new_transcript}
        is_report = parsed_data.get("action") == "GENERATE_REPORT"

        if is_report and "report_data" in parsed_data:
            update_payload.update(parsed_data["report_data"])
            update_payload["is_complete"] = True

        supabase.table('assessments').update(update_payload).eq('id', assessment_id).execute()

        return jsonify({
            "status": "SUCCESS",
            "ai_response": parsed_data.get("message_to_patient"),
            "is_report": is_report
        }), 200

    except Exception as e:
        logger.critical(f"Server Exception: {e}", exc_info=True)
        return jsonify({"status": "SUCCESS", "ai_response": "System is stabilizing. Please continue.", "is_report": False}), 200


if __name__ == '__main__':
    logger.info("🚀 GACC-EWS Master Engine running on port 5000")
    app.run(port=5000, debug=True)