import pytest
from auth import get_password_hash, verify_password, create_access_token, decode_access_token
from main import app

def test_password_hashing_and_verification():
    raw_password = "SecurePassword123!"
    hashed = get_password_hash(raw_password)
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_generation_and_decoding():
    data = {"sub": "analyst@ffre.io", "role": "investigator"}
    token = create_access_token(data)
    assert token is not None
    payload = decode_access_token(token)
    assert payload.get("sub") == "analyst@ffre.io"
    assert payload.get("role") == "investigator"

def test_unauthenticated_login_invalid_password(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@ffre.io", "password": "wrongpassword"}
    )
    assert response.status_code == 401
