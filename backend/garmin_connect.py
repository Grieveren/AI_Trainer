"""Initiate Garmin OAuth flow."""
import sys
import requests

# Use the test user token
if len(sys.argv) > 1:
    token = sys.argv[1]
else:
    print("Usage: python3 garmin_connect.py <auth_token>")
    print("\nUse the token from generate_token.py")
    sys.exit(1)

# API endpoint
API_URL = "http://localhost:8000/api/v1/garmin"

# Headers with auth token
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

print("\n" + "=" * 60)
print("🔗 GARMIN OAUTH CONNECTION")
print("=" * 60)
print("\nInitiating Garmin authorization...")

try:
    # Call authorize endpoint
    response = requests.post(f"{API_URL}/authorize", headers=headers)

    if response.status_code == 200:
        data = response.json()
        auth_url = data["authorization_url"]

        print("\n✅ Authorization URL generated successfully!")
        print("\n" + "=" * 60)
        print("📋 NEXT STEPS:")
        print("=" * 60)
        print("\n1. Open this URL in your browser (it's been copied for you):\n")
        print(f"   {auth_url}\n")
        print("2. Log in to Garmin with your credentials:")
        print(f"   Email: {data.get('client_id', 'From .env')}")
        print("   Password: (your Garmin password)")
        print("\n3. Complete 2-factor authentication:")
        print("   - Check your email for the Garmin verification code")
        print("   - Enter the code on Garmin's website")
        print("\n4. Authorize the application")
        print("\n5. You'll be redirected back to our app")
        print("\n" + "=" * 60)

    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.json())

except Exception as e:
    print(f"\n❌ Error connecting to API: {e}")
    print("\nMake sure the backend server is running on port 8000")
