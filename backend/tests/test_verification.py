"""Unit tests mock Docker; only the opt-in integration test runs a real container."""
import json
import os
import subprocess
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import verification as v

BEFORE = {"phase": "before", "port": 4000, "error": "EADDRINUSE"}
AFTER = {"phase": "after", "port": 4001, "http_status": 200, "body": "FailureForge sample healthy"}


def completed(stdout="", code=0, stderr=""):
    return subprocess.CompletedProcess([], code, stdout, stderr)


def fake_runner(monkeypatch, *, exit_code=0, evidence=True, cleanup=True):
    calls = []
    def run(*args, **kwargs):
        calls.append(args)
        if args[0] == "image":
            return completed("sha256:fixture")
        if args[0] == "inspect":
            return completed(json.dumps({"Running": False, "ExitCode": exit_code}))
        if args[0] == "logs":
            return completed('\n'.join(map(json.dumps, [BEFORE, AFTER])) if evidence else 'no evidence')
        if args[0] == "rm":
            return completed(code=0 if cleanup else 1)
        return completed("container-id")
    monkeypatch.setattr(v, '_docker', run)
    return calls


def test_pass_requires_evidence_and_cleanup(monkeypatch):
    calls = fake_runner(monkeypatch)
    result = v.verify_port_conflict()
    assert result.status == "passed" and result.docker_ran
    assert result.before == BEFORE and result.after == AFTER
    assert result.cleanup_succeeded
    run = next(call for call in calls if call[0] == 'run')
    for flag in ('--network=none', '--read-only', '--cap-drop=ALL', '--pids-limit=32', '--memory=64m', '--cpus=0.5', '--pull=never', '--user=65534:65534', '--security-opt=no-new-privileges'):
        assert flag in run
    assert not any(flag in run for flag in ('-v', '--mount', '-p', '--privileged'))
    assert calls[-1][0:2] == ('rm', '--force')


@pytest.mark.parametrize('exit_code,evidence,cleanup,status', [(1, True, True, 'failed'), (0, False, True, 'failed'), (0, True, False, 'error')])
def test_cannot_claim_pass(monkeypatch, exit_code, evidence, cleanup, status):
    fake_runner(monkeypatch, exit_code=exit_code, evidence=evidence, cleanup=cleanup)
    assert v.verify_port_conflict().status == status


def test_missing_docker(monkeypatch):
    monkeypatch.setattr(v, '_docker', Mock(side_effect=FileNotFoundError()))
    result = v.verify_port_conflict()
    assert result.status == 'unavailable' and not result.docker_ran
    assert result.cleanup_succeeded is None


@pytest.mark.parametrize('failure', [subprocess.TimeoutExpired('docker', 5), RuntimeError('inspect failed')])
def test_cleanup_on_exception(monkeypatch, failure):
    runner = Mock(side_effect=[completed('sha256:fixture'), completed('id'), failure, completed()])
    monkeypatch.setattr(v, '_docker', runner)
    result = v.verify_port_conflict()
    assert result.status in ('timeout', 'error')
    assert result.cleanup_succeeded
    assert runner.call_args.args[:2] == ('rm', '--force')


def test_busy():
    with v._lock:
        assert v.verify_port_conflict().status == 'busy'


def test_api_allowlist_and_no_meta(monkeypatch):
    fake_runner(monkeypatch)
    meta = Mock(side_effect=AssertionError('Meta must never be called'))
    monkeypatch.setattr('app.main.diagnose_with_meta', meta)
    monkeypatch.setenv('DEMO_MODE', 'true')
    client = TestClient(app)
    for body in ({'scenario': 'arbitrary'}, {'scenario': 'port-conflict', 'command': 'anything'}, {}):
        assert client.post('/api/verify-fix', json=body).status_code == 422
    assert client.post('/api/verify-fix', json={'scenario': 'port-conflict'}).json()['status'] == 'passed'
    for logs in ('Error EADDRINUSE', 'Error ECONNREFUSED', 'Error ETIMEDOUT'):
        assert client.post('/api/analyze', json={'logs': logs}).json()['mode'] == 'demo'
    meta.assert_not_called()


def test_subprocess_is_bounded_and_no_shell(monkeypatch):
    run = Mock(return_value=completed())
    monkeypatch.setattr(subprocess, 'run', run)
    v._docker('image', 'inspect', v.IMAGE)
    assert run.call_args.args[0] == ['docker', 'image', 'inspect', v.IMAGE]
    assert run.call_args.kwargs['shell'] is False
    assert run.call_args.kwargs['timeout'] == 5


@pytest.mark.skipif(os.getenv('RUN_DOCKER_TESTS') != '1', reason='Requires real Docker and built lab image')
def test_real_docker_port_conflict():
    result = v.verify_port_conflict()
    assert result.status == 'passed', result.model_dump()
    assert result.docker_ran and result.cleanup_succeeded


def test_missing_image_or_daemon(monkeypatch):
    runner = Mock(return_value=completed(code=1))
    monkeypatch.setattr(v, '_docker', runner)
    result = v.verify_port_conflict()
    assert result.status == 'unavailable' and not result.docker_ran
    assert runner.call_count == 1


def test_start_failure_still_cleans_up(monkeypatch):
    runner = Mock(side_effect=[completed('sha256:fixture'), completed(code=1, stderr='start failed'), completed()])
    monkeypatch.setattr(v, '_docker', runner)
    result = v.verify_port_conflict()
    assert result.status == 'error' and not result.docker_ran
    assert result.cleanup_succeeded
    assert runner.call_args.args[:2] == ('rm', '--force')
