# FailureForge interactive investigation

## Start the existing installation (PowerShell)

Do not overwrite `.env`. The saved key remains backend-only. Force demo mode for
development even if your private configuration was used for earlier live tests.

Backend terminal:

```powershell
cd backend
$env:DEMO_MODE='true'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Frontend terminal:

```powershell
cd frontend
npm run dev
```

Open http://127.0.0.1:5173. The existing Vite proxy uses port 8001. Confirm DEMO
MODE before development. Health requests never call Meta. The VS Code demo
startup task uses the same port. Stop an existing backend before restarting it.

## Demonstration

1. Clear the manual example if you want to analyze files alone. Choose UTF-8
   `.log` / `.txt` files using the file picker. No local files are discovered or
   read automatically. Selection alone makes no backend or Meta request.
2. Click Analyze. Files and manual text are sent as bounded JSON text, never saved
   on the server or executed. Each source line receives a reference such as S1:L2.
3. Inspect observations, unconfirmed hypotheses, supporting line references,
   confidence, questions, and the timeline. Repeated messages count exact
   whitespace-normalized messages after recognized timestamps are removed.
4. Add answers or additional log text under Investigate Further. Click Continue
   Investigation to request exactly one new analysis. Earlier rounds remain
   visible. In demo mode, the Docker/container answer to a connection-refused
   incident demonstrates a deterministic networking hypothesis, not AI reasoning.
5. Choose an approved Docker scenario and click Verify Fix. The database scenario
   starts a **simulated TCP dependency**, not MySQL. It first proves ECONNREFUSED,
   then starts its predefined sample server and checks the expected response.
   Both phases run inside one disposable network-isolated container. Neither
   scenario changes the actual application or accepts commands/images/paths.
6. Click Download Incident Report. The Markdown includes redacted evidence,
   chronological rounds, hypotheses, source references, questions, checks,
   mode/model, recorded sample runs, and limitations. Export does not call Meta.

Suggested synthetic files:

`application.log`:

```text
10:01:05 ERROR ECONNREFUSED 127.0.0.1:3306
10:01:06 ERROR ECONNREFUSED 127.0.0.1:3306
```

`database.txt`:

```text
10:01:02 Database stopped unexpectedly
No timestamp: restart pending
```

Follow-up: `MySQL runs in Docker, and Node runs in another container.`

Clock-only timestamps are shown in clock order with date/timezone explicitly
unknown. This does not prove both files describe the same day or synchronized
clocks. UTC-aware, timezone-unknown, clock-only and undated groups are separate;
the application never asserts a single global order across these groups. Supported
formats include ISO dates with T or space, optional fractions, Z/UTC offsets, and
HH:MM:SS. Unrecognized/invalid timestamps remain undated. Proximity is not causation.

## Limits and safety

- Four files; 16 KiB / 12,000 characters per file; unique plain filenames.
- Combined manual/file evidence: 8–20,000 characters, 32 KiB, 600 lines; source
  annotations are additionally bounded at 24,000 characters.
- Manual input remains limited to 12,000 characters. Follow-up input: 8–6,000.
- Five rounds maximum; 60,000-character serialized investigation request limit.
  Duplicate timeline/raw-response metadata is omitted from model history.
- Report: five rounds, ten sample runs, 250,000-character serialized limit.
- POST request buffering has a 512 KiB cap before JSON parsing, including chunked
  requests. Validation errors do not echo submitted values.
- Meta uses the existing configuration, one explicit request per Analyze/Continue,
  no automatic retries, a 35-second SDK network-operation timeout and a 4,000-token
  output budget. No tool calls or shell execution are available to the model.
- History lives only in React memory: reload closes the investigation. Starting a
  successful new analysis replaces that incident. Export before reloading.
- Source observations are user-provided; hypotheses remain unconfirmed. Meta
  evidence quotes must occur in supplied evidence, not just prior model output.
- Docker retains read-only filesystem, no external network or host mounts,
  non-root user, dropped capabilities, CPU/memory/PID limits, bounded subprocesses,
  no implicit image pulls, shared concurrency lock and forced cleanup.
- Reports are client-supplied snapshots, not signed audit records. Redaction is
  best-effort, so review logs and exported reports before sharing.

## Build the fixed database fixture

From the project root with Docker Desktop running:

```powershell
docker build --pull=false -t failureforge-database-connectivity:1 backend/docker/database-connectivity
```

The existing port-conflict image remains `failureforge-port-conflict:1`.

## Tests (no live Meta requests)

```powershell
cd backend
$env:DEMO_MODE='true'
$env:RUN_DOCKER_TESTS='1'
.\.venv\Scripts\python.exe -m pytest -q
```

Both images must already exist for the real Docker tests. Without
RUN_DOCKER_TESTS=1 those two tests are explicitly skipped. Provider tests use the
real SDK parser with in-memory HTTP responses; HTTP transports are blocked by an
autouse fixture. Coverage includes upload security/limits, timestamp groups,
repetitions, source attribution, context passing, prior-model evidence rejection,
rate limits, redaction, both Docker scenarios, report export, and the full mocked
Meta workflow through report generation.

```powershell
cd frontend
node --test src/api.test.js src/uploads.test.js
npm run build
```

The new multi-turn Meta protocol has only been tested with mocked responses.
Do not infer live-provider quality from demo rules or mocks. A controlled live
test requires your explicit choice: temporarily set process DEMO_MODE=false,
restart, Analyze once, then Continue once after inspecting the first response.
That is up to **two paid model calls**. Restore DEMO_MODE=true and restart afterward.

## Implementation map

- [API and validation](backend/app/main.py), [schemas](backend/app/schemas.py),
  [request cap](backend/app/limits.py): existing routes preserved; new
  `/api/investigate` and `/api/report` endpoints.
- [Meta adapter](backend/app/meta_model.py), [redaction](backend/app/safety.py):
  bounded context, structured questions/change explanations, source-grounded
  hypothesis evidence and safe provider failures.
- [Evidence processing](backend/app/evidence.py): timeline groups, repetition
  counts and deterministic source-line locations.
- [Verifier](backend/app/verification.py), [database fixture](backend/docker/database-connectivity/):
  two allowlisted isolated simulations with evidence and cleanup checks.
- [Report generator](backend/app/report.py): redacted, honest Markdown.
- [React workflow](frontend/src/main.jsx), [diagnosis](frontend/src/Diagnosis.jsx),
  [timeline](frontend/src/Timeline.jsx), [file reader](frontend/src/uploads.js),
  [verification](frontend/src/VerifyFix.jsx): existing layout with functional additions.
- [Backend tests](backend/tests/) and [upload tests](frontend/src/uploads.test.js).

Pre-change Git checkpoint: `51c6bb7`. No secret file was included.
