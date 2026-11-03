import os

os.environ["DEMO_MODE"] = "true"
from fastapi.testclient import TestClient
from app.main import app
from app.safety import redact_secrets

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["mode"] == "demo"


def test_port_conflict():
    r = client.post("/api/analyze", json={"logs": "Error: listen EADDRINUSE: address already in use :::4000"})
    assert r.status_code == 200
    assert r.json()["diagnosis"]["failure_type"] == "Port conflict"
    assert r.json()["mode"] == "demo"


def test_connection_refused():
    r = client.post("/api/analyze", json={"logs": "Error: connect ECONNREFUSED 127.0.0.1:3306"})
    assert r.json()["diagnosis"]["failure_type"] == "Connection refused"


def test_unknown_does_not_fabricate():
    r = client.post("/api/analyze", json={"logs": "This is an unfamiliar application crash"})
    assert r.json()["diagnosis"]["confidence"] == "low"


def test_reject_short_or_oversized():
    assert client.post("/api/analyze", json={"logs": "bad"}).status_code == 422
    assert client.post("/api/analyze", json={"logs": "a" * 12001}).status_code == 422


def test_redaction():
    x = redact_secrets("password=hunter2 token=xyz Authorization: Bearer 123abc")
    assert "hunter2" not in x
    assert "token=xyz" not in x
    assert "Bearer 123abc" not in x
