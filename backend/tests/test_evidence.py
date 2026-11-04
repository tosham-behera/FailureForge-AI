import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.evidence import prepare_evidence
from app.schemas import AnalyzeRequest
from test_meta_model import provider, completion, DIAGNOSIS

client = TestClient(app)
SOURCES = [
    {'name': 'application.log', 'content': '10:01:05 ERROR connection failed\n10:01:06 ERROR connection failed'},
    {'name': 'database.txt', 'content': '10:01:02 Database stopped unexpectedly\nMissing timestamp event'},
]


def test_multiple_files_timeline_and_repeat_counts():
    response = client.post('/api/analyze', json={'sources': SOURCES})
    assert response.status_code == 200
    result = response.json()
    timed = [e for e in result['timeline'] if e['timestamp']]
    assert [e['timestamp'] for e in timed] == ['10:01:02', '10:01:05', '10:01:06']
    assert timed[0]['source'] == 'database.txt'
    assert timed[1]['repetitions'] == 2
    assert any(e['group'] == 'undated' for e in result['timeline'])
    assert '[S2:L1 database.txt]' in result['input_evidence']


def test_mixed_clocks_never_combined():
    req = AnalyzeRequest(logs='2026-11-03T10:00:00Z ERROR one\n2026-11-03 10:00:01 ERROR two\n10:00:02 ERROR three\nno timestamp\n2026-99-99 10:01:01 invalid date')
    _, events = prepare_evidence(req)
    assert len({e['group'] for e in events}) == 4
    assert events[-1]['sort'] is None


@pytest.mark.parametrize('source', [
    {'name': '../private.log', 'content': 'error text'},
    {'name': 'C:\\private.log', 'content': 'error text'},
    {'name': 'script.py', 'content': 'error text'},
    {'name': 'binary.log', 'content': 'error\x00text'},
    {'name': 'large.log', 'content': 'é' * 9000},
])
def test_reject_unsafe_files(source):
    assert client.post('/api/analyze', json={'sources': [source]}).status_code == 422


def test_count_combined_size_and_lines():
    for sources in [SOURCES * 3, [{'name': f'{i}.log', 'content': 'a' * 11000} for i in range(2)], [{'name':'many.log', 'content':'x\n' * 601}]]:
        assert client.post('/api/analyze', json={'sources': sources}).status_code == 422


def test_transport_limit_and_validation_never_echo_secrets(monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY', 'private-test-key')
    response = client.post('/api/analyze', json={'app_name':'private-test-key' * 10, 'logs':'error text'})
    assert response.status_code == 422
    assert 'private-test-key' not in response.text
    assert client.post('/api/analyze', content=b'x' * 524289, headers={'Content-Type':'application/json'}).status_code == 413


def test_source_references_and_redaction_reach_meta(provider):
    quote = 'Database stopped unexpectedly'
    diagnosis = {**DIAGNOSIS, 'evidence': [quote], 'hypothesis_support': [{'hypothesis': DIAGNOSIS['probable_root_cause'], 'evidence': [quote]}]}
    provider['body'] = completion(json.dumps(diagnosis))
    response = client.post('/api/analyze', json={'logs': 'token=private123', 'sources': SOURCES})
    assert response.status_code == 200
    data = response.json()
    assert data['evidence_locations'][0]['locations'][0] == {'ref':'S2:L1', 'source':'database.txt', 'line':1}
    assert 'private123' not in json.dumps(provider['calls']) + response.text
    assert 'S1:L1' in provider['calls'][0]['messages'][1]['content']
