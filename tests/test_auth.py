# test_auth.py - CLI test for the auth layer.
#
# Tests:
#   1. Password hashing and verification
#   2. JWT token creation and decoding
#   3. Register endpoint
#   4. Login endpoint
#   5. Duplicate username rejection
#   6. Wrong password rejection
#   7. Cleanup
#
# ⚠  Requires the FastAPI server to be running for endpoint tests (steps 3-6)
#    Start with: uvicorn app.main:app --reload
#
# Run with:
#   python tests/test_auth.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from app.auth.password import hash_password, verify_password
from app.auth.auth_handler import create_token, decode_token
from app.db.database import get_client

API_BASE = "http://localhost:8000"
TEST_USERNAME = "test_auth_user_phase4"
TEST_PASSWORD = "SecurePass123!"


def divider(title: str = ""):
    print("\n" + "=" * 55)
    if title:
        print(f"  {title}")
        print("=" * 55)


def main():
    divider("AUTH LAYER TEST")

    # ── 1. Password hashing ───────────────────────────────────────────────────
    divider("1 — Password Hashing")
    try:
        hashed = hash_password(TEST_PASSWORD)
        assert hashed != TEST_PASSWORD, "Hash should not equal plain text"
        assert hashed.startswith("$2b$"), "Should be a bcrypt hash"
        print(f"  ✓ Password hashed correctly")
        print(f"    Hash prefix: {hashed[:20]}...")

        assert verify_password(TEST_PASSWORD, hashed) is True
        print(f"  ✓ Correct password verified")

        assert verify_password("wrongpassword", hashed) is False
        print(f"  ✓ Wrong password rejected")
    except Exception as e:
        print(f"  ✗ Password test failed: {e}")

    # ── 2. JWT tokens ─────────────────────────────────────────────────────────
    divider("2 — JWT Tokens")
    try:
        fake_user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_token(fake_user_id)
        assert isinstance(token, str) and len(token) > 20
        print(f"  ✓ Token created")
        print(f"    Token prefix: {token[:30]}...")

        decoded_id = decode_token(token)
        assert decoded_id == fake_user_id
        print(f"  ✓ Token decoded correctly — user_id matches")

        try:
            decode_token("invalid.token.string")
            print(f"  ✗ Should have raised ValueError for invalid token")
        except ValueError:
            print(f"  ✓ Invalid token rejected correctly")
    except Exception as e:
        print(f"  ✗ JWT test failed: {e}")

    # ── 3-6. API endpoint tests ───────────────────────────────────────────────
    divider("3 — Register (POST /auth/register)")
    try:
        # Clean up any leftover test user
        client = get_client()
        client.table("users").delete().eq("username", TEST_USERNAME).execute()

        response = requests.post(
            f"{API_BASE}/auth/register",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data
        token = data["access_token"]
        print(f"  ✓ Registered successfully, token received")
    except requests.exceptions.ConnectionError:
        print(f"  ✗ Cannot connect to API. Start the server first:")
        print(f"    uvicorn app.main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"  ✗ Register failed: {e}")
        token = None

    divider("4 — Login (POST /auth/login)")
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data
        print(f"  ✓ Login successful, token received")
    except Exception as e:
        print(f"  ✗ Login failed: {e}")

    divider("5 — Duplicate Username (POST /auth/register)")
    try:
        response = requests.post(
            f"{API_BASE}/auth/register",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        )
        assert response.status_code == 409, f"Expected 409, got {response.status_code}"
        print(f"  ✓ Duplicate username rejected with 409")
    except Exception as e:
        print(f"  ✗ Duplicate check failed: {e}")

    divider("6 — Wrong Password (POST /auth/login)")
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": TEST_USERNAME, "password": "wrongpassword"},
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"  ✓ Wrong password rejected with 401")
    except Exception as e:
        print(f"  ✗ Wrong password test failed: {e}")

    divider("7 — Cleanup")
    try:
        client = get_client()
        client.table("users").delete().eq("username", TEST_USERNAME).execute()
        print(f"  ✓ Test user deleted")
    except Exception as e:
        print(f"  ✗ Cleanup failed: {e}")

    divider("RESULT")
    print("  ✓ Auth layer test complete.")
   


if __name__ == "__main__":
    main()
