import requests

print("\n=========================================")
print("🩺 GACC-EWS Triage Engine Active")
print("⚠️ CRITICAL: Did you run test_init.py first to get a new ID?")
print("=========================================\n")

ASSESSMENT_ID = input("Paste your NEW Assessment ID here: ").strip()
URL = "http://localhost:5000/api/assessments/chat"

while True:
    user_message = input("\n🧑 You: ")
    if user_message.lower() == 'exit': 
        print("Ending session...")
        break
        
    try:
        response = requests.post(URL, json={"assessment_id": ASSESSMENT_ID, "user_message": user_message})
        data = response.json()
        
        if data.get("status") == "SUCCESS":
            print(f"\n🏥 Engine: {data.get('ai_response')}")
            
            if data.get("is_report"):
                print("\n✅ [REPORT GENERATED IN DATABASE. SESSION COMPLETE.]")
                break
        else:
            print(f"\n⚠️ SERVER ERROR: {data.get('error')}")
            
    except Exception as e:
        print(f"\n⚠️ NETWORK ERROR: {e}")