import json
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import verification as v
from test_verification import completed

BEFORE = {'phase': 'before', 'port': 54321, 'error': 'ECONNREFUSED'}
AFTER = {'phase': 'after', 'port': 54321, 'connected': True,
         'recovery_action': 'start-sample-dependency', 'reply': 'FailureForge simulated database ready'}


@pytest.mark.parametrize('valid,cleanup,expected', [(True, True, 'passed'), (False, True, 'failed'), (True, False, 'error')])
def test_database_api_evidence_isolation_and_cleanup(monkeypatch, valid, cleanup, expected):
    calls = []
    def run(*args, **kwargs):
        calls.append(args)
        if args[0] == 'image':
            assert args[2] == v.DATABASE_IMAGE
            return completed('sha256:fixture')
        if args[0] == 'inspect':
            return completed(json.dumps({'Running': False, 'ExitCode': 0}))
        if args[0] == 'logs':
            return completed('\n'.join(map(json.dumps, [BEFORE, AFTER if valid else {'phase':'after'}])))
        if args[0] == 'rm':
            return completed(code=0 if cleanup else 1)
        return completed('id')
    monkeypatch.setattr(v, '_docker', run)
    response = TestClient(app).post('/api/verify-fix', json={'scenario':'database-connectivity'})
    assert response.status_code == 200
    result = response.json()
    assert result['scenario'] == 'database-connectivity'
    assert result['status'] == expected
    assert result['cleanup_succeeded'] == cleanup
    assert 'real MySQL' in result['note']
    command = next(c for c in calls if c[0] == 'run')
    for flag in ('--network=none', '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user=65534:65534', '--memory=64m', '--cpus=0.5', '--pids-limit=32', '--pull=never'):
        assert flag in command
    assert calls[-1][:2] == ('rm', '--force')


def test_database_disallows_commands():
    assert TestClient(app).post('/api/verify-fix', json={'scenario':'database-connectivity','command':'anything'}).status_code == 422
    with pytest.raises(ValueError):
        v.verify_scenario('user-defined-image')


@pytest.mark.skipif(os.getenv('RUN_DOCKER_TESTS') != '1', reason='Requires real Docker and built database fixture')
def test_real_database_fixture():
    result = v.verify_scenario('database-connectivity')
    assert result.status == 'passed', result.model_dump()
    assert result.docker_ran and result.cleanup_succeeded
    assert result.before == BEFORE and result.after == AFTER
