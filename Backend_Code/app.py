import os
import json
import random
import string
import logging
from typing import Any, Dict, List, Optional
import io
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

from services.nvidia_service import nvidia_service
from services.safety_engine import safety_engine, SafetyEvaluation
from services.scoring_service import scoring_service
from services.clinical_engine import clinical_engine, ClinicalState, StructuredClinicalReport
from services.hardware_service import hardware_service, ObservationSource
from services.rag_service import rag_service
from services.pdf_service import pdf_service

# --- CONFIGURATION & LOGGING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# --- INITIALIZE DATABASE ---
raw_supabase_url = os.environ.get("SUPABASE_URL", "").strip().strip('"').strip("'")
raw_supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip().strip('"').strip("'")
supabase: Optional[Client] = None

try:
    if raw_supabase_url and raw_supabase_key:
        supabase = create_client(raw_supabase_url, raw_supabase_key)
        logger.info("✅ Supabase client initialized successfully.")
    else:
        logger.warning("⚠️ SUPABASE CREDENTIALS MISSING FROM .env")
except Exception as e:
    logger.critical(f"🚨 Failed to initialize Supabase client: {e}")

# In-memory store for session continuity and active clinical states
memory_store: Dict[str, Dict[str, Any]] = {
    "patients": {},
    "metrics": {},
    "assessments": {},
    "clinical_states": {},
    "reports": {}
}

def generate_hospital_uhid() -> str:
    """Generate a realistic hospital UHID in CC-2026-XXXXXX format."""
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"CC-2026-{code}"

# --- ERROR HANDLERS ---
@app.errorhandler(404)
def handle_not_found(error):
    return jsonify({"status": "ERROR", "message": "The requested Cardiac Care service was not found."}), 404

@app.errorhandler(405)
def handle_method_not_allowed(error):
    return jsonify({"status": "ERROR", "message": "This action is not available for the requested service."}), 405

@app.errorhandler(500)
def handle_server_error(error):
    return jsonify({"status": "ERROR", "message": "The Cardiac Care service encountered an internal error."}), 500

# --- HEALTH & DIAGNOSTICS ROUTES ---
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "Cardiac Care Decision Support API",
        "supabase_configured": bool(supabase),
        "ai_configured": nvidia_service.is_configured,
        "primary_model": nvidia_service.active_primary_model
    }), 200

@app.route('/api/admin/diagnostics', methods=['GET'])
def admin_diagnostics():
    """Developer/admin diagnostics only. Does not expose secrets or sensitive patient data."""
    return jsonify({
        "status": "SUCCESS",
        "diagnostics": {
            **nvidia_service.get_diagnostics(),
            "supabase_connected": bool(supabase),
            "supported_clinical_dimensions": scoring_service.CORE_CLINICAL_DIMENSIONS,
            "cardiology_guideline_topics": [g.topic for g in rag_service.CARDIAC_KNOWLEDGE_BASE]
        }
    }), 200

# --- HARDWARE OBSERVATIONS INGESTION (PHASE 4 & 19) ---
@app.route('/api/device/observations', methods=['POST'])
def ingest_device_observations():
    """
    Hardware-Ready Ingestion Endpoint for future electronic cardiac devices.
    Accepts heart rate, SpO2, blood pressure, ECG telemetry, and temperature.
    """
    try:
        data = request.json or {}
        patient_id = data.get("patient_id")
        assessment_id = data.get("assessment_id")
        device_id = data.get("device_id", "UNKNOWN_DEVICE")
        observations_raw = data.get("observations", [])

        if not patient_id or not assessment_id or not observations_raw:
            return jsonify({
                "status": "ERROR",
                "message": "patient_id, assessment_id, and observations are required."
            }), 400

        validated, errors = hardware_service.ingest_observations(
            patient_id=patient_id,
            assessment_id=assessment_id,
            device_id=device_id,
            raw_observations=observations_raw
        )

        return jsonify({
            "status": "SUCCESS",
            "ingested_count": len(validated),
            "errors": errors,
            "observations": [obs.model_dump() for obs in validated]
        }), 201

    except Exception as e:
        logger.error(f"Error ingesting device observations: {e}")
        return jsonify({"status": "ERROR", "message": "Failed to ingest device observations."}), 500

# --- PATIENT & METRICS REGISTRATION ---
@app.route('/api/patients', methods=['POST'])
def create_patient():
    data = request.json or {}
    if not data.get('uhid') or str(data.get('uhid', '')).startswith('PT-'):
        data['uhid'] = generate_hospital_uhid()
    patient_uhid = data['uhid']

    db_payload = dict(data)
    if "name" in db_payload and "full_name" not in db_payload:
        db_payload["full_name"] = db_payload.pop("name")
    if "phone_number" in db_payload and "contact_number" not in db_payload:
        db_payload["contact_number"] = db_payload.pop("phone_number")
    if "emergency_contact_phone" in db_payload and "emergency_contact_number" not in db_payload:
        db_payload["emergency_contact_number"] = db_payload.pop("emergency_contact_phone")

    if not db_payload.get("full_name") or not db_payload.get("age") or not db_payload.get("gender"):
        return jsonify({"status": "ERROR", "message": "Please provide full name, age, and biological sex."}), 400

    patient_id = str(random.randint(10000000, 99999999))
    if supabase:
        try:
            res = supabase.table('patients').insert(db_payload).execute()
            if res.data:
                patient_id = res.data[0]['id']
        except Exception as e:
            logger.error(f"Supabase error in create_patient: {e}")

    memory_store["patients"][patient_id] = {**db_payload, "id": patient_id, "uhid": patient_uhid}
    return jsonify({"status": "SUCCESS", "patient_id": patient_id, "uhid": patient_uhid}), 201

@app.route('/api/metrics', methods=['POST'])
def create_metrics():
    data = request.json or {}
    patient_id = data.get("patient_id")
    if not patient_id:
        return jsonify({"status": "ERROR", "message": "Patient ID is required."}), 400

    metrics_id = str(random.randint(10000000, 99999999))
    if supabase:
        try:
            res = supabase.table('patient_health_metrics').insert(data).execute()
            if res.data:
                metrics_id = res.data[0]['id']
        except Exception as e:
            logger.error(f"Supabase error in create_metrics: {e}")

    memory_store["metrics"][metrics_id] = {**data, "id": metrics_id}
    return jsonify({"status": "SUCCESS", "metrics_id": metrics_id}), 201

# --- ASSESSMENT SESSION INITIALIZATION ---
@app.route('/api/assessments/init', methods=['POST'])
def init_assessment():
    try:
        data = request.json or {}
        patient_id = data.get("patient_id")
        metrics_id = data.get("metrics_id")

        if not patient_id or not metrics_id:
            return jsonify({"status": "ERROR", "message": "Patient ID and Metrics ID are required."}), 400

        assessment_id = str(random.randint(10000000, 99999999))
        payload = {
            "patient_id": patient_id,
            "metrics_id": metrics_id,
            "full_chat_transcript": [],
            "is_complete": False
        }

        if supabase:
            try:
                res = supabase.table('assessments').insert(payload).execute()
                if res.data:
                    assessment_id = res.data[0]['id']
            except Exception as e:
                logger.error(f"Supabase error in init_assessment: {e}")

        # Initialize structured clinical state
        init_state = ClinicalState()
        memory_store["clinical_states"][assessment_id] = init_state
        memory_store["assessments"][assessment_id] = {
            "id": assessment_id,
            "patient_id": patient_id,
            "metrics_id": metrics_id,
            "full_chat_transcript": [],
            "is_complete": False,
            "patients": memory_store["patients"].get(patient_id, {}),
            "patient_health_metrics": memory_store["metrics"].get(metrics_id, {})
        }

        return jsonify({"status": "SUCCESS", "assessment_id": assessment_id}), 201

    except Exception as e:
        logger.error(f"Error in init_assessment: {e}")
        return jsonify({"status": "ERROR", "message": "Failed to initialize cardiac assessment."}), 500

# --- ASSESSMENT RETRIEVAL ---
@app.route('/api/assessments/<assessment_id>', methods=['GET'])
def get_assessment(assessment_id):
    try:
        assessment = None
        if supabase:
            try:
                res = supabase.table('assessments') \
                    .select('*, patients(*), patient_health_metrics(*)') \
                    .eq('id', assessment_id).execute()
                if res.data:
                    assessment = res.data[0]
            except Exception as db_err:
                logger.warning(f"Supabase get_assessment failed: {db_err}")

        if not assessment and assessment_id in memory_store["assessments"]:
            assessment = memory_store["assessments"][assessment_id]

        if not assessment:
            return jsonify({"status": "ERROR", "message": "Assessment not found."}), 404

        # Include structured report if stored
        if assessment_id in memory_store["reports"]:
            assessment["report_data"] = memory_store["reports"][assessment_id]

        return jsonify({"status": "SUCCESS", "assessment": assessment}), 200
    except Exception as e:
        logger.error(f"Error in get_assessment: {e}")
        return jsonify({"status": "ERROR", "message": str(e)}), 500

# --- CLINICAL CONSULTATION CHAT ENGINE ---
@app.route('/api/assessments/chat', methods=['POST'])
def chat_engine():
    try:
        body = request.json or {}
        assessment_id = body.get('assessment_id')
        user_message = body.get('user_message', '').strip()

        if not assessment_id or not user_message:
            return jsonify({"status": "ERROR", "message": "Assessment ID and message are required."}), 400

        # Retrieve assessment and linked records
        assessment = None
        if supabase:
            try:
                res = supabase.table('assessments') \
                    .select('*, patients(*), patient_health_metrics(*)') \
                    .eq('id', assessment_id).execute()
                if res.data:
                    assessment = res.data[0]
            except Exception as e:
                logger.warning(f"Supabase fetch in chat_engine failed: {e}")

        if not assessment and assessment_id in memory_store["assessments"]:
            assessment = memory_store["assessments"][assessment_id]

        if not assessment:
            return jsonify({"status": "ERROR", "message": "Assessment record could not be found."}), 404

        transcript = assessment.get('full_chat_transcript') or []
        patient_info = assessment.get('patients') or {}
        metrics_info = assessment.get('patient_health_metrics') or {}

        # Retrieve or initialize ClinicalState
        current_state = memory_store["clinical_states"].get(assessment_id) or ClinicalState()

        # 1. Update structured clinical facts from user message
        updated_state = clinical_engine.extract_clinical_facts(user_message, current_state)
        updated_state.question_count += 1

        # 2. Run Deterministic Safety Engine immediately
        safety_eval = safety_engine.evaluate(updated_state.model_dump(), baseline_metrics=metrics_info)

        # 3. Check for Emergency Interrupt
        if safety_eval.is_emergency:
            logger.info(f"[SAFETY ENGINE] Emergency interrupt triggered for assessment {assessment_id}")
            report = clinical_engine.generate_clinical_synthesis(
                state=updated_state,
                patient_info=patient_info,
                metrics=metrics_info,
                safety=safety_eval
            )
            report_dict = report.model_dump()
            memory_store["reports"][assessment_id] = report_dict
            memory_store["clinical_states"][assessment_id] = updated_state

            emergency_message = (
                f"Thank you. Based on the symptoms you reported — particularly {safety_eval.reason.lower()} — "
                f"this pattern can occur with serious cardiac conditions. I am immediately preparing your clinical "
                f"decision-support summary so you can seek emergency medical evaluation without delay."
            )

            new_transcript = list(transcript)
            new_transcript.append({"role": "user", "content": user_message})
            new_transcript.append({"role": "assistant", "content": emergency_message})

            db_update = {
                "full_chat_transcript": new_transcript,
                "is_complete": True,
                "triage_category_level": safety_eval.triage_category,
                "calculated_risk_score_100": int(report.clinical_completeness_pct),
                "confidence_percentage": report.clinical_completeness_pct,
                "primary_suspected_pattern": report.leading_concern.get("possible_condition"),
                "secondary_suspected_pattern": report.possible_conditions[1].condition if len(report.possible_conditions) > 1 else None,
                "critical_red_flags_identified": safety_eval.red_flags,
                "doctor_clinical_summary_text": report.doctor_clinical_summary_text,
                "triage_routing_recommendation": safety_eval.action_recommendation
            }

            if supabase:
                try:
                    supabase.table('assessments').update(db_update).eq('id', assessment_id).execute()
                except Exception as db_err:
                    logger.error(f"Supabase update failed on emergency interrupt: {db_err}")

            if assessment_id in memory_store["assessments"]:
                memory_store["assessments"][assessment_id].update(db_update)

            return jsonify({
                "status": "SUCCESS",
                "action": "GENERATE_REPORT",
                "message_to_patient": emergency_message,
                "ai_response": emergency_message,
                "is_report": True,
                "report_data": report_dict
            }), 200

        # 4. Check if interview is ready to complete
        # Must meet minimum 5 questions, or have high clinical completeness, or reached max questions
        completeness = scoring_service.calculate_completeness(updated_state.model_dump())
        has_min_questions = updated_state.question_count >= clinical_engine.MINIMUM_QUESTIONS
        is_max_reached = updated_state.question_count >= clinical_engine.MAXIMUM_QUESTIONS
        has_high_completeness = completeness.completeness_percentage >= 80.0

        if (has_min_questions and has_high_completeness) or is_max_reached:
            report = clinical_engine.generate_clinical_synthesis(
                state=updated_state,
                patient_info=patient_info,
                metrics=metrics_info,
                safety=safety_eval
            )
            report_dict = report.model_dump()
            memory_store["reports"][assessment_id] = report_dict
            memory_store["clinical_states"][assessment_id] = updated_state

            completion_message = (
                "Thank you for providing all of this detailed information. I have completed the preliminary "
                "cardiac assessment and compiled your clinical summary for review."
            )

            new_transcript = list(transcript)
            new_transcript.append({"role": "user", "content": user_message})
            new_transcript.append({"role": "assistant", "content": completion_message})

            db_update = {
                "full_chat_transcript": new_transcript,
                "is_complete": True,
                "triage_category_level": safety_eval.triage_category,
                "calculated_risk_score_100": int(report.clinical_completeness_pct),
                "confidence_percentage": report.clinical_completeness_pct,
                "primary_suspected_pattern": report.leading_concern.get("possible_condition"),
                "secondary_suspected_pattern": report.possible_conditions[1].condition if len(report.possible_conditions) > 1 else None,
                "critical_red_flags_identified": safety_eval.red_flags,
                "doctor_clinical_summary_text": report.doctor_clinical_summary_text,
                "triage_routing_recommendation": safety_eval.action_recommendation
            }

            if supabase:
                try:
                    supabase.table('assessments').update(db_update).eq('id', assessment_id).execute()
                except Exception as db_err:
                    logger.error(f"Supabase update failed on report completion: {db_err}")

            if assessment_id in memory_store["assessments"]:
                memory_store["assessments"][assessment_id].update(db_update)

            return jsonify({
                "status": "SUCCESS",
                "action": "GENERATE_REPORT",
                "message_to_patient": completion_message,
                "ai_response": completion_message,
                "is_report": True,
                "report_data": report_dict
            }), 200

        # 5. Adaptive Follow-Up Question Selection (Semantic Duplicate Prevention)
        next_q_info = clinical_engine.select_next_question(updated_state)
        if not next_q_info:
            # All core questions resolved; conclude interview
            report = clinical_engine.generate_clinical_synthesis(
                state=updated_state,
                patient_info=patient_info,
                metrics=metrics_info,
                safety=safety_eval
            )
            report_dict = report.model_dump()
            memory_store["reports"][assessment_id] = report_dict
            memory_store["clinical_states"][assessment_id] = updated_state

            completion_message = "Thank you. I have enough clinical information to prepare your assessment summary."
            new_transcript = list(transcript)
            new_transcript.append({"role": "user", "content": user_message})
            new_transcript.append({"role": "assistant", "content": completion_message})

            return jsonify({
                "status": "SUCCESS",
                "action": "GENERATE_REPORT",
                "message_to_patient": completion_message,
                "ai_response": completion_message,
                "is_report": True,
                "report_data": report_dict
            }), 200

        next_q_key, next_q_prompt = next_q_info
        updated_state.asked_question_keys.append(next_q_key)
        memory_store["clinical_states"][assessment_id] = updated_state

        # Use NVIDIA reasoning model for an empathetic, natural transition
        empathetic_question = next_q_prompt
        if nvidia_service.is_configured:
            try:
                system_instruction = (
                    "You are Dr. Cardia, a compassionate, calm, and professional cardiac clinical triage specialist. "
                    "Acknowledge the patient's statement briefly with empathy, then ask this exact clinical question: "
                    f"\"{next_q_prompt}\". Do not ask multiple concepts. Do not use technical jargon or claim a diagnosis."
                )
                ai_reply = nvidia_service.chat_completion(
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.2,
                    max_tokens=200
                )
                if ai_reply and len(ai_reply.strip()) > 10:
                    empathetic_question = ai_reply.strip()
            except Exception as e:
                logger.warning(f"Dr. Cardia LLM transition fallback used: {e}")

        new_transcript = list(transcript)
        new_transcript.append({"role": "user", "content": user_message})
        new_transcript.append({"role": "assistant", "content": empathetic_question})

        if supabase:
            try:
                supabase.table('assessments').update({
                    "full_chat_transcript": new_transcript
                }).eq('id', assessment_id).execute()
            except Exception as e:
                logger.warning(f"Supabase transcript update failed: {e}")

        if assessment_id in memory_store["assessments"]:
            memory_store["assessments"][assessment_id]["full_chat_transcript"] = new_transcript

        return jsonify({
            "status": "SUCCESS",
            "action": "ASK_QUESTION",
            "message_to_patient": empathetic_question,
            "ai_response": empathetic_question,
            "is_report": False
        }), 200

    except Exception as e:
        logger.critical(f"Server Exception in chat_engine: {e}", exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "Dr. Cardia is temporarily unavailable. Please try again."
        }), 503

@app.route('/api/assessments/<assessment_id>/pdf', methods=['GET'])
def get_assessment_pdf(assessment_id):
    try:
        assessment = None
        patient = {}
        metrics = {}
        report_data = {}

        if supabase:
            try:
                res = supabase.table('assessments').select('*, patients(*), patient_health_metrics(*)').eq('id', assessment_id).execute()
                if res.data and len(res.data) > 0:
                    rec = res.data[0]
                    patient = rec.get('patients') or {}
                    metrics = rec.get('patient_health_metrics') or {}
                    report_data = rec.get('report_data') or rec
                    assessment = rec
            except Exception as e:
                logger.warning(f"Supabase PDF lookup failed: {e}")

        if not assessment and assessment_id in memory_store["assessments"]:
            assessment = memory_store["assessments"][assessment_id]
            pat_id = assessment.get("patient_id")
            met_id = assessment.get("metrics_id")
            patient = memory_store["patients"].get(pat_id, {})
            metrics = memory_store["metrics"].get(met_id, {})
            report_data = assessment.get("report_data") or assessment

        if not assessment:
            return jsonify({"status": "ERROR", "message": "Assessment record not found."}), 404

        pdf_bytes = pdf_service.generate_assessment_pdf(
            patient=patient,
            metrics=metrics,
            report_data=report_data,
            assessment_id=assessment_id
        )

        uhid = patient.get('uhid', 'Report')
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"CardiacCare_{uhid}_{assessment_id[:8]}.pdf"
        )
    except Exception as e:
        logger.error(f"PDF generation endpoint error: {e}", exc_info=True)
        return jsonify({"status": "ERROR", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Cardiac Care Master Clinical Engine running on port {port}")
    app.run(port=port, debug=True)