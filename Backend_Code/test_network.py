import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Pull the exact URL from your .env file
supabase_url = os.environ.get("SUPABASE_URL", "").strip()

print(f"\n🔍 Attempting to ping: {supabase_url}")

if not supabase_url:
    print("❌ ERROR: Your .env file is not being read. SUPABASE_URL is empty.")
    exit()

try:
    # Try to ping the Supabase REST API directly
    response = requests.get(f"{supabase_url}/rest/v1/", timeout=5)
    print("✅ SUCCESS! Your computer can see Supabase. The network is clear.")
except Exception as e:
    print("\n❌ CRITICAL NETWORK FAILURE:")
    print(str(e))
    print("\n💡 DIAGNOSIS: Your code is fine. Your URL is either fake/typed incorrectly, or your current Wi-Fi/Antivirus is strictly blocking the connection to Supabase.")