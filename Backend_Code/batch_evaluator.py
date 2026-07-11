import requests
import time

BASE_URL = "http://localhost:5000/api"

# --- THE COMPLETE 30-PERSONA CLINICAL DATASET ---
PERSONAS = [
    {
        "id": "Persona 1 (STEMI)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test STEMI", "age": 58, "gender": "Male"},
        "opening": "Oh God, my chest is killing me – it feels like an elephant is standing on it and I can't breathe right!",
        "quality_severity": "It's this heavy crushing pressure, like a tight band squeezing the middle of my chest. It's a 10 out of 10, I feel like I'm going to pass out.",
        "radiation": "It shoots down my left arm all the way to my fingers and up into my jaw.",
        "provocation": "It hit me suddenly while I was walking to the car; nothing makes it better, even when I sit down.",
        "sample": "Hypertension and type 2 diabetes for 15 years; takes lisinopril and metformin daily; father died of heart attack at age 62; smokes ½ pack per day; no allergies."
    },
    {
        "id": "Persona 2 (Unstable Angina)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test UA", "age": 72, "gender": "Male"},
        "opening": "The pain in my chest keeps coming back even when I'm just sitting watching TV – this has never happened before.",
        "quality_severity": "Feels like a heavy weight pressing right in the center. 8 out of 10, bad enough that I'm sweating.",
        "radiation": "Goes into both shoulders and my neck.",
        "provocation": "Started at rest today and gets worse with any little movement.",
        "sample": "Known coronary artery disease with two stents 3 years ago; takes aspirin, atorvastatin, metoprolol; mother had bypass at 68; former smoker, quit 10 years ago."
    },
    {
        "id": "Persona 3 (Massive PE)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test Massive PE", "age": 48, "gender": "Female"},
        "opening": "I can't catch my breath and my chest feels like it's being stabbed every time I breathe in!",
        "quality_severity": "Sharp, stabbing pain that catches when I inhale. 9 out of 10, I'm really scared.",
        "radiation": "Mostly in the right side of my chest.",
        "provocation": "Started suddenly after I got off a long flight yesterday; breathing makes it worse.",
        "sample": "Recent knee surgery 2 weeks ago, still on bed rest part-time; takes oral contraceptive; no prior heart issues; family history of blood clots in sister; no allergies."
    },
    {
        "id": "Persona 4 (Aortic Dissection Type A)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test Aortic Dissection", "age": 70, "gender": "Male"},
        "opening": "This is the worst pain I've ever had – like someone tore something inside my chest and it's going straight through to my back!",
        "quality_severity": "Tearing, ripping sensation. 10 out of 10, came on like a thunderbolt.",
        "radiation": "Straight through to the middle of my upper back.",
        "provocation": "Started while I was arguing on the phone; nothing relieves it.",
        "sample": "Long-standing uncontrolled hypertension; takes amlodipine irregularly; father had similar sudden death at 68; smokes occasionally."
    },
    {
        "id": "Persona 5 (NSTEMI)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test NSTEMI", "age": 55, "gender": "Female"},
        "opening": "My chest feels so heavy and I'm nauseous – I thought it was just indigestion but it's not going away.",
        "quality_severity": "Dull, heavy ache. 7–8 out of 10.",
        "radiation": "Into my left shoulder blade.",
        "provocation": "Worse when I walk around the house; started after breakfast.",
        "sample": "High cholesterol, previous small heart attack 4 years ago; on atorvastatin and clopidogrel; mother had heart disease at 60."
    },
    {
        "id": "Persona 6 (STEMI)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test STEMI 2", "age": 62, "gender": "Male"},
        "opening": "I'm sweating buckets and my chest is exploding with pain – please tell me what to do!",
        "quality_severity": "Crushing, vise-like pressure. 10 out of 10.",
        "radiation": "Down left arm and into jaw.",
        "provocation": "Hit while shoveling snow, no relief at rest.",
        "sample": "Smoker 40 years, hypertension, diabetes; on metformin and lisinopril; brother had bypass at 55."
    },
    {
        "id": "Persona 7 (Submassive PE)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test Sub PE", "age": 45, "gender": "Female"},
        "opening": "My chest hurts so bad on the right side and I feel like I might faint any second.",
        "quality_severity": "Sharp and worse with every breath. 8 out of 10.",
        "radiation": "Right chest only.",
        "provocation": "Sudden after a long car trip; deep breath makes it unbearable.",
        "sample": "Recent long-haul flight, oral contraceptive use; family history of DVT in aunt."
    },
    {
        "id": "Persona 8 (Unstable Angina 2)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test UA 2", "age": 68, "gender": "Male"},
        "opening": "The tightness in my chest is back again and it's scaring me – this time it's at rest.",
        "quality_severity": "Tight, squeezing. 8 out of 10.",
        "radiation": "To both arms.",
        "provocation": "Happens even when lying down now.",
        "sample": "Triple vessel disease, two prior stents; on multiple cardiac meds including beta-blocker; father died suddenly at 70."
    },
    {
        "id": "Persona 9 (Aortic Dissection)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test AD 2", "age": 59, "gender": "Female"},
        "opening": "A sudden ripping pain just shot through my chest and back – I’ve never felt anything like this!",
        "quality_severity": "Ripping and tearing. 10 out of 10 instantly.",
        "radiation": "Between shoulder blades.",
        "provocation": "While reaching up to get something from a shelf.",
        "sample": "Severe hypertension for 20+ years, often forgets medication."
    },
    {
        "id": "Persona 10 (STEMI 3)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test STEMI 3", "age": 52, "gender": "Male"},
        "opening": "Help, my chest is on fire and my arm is going numb!",
        "quality_severity": "Burning heavy pressure. 9 out of 10.",
        "radiation": "Left arm and jaw.",
        "provocation": "During morning walk, no better since.",
        "sample": "Smoker, high cholesterol; takes statin irregularly; family history of early heart attacks."
    },
    {
        "id": "Persona 11 (NSTEMI - Female Atypical)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test NSTEMI Atypical", "age": 52, "gender": "Female"},
        "opening": "I’ve had this weird jaw pain and nausea for hours and now my back hurts – is this normal?",
        "quality_severity": "Dull ache and burning. 6–7 out of 10.",
        "radiation": "Jaw and upper back.",
        "provocation": "Started after light housework, doesn’t ease with rest.",
        "sample": "Post-menopausal, hypertension, on HRT; mother had “silent” heart attack."
    },
    {
        "id": "Persona 12 (HCM Genetic)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test HCM", "age": 29, "gender": "Male"},
        "opening": "I’m only 29 but my chest hurts badly when I run and my dad died young from heart stuff – I’m freaking out.",
        "quality_severity": "Heavy tightness. 8 out of 10 during activity.",
        "radiation": "Center of chest only.",
        "provocation": "Only when exercising hard; eases with rest but scared now.",
        "sample": "Father sudden cardiac death age 38; known family HCM; no meds yet."
    },
    {
        "id": "Persona 13 (Silent Ischemia to UA)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test Silent Ischemia", "age": 64, "gender": "Male"},
        "opening": "My stomach feels like bad indigestion but I’m also sweating a lot and feel weak.",
        "quality_severity": "Burning pressure in upper belly. 6 out of 10 but constant.",
        "radiation": "None really.",
        "provocation": "Started at rest after dinner, not better with antacids.",
        "sample": "Long-standing diabetes on insulin; neuropathy; previous “silent” events; family CAD."
    },
    {
        "id": "Persona 14 (NSTEMI Elderly)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test Elderly NSTEMI", "age": 78, "gender": "Female"},
        "opening": "I feel so weak and my chest is just uncomfortable – I’m usually fine but today I’m confused.",
        "quality_severity": "Mild pressure, more like fatigue. 5 out of 10.",
        "radiation": "Mild to left shoulder.",
        "provocation": "Gradual over morning, no clear trigger.",
        "sample": "Hypertension, mild dementia; on multiple BP meds; daughter had early heart disease."
    },
    {
        "id": "Persona 15 (Premature CAD)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test Premature CAD", "age": 35, "gender": "Male"},
        "opening": "My cholesterol has been crazy high since I was a kid and now my chest is tight – this can’t be happening at my age.",
        "quality_severity": "Squeezing heaviness. 7 out of 10.",
        "radiation": "Left arm.",
        "provocation": "During brisk walk, first time at rest too.",
        "sample": "Familial hypercholesterolemia diagnosed young; on high-dose statin; father CABG at 42."
    },
    {
        "id": "Persona 16 (Diabetic NSTEMI)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test Diabetic NSTEMI", "age": 55, "gender": "Female"},
        "opening": "Just a little chest flutter and nausea – I thought it was my sugar but it’s not getting better.",
        "quality_severity": "Mild burning tightness. 5–6 out of 10.",
        "radiation": "None obvious.",
        "provocation": "After eating, persists.",
        "sample": "Type 2 diabetes 20 years, neuropathy; on metformin and insulin."
    },
    {
        "id": "Persona 17 (Takotsubo)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test Takotsubo", "age": 41, "gender": "Female"},
        "opening": "After a huge argument my chest suddenly felt crushed – I’m still shaking.",
        "quality_severity": "Crushing pressure. 8 out of 10.",
        "radiation": "To back.",
        "provocation": "Sudden after extreme emotional stress.",
        "sample": "No prior heart disease; recent major life stressor; on anxiety medication occasionally."
    },
    {
        "id": "Persona 18 (SCAD)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test SCAD", "age": 27, "gender": "Female"},
        "opening": "I’m young and healthy but my chest just started hurting terribly after yoga.",
        "quality_severity": "Sharp then heavy. 9 out of 10.",
        "radiation": "Left arm.",
        "provocation": "During physical activity.",
        "sample": "Post-partum 6 months ago; fibromuscular dysplasia in family."
    },
    {
        "id": "Persona 19 (Cocaine Ischemia)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test Cocaine Ischemia", "age": 48, "gender": "Male"},
        "opening": "I did a little coke last night and now my chest won’t stop hurting – I’m terrified.",
        "quality_severity": "Tight crushing. 8 out of 10.",
        "radiation": "Jaw.",
        "provocation": "After using stimulant.",
        "sample": "Occasional cocaine use; otherwise healthy; no family history."
    },
    {
        "id": "Persona 20 (NSTEMI Older Woman)",
        "expected_triage": "Category A (EMERGENCY)",
        "patient_data": {"full_name": "Test NSTEMI 62F", "age": 62, "gender": "Female"},
        "opening": "My upper back and arms feel heavy and I’m short of breath – not sure if it’s my heart.",
        "quality_severity": "Achy heaviness. 7 out of 10.",
        "radiation": "Both arms and back.",
        "provocation": "Gradual while resting.",
        "sample": "Diabetes and hypertension; on multiple meds."
    },
    {
        "id": "Persona 21 (GERD)",
        "expected_triage": "Category C - Routine",
        "patient_data": {"full_name": "Test GERD", "age": 42, "gender": "Male"},
        "opening": "I get this burning in my chest after eating spicy food – it’s been worse lately.",
        "quality_severity": "Burning, acidic feeling. 5 out of 10.",
        "radiation": "Up to my throat.",
        "provocation": "After meals or lying down; antacids help.",
        "sample": "Occasional heartburn for years; takes OTC omeprazole; no cardiac risk factors; family reflux."
    },
    {
        "id": "Persona 22 (Costochondritis)",
        "expected_triage": "Category C - Routine",
        "patient_data": {"full_name": "Test Costochondritis", "age": 33, "gender": "Female"},
        "opening": "My chest hurts right where my ribs meet the breastbone and it’s worse when I touch it.",
        "quality_severity": "Sharp and localized. 6 out of 10.",
        "radiation": "Stays in one spot on left chest wall.",
        "provocation": "Worse when I move or press; started after gym workout.",
        "sample": "Recent increase in push-ups at gym; no medical issues; no family heart disease."
    },
    {
        "id": "Persona 23 (Panic Attack)",
        "expected_triage": "Category C - Routine",
        "patient_data": {"full_name": "Test Panic", "age": 26, "gender": "Male"},
        "opening": "My chest feels tight and I can’t breathe – I think I’m having a panic attack but I’m scared it’s my heart!",
        "quality_severity": "Tight, like I can’t get air in. 8 out of 10 with tingling hands.",
        "radiation": "None.",
        "provocation": "Sudden after stressful work call; breathing exercises help a bit.",
        "sample": "History of anxiety disorder; on SSRI; family history of anxiety."
    },
    {
        "id": "Persona 24 (MSK Strain)",
        "expected_triage": "Category C - Routine",
        "patient_data": {"full_name": "Test MSK", "age": 50, "gender": "Male"},
        "opening": "I lifted something heavy yesterday and now the left side of my chest aches when I move.",
        "quality_severity": "Dull ache, sore. 4–5 out of 10.",
        "radiation": "Stays on left rib area.",
        "provocation": "Worse with twisting or lifting; better with rest and ibuprofen.",
        "sample": "No cardiac history; manual job; no family heart disease."
    },
    {
        "id": "Persona 25 (Viral Pleurisy)",
        "expected_triage": "Category C - Routine",
        "patient_data": {"full_name": "Test Pleurisy", "age": 37, "gender": "Female"},
        "opening": "I had a bad cold and now my chest hurts every time I cough or take a deep breath.",
        "quality_severity": "Sharp with breathing or coughing. 5 out of 10.",
        "radiation": "Both sides of chest.",
        "provocation": "Worse with cough; started after viral illness.",
        "sample": "Recent flu-like illness; no chronic conditions."
    },
    {
        "id": "Persona 26 (Esophageal Spasm)",
        "expected_triage": "Category C - Routine",
        "patient_data": {"full_name": "Test Esophageal", "age": 45, "gender": "Male"},
        "opening": "It feels like my chest is squeezing after I eat – almost like a cramp but not my heart I hope.",
        "quality_severity": "Cramping, squeezing. 6 out of 10.",
        "radiation": "Center chest.",
        "provocation": "After swallowing cold drinks or large meals; antacids sometimes help.",
        "sample": "Occasional similar episodes; history of reflux; no cardiac risks."
    },
    {
        "id": "Persona 27 (Panic with Hyperventilation)",
        "expected_triage": "Category C - Routine",
        "patient_data": {"full_name": "Test Panic 2", "age": 29, "gender": "Female"},
        "opening": "Everything went tight in my chest and my hands are tingling – I can’t stop feeling like I’m dying.",
        "quality_severity": "Tight and suffocating. 7–8 out of 10.",
        "radiation": "None.",
        "provocation": "Triggered by crowded place; calms with slow breathing.",
        "sample": "Diagnosed anxiety disorder; recent stress at work."
    },
    {
        "id": "Persona 28 (Biliary Colic)",
        "expected_triage": "Category C - Routine",
        "patient_data": {"full_name": "Test Gallbladder", "age": 55, "gender": "Female"},
        "opening": "After eating fatty food my upper chest and right side hurt so bad it radiates up.",
        "quality_severity": "Cramping, gnawing. 7 out of 10.",
        "radiation": "To right shoulder.",
        "provocation": "30 minutes after greasy meals; lasts 1–2 hours.",
        "sample": "Known gallstones on ultrasound; no heart history."
    },
    {
        "id": "Persona 29 (Hiatal Hernia)",
        "expected_triage": "Category C - Routine",
        "patient_data": {"full_name": "Test Hernia", "age": 38, "gender": "Male"},
        "opening": "Burning comes up my chest when I lie down after dinner – it’s been happening for months.",
        "quality_severity": "Burning rising up. 5 out of 10.",
        "radiation": "Throat.",
        "provocation": "Lying flat or bending over; better sitting up.",
        "sample": "Diagnosed hiatal hernia; uses antacids; overweight."
    },
    {
        "id": "Persona 30 (Post-viral Costo)",
        "expected_triage": "Category C - Routine",
        "patient_data": {"full_name": "Test Post-Viral Costo", "age": 47, "gender": "Female"},
        "opening": "My ribs are so sore on the left side after that chest cold I had – touching it kills.",
        "quality_severity": "Sharp, tender to touch. 6 out of 10.",
        "radiation": "Local rib area.",
        "provocation": "Movement, coughing, pressing; started after coughing illness.",
        "sample": "Recent viral respiratory infection; no cardiac risk factors; healthy otherwise."
    }
]

def run_simulation():
    print("======================================================")
    print("🚀 INITIATING GACC-EWS AUTOMATED BATCH EVALUATION")
    print("======================================================\n")

    for idx, persona in enumerate(PERSONAS):
        print(f"======================================================")
        print(f"--- Testing {idx+1}/30: {persona['id']} ---")
        print(f"Expected Triage: {persona['expected_triage']}")
        print(f"======================================================")
        
        # 1. Init Patient & Metrics
        try:
            p_res = requests.post(f"{BASE_URL}/patients", json=persona["patient_data"]).json()
            patient_id = p_res["patient_id"]
            
            m_res = requests.post(f"{BASE_URL}/metrics", json={"patient_id": patient_id, "blood_pressure_status": "Unknown", "resting_heart_rate_status": "Unknown"}).json()
            metrics_id = m_res["metrics_id"]
            
            a_res = requests.post(f"{BASE_URL}/assessments/init", json={"patient_id": patient_id, "metrics_id": metrics_id}).json()
            assessment_id = a_res["assessment_id"]
        except Exception as e:
            print(f"⚠️ Failed to initialize patient {persona['id']} in Supabase: {e}")
            continue

        # 2. Sequential Chat Simulation
        chat_sequence = [
            persona["opening"],
            persona["quality_severity"],
            persona["radiation"],
            persona["provocation"],
            persona["sample"]
        ]
        
        for turn, user_msg in enumerate(chat_sequence):
            print(f"\n🧑 Patient: {user_msg}")
            
            try:
                response = requests.post(f"{BASE_URL}/assessments/chat", json={
                    "assessment_id": assessment_id,
                    "user_message": user_msg
                }).json()
                
                print(f"🤖 Engine: {response.get('ai_response')}")
                
                # Check if the AI aborted early or finished normally
                if response.get("is_report"):
                    print(f"\n🚨 [REPORT GENERATED SUCCESSFULLY in Supabase for {persona['id']}]")
                    break
                    
            except Exception as e:
                print(f"\n⚠️ NETWORK ERROR: {e}")
                break
                
            # Prevent rate-limiting the NVIDIA API
            time.sleep(2) 

        print("\n\n")

if __name__ == "__main__":
    run_simulation()