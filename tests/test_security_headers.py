import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_security_headers_present(client):
    response = client.get("/health")
    expected_headers = [
        "Strict-Transport-Security",
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Content-Security-Policy",
        "Permissions-Policy",
    ]
    for header in expected_headers:
        assert header in response.headers, f"{header} missing from response"

