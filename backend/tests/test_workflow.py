import json
from fastapi.testclient import TestClient
from app.main import app
from test_meta_model import provider, completion, DIAGNOSIS, LOGS
from test_verification import fake_runner


def test_uploaded_evidence_meta_followup_docker_and_report(provider, monkeypatch):
    client = TestClient(app)
    first = client.post('/api/analyze', json={'app_name':'Worker', 'sources':[
        {'name':'worker.log','content':LOGS}, {'name':'system.txt','content':'2026-11-03T10:00:00Z ERROR write failed'}]}).json()
    assert first['mode'] == 'meta'
    assert first['evidence_locations'][0]['locations'][0]['source'] == 'worker.log'
    history = [{'evidence':first['input_evidence'], 'result':first}]
    provider['body'] = completion(json.dumps({**DIAGNOSIS, 'what_changed':'Free bytes remain; investigate inode limits.'}))
    response = client.post('/api/investigate', json={'app_name':'Worker','history':history,'evidence':'Free bytes remain, inode usage is 100%.'})
    assert response.status_code == 200
    second = response.json()
    assert second['evidence_locations'][0]['locations'][0]['source'] == 'worker.log'
    history.append({'evidence':second['input_evidence'],'result':second})
    fake_runner(monkeypatch)
    verification = client.post('/api/verify-fix', json={'scenario':'port-conflict'}).json()
    assert verification['status'] == 'passed'
    exported = client.post('/api/report', json={'app_name':'Worker','history':history,'verifications':[{'round':2,'result':verification}]}).json()['markdown']
    assert 'muse-spark-1.3' in exported
    assert 'Free bytes remain' in exported and 'EADDRINUSE' in exported
    assert 'not a signed audit record' in exported
    assert len(provider['calls']) == 2  # No model requests for verification/export.
