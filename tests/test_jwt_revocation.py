# tests/test_jwt_revocation.py
from backend.app.security.jwt_manager import jwt_manager


def test_revocation_ttl():
    token_data = {"sub": "test_user", "jti": "abc123", "role": "admin"}
    _token = jwt_manager.create_token(token_data)  # keep if your manager returns str
    jwt_manager.revoke_token("abc123", 5)
    assert jwt_manager.is_revoked("abc123")
