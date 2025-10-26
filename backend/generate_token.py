"""Generate JWT token for test user."""
import sys
from datetime import datetime, timedelta
from jose import jwt

# JWT settings from .env
SECRET_KEY = "your-jwt-secret-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

# Test user ID (from create_test_data.py output)
if len(sys.argv) > 1:
    user_id = sys.argv[1]
else:
    print("Usage: python3 generate_token.py <user_id>")
    sys.exit(1)

# Create token
expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
to_encode = {"sub": user_id, "exp": expire, "type": "access"}

token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

print("\n" + "=" * 60)
print("🔑 JWT ACCESS TOKEN")
print("=" * 60)
print(f"\nUser ID: {user_id}")
print(f"Expires: {expire}")
print(f"\nToken:\n{token}")
print("\n" + "=" * 60)
print("\n📋 To use this token:")
print("1. Open your browser to http://localhost:5176/")
print("2. Open DevTools (F12)")
print("3. Go to Application > Local Storage > http://localhost:5176")
print("4. Add new key: 'auth_token' with value: " + token)
print("5. Refresh the page")
print("=" * 60 + "\n")
