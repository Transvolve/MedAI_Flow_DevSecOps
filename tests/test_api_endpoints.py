import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from backend.app.main import app  # noqa: E402


client = TestClient(app)


def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "uptime" in body


def test_version_endpoint():
    r = client.get("/version")
    assert r.status_code == 200
    body = r.json()
    assert "version" in body


def test_infer_requires_auth():
    r = client.post("/infer", json={"data": [0.0, 1.0]})
    assert r.status_code in (401, 403)


def test_infer_with_token():
    # First get a valid token
    form_data = {"username": "user", "password": "user123"}
    r = client.post("/token", data=form_data)
    assert r.status_code == 200
    token = r.json()["access_token"]

    # Use the token for infer endpoint
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/infer", headers=headers, json={"data": [0.0, 1.0]})
    assert r.status_code == 200
    body = r.json()
    assert "latency_ms" in body
    assert "result" in body
    assert "outputs" in body["result"] or "message" in body["result"]


