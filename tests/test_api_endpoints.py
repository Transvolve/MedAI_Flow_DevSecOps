import os
import sys
from fastapi.testclient import TestClient


sys.path.append(os.path.abspath("backend"))
from app.main import app  # noqa: E402


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
    r = client.get("/infer")
    assert r.status_code in (401, 403)


def test_infer_with_token():
    headers = {"Authorization": "Bearer test-token"}
    r = client.get("/infer", headers=headers)
    assert r.status_code == 200
    body = r.json()
    # latency_timer wraps the result
    assert "latency_ms" in body
    assert "result" in body
    assert body["result"]["message"] == "Model inference endpoint ready."


