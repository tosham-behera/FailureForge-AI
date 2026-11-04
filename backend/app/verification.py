"""Allowlisted Docker lab runner. Never accepts commands, paths, or images from clients."""
import json
import subprocess
import threading
import time
import uuid

from .schemas import VerifyResponse

IMAGE = "failureforge-port-conflict:1"
DATABASE_IMAGE = "failureforge-database-connectivity:1"
_lock = threading.Lock()


def _docker(*args: str, timeout: float = 5):
    return subprocess.run(["docker", *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout,
                          shell=False)


def verify_port_conflict() -> VerifyResponse:
    return verify_scenario("port-conflict")


def verify_scenario(scenario: str) -> VerifyResponse:
    images = {"port-conflict": IMAGE, "database-connectivity": DATABASE_IMAGE}
    if scenario not in images:
        raise ValueError("Unsupported verification scenario")
    if not _lock.acquire(blocking=False):
        return VerifyResponse(scenario=scenario, status="busy", errors=["A verification is already running."])
    result = VerifyResponse(scenario=scenario, status="error")
    if scenario == "database-connectivity":
        result.note = "Tests a simulated TCP database dependency in an isolated sample. Does not repair or verify real MySQL. No Meta API calls."
    name = "failureforge-verify-" + uuid.uuid4().hex
    attempted = False
    try:
        check = _docker("image", "inspect", images[scenario], "--format", "{{.Id}}")
        if check.returncode:
            result.status = "unavailable"
            result.errors.append("Docker is unavailable or the lab image is missing. Build the documented image first.")
            return result
        # Pin this invocation to the inspected local image; never pull implicitly.
        image_id = check.stdout.strip()
        attempted = True
        start = _docker("run", "--detach", "--pull=never", "--name", name,
                        "--network=none", "--read-only", "--cap-drop=ALL",
                        "--security-opt=no-new-privileges", "--user=65534:65534",
                        "--cpus=0.5", "--memory=64m", "--memory-swap=64m",
                        "--pids-limit=32", "--ulimit", "nofile=64:64",
                        "--log-driver=local", "--log-opt=max-size=1m",'--log-opt', 'compress=false',
                        "--log-opt=max-file=1", image_id)
        if start.returncode:
            result.errors.append("Docker could not start the lab: " + start.stderr[:2000])
            return result
        result.docker_ran = True
        deadline = time.monotonic() + 15
        while True:
            state = _docker("inspect", "--format", "{{json .State}}", name)
            if state.returncode:
                raise RuntimeError("Could not inspect the lab container")
            details = json.loads(state.stdout)
            if not details["Running"]:
                break
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired("Docker lab", 15)
            time.sleep(0.2)
        logs = _docker("logs", "--tail=100", name)
        if logs.returncode:
            raise RuntimeError("Could not collect container logs")
        result.logs = (logs.stdout + logs.stderr)[:16000]
        for line in logs.stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict) and event.get("phase") in {"before", "after"}:
                setattr(result, event["phase"], event)
        evidence_passed = (result.before.get("error") == "EADDRINUSE"
                  and result.before.get("port") == 4000
                  and result.after.get("port") == 4001
                  and result.after.get("http_status") == 200
                  and result.after.get("body") == "FailureForge sample healthy")
        if scenario == "database-connectivity":
            evidence_passed = (result.before.get("error") == "ECONNREFUSED"
                               and result.before.get("port") == 54321
                               and result.after.get("port") == 54321
                               and result.after.get("connected") is True
                               and result.after.get("recovery_action") == "start-sample-dependency"
                               and result.after.get("reply") == "FailureForge simulated database ready")
        passed = details["ExitCode"] == 0 and not details.get("OOMKilled", False) and evidence_passed
        result.status = "passed" if passed else "failed"
        if not passed:
            result.errors.append(f"Required evidence missing or lab failed (exit {details['ExitCode']}).")
    except FileNotFoundError:
        result.status = "unavailable"
        result.errors.append("Docker CLI is not installed or is not on the backend PATH.")
    except subprocess.TimeoutExpired:
        result.status = "timeout"
        result.errors.append("Docker operation exceeded its execution timeout.")
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        result.status = "error"
        result.errors.append(str(exc)[:2000])
    finally:
        if attempted:
            try:
                cleanup = _docker("rm", "--force", name)
                result.cleanup_succeeded = cleanup.returncode == 0 or "No such container" in cleanup.stderr
            except (OSError, subprocess.TimeoutExpired):
                result.cleanup_succeeded = False
            if not result.cleanup_succeeded:
                result.status = "error"
                result.errors.append(f"Cleanup failed; remove temporary container {name} when Docker is available.")
        _lock.release()
    return result
