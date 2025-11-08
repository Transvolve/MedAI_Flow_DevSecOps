import time
import pytest
from backend.app.security.jwt_manager import jwt_manager

def test_token_revocation_cycle(monkeypatch):
    # mock small expiry
    token_data = {"sub": "test_user", "jti": "abc123", "role": "admin"}
    token = jwt_manager.create_token(token_data)
    # simulate revocation
    jwt_manager.revoke_token("abc123", 5)
    assert jwt_manager.is_revoked("abc123") is True
    # allow Redis TTL to expire (simulate)
    time.sleep(5)
    # after expiry token should be gone
    assert not jwt_manager.is_revoked("abc123")
