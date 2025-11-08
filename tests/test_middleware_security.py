import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_security_headers_are_present():
    resp = client.get("/health")  # or any existing endpoint
    expected_headers = [
        "Strict-Transport-Security",
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Content-Security-Policy",
        "Permissions-Policy",
        "Referrer-Policy",
        "Cache-Control",
        "X-XSS-Protection",
        "Cross-Origin-Opener-Policy",
        "Cross-Origin-Embedder-Policy",
    ]
    for header in expected_headers:
        assert header in resp.headers, f"{header} missing"
        assert resp.headers[header] != "", f"{header} is empty"

def test_request_tracking_headers():
    resp = client.get("/health")
    assert "X-Request-ID" in resp.headers
    assert "X-Process-Time" in resp.headers
