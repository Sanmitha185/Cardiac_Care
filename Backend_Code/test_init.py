import requests

BASE_URL = "http://localhost:5000/api"

print("--- 🩺 INITIALIZING NEW PATIENT SESSION ---")

# 1. Create Patient
patient_data = {
    "uhid": "PT-99812",
    "full_name": "Omkar Admin Test",
    "age": 25,
    "gender": "Male",
    "blood_group": "O+",
    "contact_number": "555-0199",
    "emergency_contact_name": "Primary Contact",
    "emergency_contact_number": "555-0200"
}
print("\n1. Registering Patient...")
patient_res = requests.post(f"{BASE_URL}/patients", json=patient_data).json()

if patient_res.get("status") == "SUCCESS":
    patient_id = patient_res["patient_id"]
    print(f"✅ Patient Created! ID: {patient_id}")
else:
    print(f"❌ Failed: {patient_res}")
    exit()

# 2. Create Metrics
metrics_data = {
    "patient_id": patient_id,
    "weight_kg": 75.5,
    "height_cm": 180,
    "blood_pressure_status": "140/90",
    "resting_heart_rate_status": "88 bpm",
    "blood_glucose_status": "Normal",
    "past_ecg_history": "None"
}
print("\n2. Logging Vitals...")
metrics_res = requests.post(f"{BASE_URL}/metrics", json=metrics_data).json()

if metrics_res.get("status") == "SUCCESS":
    metrics_id = metrics_res["metrics_id"]
    print(f"✅ Vitals Logged! ID: {metrics_id}")
else:
    print(f"❌ Failed: {metrics_res}")
    exit()

# 3. Initialize Assessment
assessment_data = {
    "patient_id": patient_id,
    "metrics_id": metrics_id
}
print("\n3. Starting Assessment...")
assessment_res = requests.post(f"{BASE_URL}/assessments/init", json=assessment_data).json()

if assessment_res.get("status") == "SUCCESS":
    assessment_id = assessment_res["assessment_id"]
    print(f"✅ Assessment Started!")
    print("\n=======================================================")
    print(f"🔥 YOUR NEW ASSESSMENT ID: {assessment_id}")
    print("=======================================================\n")
    print("Copy the ID above and replace it in live_chat.py if you want a fresh session!")
else:
    print(f"❌ Failed: {assessment_res}")