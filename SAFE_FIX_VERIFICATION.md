# Safe Fix Verification: port conflict

The endpoint runs a fixed Docker sample, never the application described by pasted logs. No Meta API calls are made by verification. Keep `DEMO_MODE=true` for offline diagnosis too.

## Setup and real verification

Install/start Docker Desktop with Linux containers. From the repository root, build the reviewed fixture (the initial Python base-image download requires network access):

```powershell
docker build --tag failureforge-port-conflict:1 backend/docker/port-conflict
```

The build context contains only the fixture and Dockerfile. No host directory is mounted at runtime. The backend never builds or pulls images on request. Rebuild after changing the fixture; the local image tag is trusted operator-managed code.

Start FastAPI and Vite as in the README. Select **Port conflict**, analyze it, then click **Verify Fix**. The API request is:

```http
POST /api/verify-fix
Content-Type: application/json

{"scenario":"port-conflict"}
```

Unknown scenarios and additional fields (including commands, paths and images) receive HTTP 422. Operational results use HTTP 200 with `status`: `passed`, `failed`, `error`, `timeout`, `unavailable`, or `busy`. Responses include `docker_ran`, `before`, `after`, bounded `logs`, `errors`, and `cleanup_succeeded` (null when no container was attempted).

A pass requires the actual container to exit zero, emit EADDRINUSE on 4000 and return the expected HTTP 200 body on 4001, and complete cleanup. It proves only this controlled sample. An absent Docker CLI/daemon/image is unavailable, never a simulated pass.

## Isolation and limits

The fixed Python HTTP app and port blocker live inside one disposable container. It has no external network, published ports, host mounts, Docker socket, or host environment credentials. Runtime uses UID 65534, read-only root, all capabilities dropped, no new privileges, 0.5 CPU, 64 MiB RAM with no extra swap, 32 PIDs, and 64 file descriptors. Container logs rotate at 1 MiB. The fixture has a 10-second alarm; the runner polls for at most 15 seconds with each Docker CLI operation limited to 5 seconds. Cleanup has its own 5-second timeout. Total request time can exceed 15 seconds due to CLI and cleanup operations.

A nonblocking process-local lock allows one test per backend process. Run this local prototype with one FastAPI worker, bound to loopback. It has no authentication or distributed rate limit and is not intended as a public execution service. The host Docker daemon remains a trusted prerequisite.

Cleanup always attempts `docker rm --force` for the generated container name after a run attempt. If Docker becomes unreachable, cleanup cannot be guaranteed: the response reports the exact name to remove after Docker recovers and cannot report a pass. Host/backend crashes also require operator cleanup. The fixture's alarm bounds execution while the daemon is healthy.

## Tests

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
$env:RUN_DOCKER_TESTS='1'
.\.venv\Scripts\python.exe -m pytest tests/test_verification.py::test_real_docker_port_conflict -q
Remove-Item Env:RUN_DOCKER_TESTS
```

Unit tests mock Docker and are not evidence of a Docker pass. The opt-in integration test invokes the real runner, requires the built image, and fails if Docker is unavailable.

## Files added or changed

- `backend/docker/port-conflict/Dockerfile`: builds the non-root sample image.
- `backend/docker/port-conflict/.dockerignore`: limits the build context.
- `backend/docker/port-conflict/sample.py`: reproduces the conflict and probes the fixed port.
- `backend/app/verification.py`: fixed Docker runner, isolation, limits, evidence validation and cleanup.
- `backend/app/schemas.py`: strict scenario request and structured verification response.
- `backend/app/main.py`: adds the verification endpoint without changing diagnosis routing.
- `backend/tests/test_verification.py`: mocked safety/error tests and opt-in real Docker integration test.
- `frontend/src/VerifyFix.jsx`: button, loading/error states, evidence and logs.
- `frontend/src/main.jsx`: displays verification only for a port-conflict diagnosis.
- `frontend/src/styles.css`: readable evidence/log styling.
- `.vscode/tasks.json`: repeatable frontend build task.
- `README.md`: links this workflow and updates implementation status.
- `SAFE_FIX_VERIFICATION.md`: setup, API semantics, safety boundaries, tests and change inventory.

The existing backend `.env` remains unchanged with `DEMO_MODE=true`.
