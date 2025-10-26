"""Test JWT token verification."""
import os
from dotenv import load_dotenv
from jose import jwt

# Load .env file
load_dotenv()

# Get secret from environment
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-me")

print(f"\nSecret key from .env: {SECRET_KEY}")

# Test token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3MWM0MDNhYS03YTQ2LTQ4YjItOGFlOC1jZGI4MjA4MDNhOTAiLCJleHAiOjE3NjE1Njk1ODksInR5cGUiOiJhY2Nlc3MifQ.CQ7jAec3BW6WUI5Lphg4satyNyd9tbcQAIMRm0PV6VQ"

try:
    decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    print("\n✅ Token is valid!")
    print(f"User ID: {decoded['sub']}")
    print(f"Expires: {decoded['exp']}")
except Exception as e:
    print(f"\n❌ Token validation failed: {e}")
