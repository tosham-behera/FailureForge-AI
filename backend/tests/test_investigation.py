import json
from fastapi.testclient import TestClient
from app.main import app
from test_meta_model import provider, completion, DIAGNOSIS, LOGS

client = TestClient(app)


def initial():
    result = client.post('/api/analyze', json={'logs': 'Error ECONNREFUSED 127.0.0.1:3306'}).json()
    return {'evidence': result['input_evidence'], 'result': result}


def test_demo_continuation_preserves_original():
    first = initial()
    snapshot = json.dumps(first)
    response = client.post('/api/investigate', json={'history': [first], 'evidence': 'MySQL and Node run in separate Docker containers.'})
    assert response.status_code == 200
    data = response.json()
    assert data['mode'] == 'demo'
    assert 'network' in data['diagnosis']['probable_root_cause']
    assert len(data['diagnosis']['questions']) in (2, 3)
    assert json.dumps(first) == snapshot


def test_history_limits():
    first = initial()
    for history, evidence in [([], 'new logs here'), ([first] * 5, 'new logs here'), ([first], 'x' * 6001), ([first], '        ')]:
        assert client.post('/api/investigate', json={'history': history, 'evidence': evidence}).status_code == 422
    huge = {**first, 'evidence': 'a' * 24000}
    assert client.post('/api/investigate', json={'history': [huge] * 4, 'evidence': 'new logs here'}).status_code == 422


def test_meta_receives_history_and_new_evidence(provider):
    first_result = client.post('/api/analyze', json={'logs': LOGS}).json()
    first = {'evidence': LOGS, 'result': first_result}
    provider['body'] = completion(json.dumps({**DIAGNOSIS, 'what_changed': 'New evidence suggests inode exhaustion.'}))
    response = client.post('/api/investigate', json={'history': [first], 'evidence': 'Disk has 80% free space, but inode usage is 100%.'})
    assert response.status_code == 200
    assert 'inode' in response.json()['diagnosis']['what_changed']
    user = json.loads(provider['calls'][-1]['messages'][1]['content'])
    assert user['previous_investigation'][0]['evidence'] == LOGS
    assert 'inode usage' in user['logs']
    assert len(provider['calls']) == 2


def test_prior_hypothesis_is_not_observation(provider):
    first = {'evidence': LOGS, 'result': client.post('/api/analyze', json={'logs': LOGS}).json()}
    provider['body'] = completion(json.dumps({**DIAGNOSIS, 'evidence': [DIAGNOSIS['probable_root_cause']]}))
    assert client.post('/api/investigate', json={'history': [first], 'evidence': 'Additional logs pending.'}).status_code == 502


def test_continuation_rate_limit(provider):
    first = {'evidence': LOGS, 'result': client.post('/api/analyze', json={'logs': LOGS}).json()}
    provider.update(status=429, body={'error': {'message': 'limited'}})
    assert client.post('/api/investigate', json={'history': [first], 'evidence': 'Additional logs pending.'}).status_code == 429
