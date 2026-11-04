from fastapi.testclient import TestClient
from app.main import app
from test_database_verification import BEFORE, AFTER

client = TestClient(app)


def payload():
    first = client.post('/api/analyze', json={'logs':'Error ECONNREFUSED token=private123'}).json()
    history = [{'evidence':first['input_evidence'], 'result':first}]
    second = client.post('/api/investigate', json={'history':history, 'evidence':'Node and database run in separate Docker containers.'}).json()
    history.append({'evidence':second['input_evidence'], 'result':second})
    return {'app_name':'Example app password=private123', 'history':history}


def test_export_chronology_limitations_redaction_and_no_meta(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Report must not call Meta or Docker')
    monkeypatch.setattr('app.main.diagnose_with_meta', forbidden)
    monkeypatch.setattr('app.main.verify_scenario', forbidden)
    response = client.post('/api/report', json=payload())
    assert response.status_code == 200
    data = response.json()
    assert data['filename'].endswith('.md')
    text = data['markdown']
    assert 'private123' not in text
    assert text.index('Investigation round 1') < text.index('Investigation round 2')
    for expected in ['offline-rules', 'No Docker verification', 'not confirmed', 'Provided context', 'Recommended diagnostic checks', 'No fix has been experimentally verified']:
        assert expected in text


def test_report_includes_realistic_sample_evidence():
    body = payload()
    body['verifications'] = [{'round':2, 'result':{'scenario':'database-connectivity', 'status':'passed', 'docker_ran':True, 'cleanup_succeeded':True, 'before':BEFORE, 'after':AFTER}}]
    text = client.post('/api/report', json=body).json()['markdown']
    assert 'ECONNREFUSED' in text and 'start-sample-dependency' in text
    assert 'does not confirm the incident root cause' in text
    assert 'client-supplied' in text


def test_report_limits_and_escaped_context():
    body = payload()
    body['app_name'] = '<script>untrusted</script>'
    text = client.post('/api/report', json=body).json()['markdown']
    assert '    <script>untrusted</script>' in text
    body['history'] *= 3
    assert client.post('/api/report', json=body).status_code == 422
