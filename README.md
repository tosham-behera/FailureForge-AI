# FailureForge AI — Hackathon MVP (v0.1)

> AI-assisted incident diagnosis. **No changes to your applications. Optional fixed Docker sample verification.**

Built for the Meta Global AI Developer Hackathon 2026. Frontend: React/Vite. Backend: FastAPI. AI: Meta Muse Spark 1.3 via Meta Model API (OpenAI-compatible SDK, schema-validated responses).

## First run on Windows 11 (PowerShell)

### 1) Download/extract the ZIP and open the folder in VS Code

### 2) Backend terminal

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
$env:DEMO_MODE = 'true'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

If `py` is not installed, use `python` in the first command. If PowerShell blocks activation, run `.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000` instead.

Go to http://127.0.0.1:8000/docs for FastAPI's interactive API docs. The backend starts in **DEMO_MODE=true** without an API key.

### 3) Frontend terminal (second terminal, with Node.js 18+)

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 and click **Analyze incident**.

For an existing installation, do not recreate the environment or overwrite `.env`.
From `backend`, run `$env:DEMO_MODE = 'true'` and
`.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
From a second terminal in `frontend`, run `npm run dev`.
Confirm `/api/health` on both ports 8000 and 5173 returns `"mode":"demo"`.
Try Database down, Port conflict, and Service timeout, clicking Analyze after each.
For Port conflict, click Verify Fix and check PASSED, Docker ran: Yes,
Cleanup: Succeeded, EADDRINUSE on port 4000, and HTTP 200 on port 4001.

If Vite returns an empty HTTP 500, the backend may not be accepting connections.
Check the backend terminal for startup errors. A stale Uvicorn reload process can
hold port 8000 without serving requests: stop the old backend with Ctrl+C and
restart it using the command above. Wait for `Application startup complete`.
Reload the browser to refresh the mode badge. Use one backend process for the demo.

Frontend response handling tests: `node --test src/api.test.js` from `frontend`.

### 4) Switch on real Meta AI

Edit `backend/.env`:

```env
DEMO_MODE=false
MODEL_API_KEY=YOUR_OWN_PRIVATE_KEY
META_MODEL=muse-spark-1.3
META_BASE_URL=https://api.meta.ai/v1
```

Restart FastAPI. Refresh the frontend. The badge should say **META LIVE**. Never paste your actual API key into a chat, browser console or public repository. `.env` is gitignored. Read [SECURITY.md](SECURITY.md) before pushing to GitHub. Calls in live mode may consume credits or incur charges.

## Test backend (from backend directory)

```powershell
python -m pytest -q
```

## API

- `GET /api/health` — status and active mode.
- `POST /api/analyze` — input: `{"app_name":"My API","logs":"Error: connect ECONNREFUSED 127.0.0.1:3306"}`

## What works

- Three synthetic incident examples (DB connection refused, port already used, timeout).
- Backend validation: input 8–12,000 characters, bounded app name.
- Offline, deterministic **demo mode**, with clearly labeled results and no API calls.
- Live Meta Muse Spark diagnosis via structured output parsed as a Pydantic model.
- Basic secret redaction before sending logs to Meta; **not a complete privacy filter**.
- React diagnosis interface with evidence and safe next checks.

## What is NOT implemented yet

- Production application fixes, multi-agent orchestration, observability metrics, file upload, persistent incident history, authentication, deployments.
- Live Meta API integration was **not tested with a real key** in this starter.
- Do not paste private production logs unless you are authorized and have checked for secrets/PII.

## Recommended next milestones

1. Test live Meta inference using your own API key.
2. Add one **predefined, harmless Docker lab** with a known-good fixture: simulate a connection-refused issue, verify service status and run a prewritten test; never execute LLM-generated shell commands.
3. Run 10–15 synthetic failures and track the fraction identified correctly with supporting evidence.
4. Record a short demo showing the difference between a human searching logs and the tool's evidence-backed analysis.

Meta documentation: https://dev.meta.ai/docs/cookbook/quickstart-chat-completions and https://dev.meta.ai/docs/cookbook/structured-output

## Safe Fix Verification

Port-conflict Docker verification is implemented. See [setup, safety limits, tests and file inventory](SAFE_FIX_VERIFICATION.md). A real Docker pass requires Docker Desktop and the locally built fixture image; unit tests alone do not verify the fix.

## Unfamiliar failures and one controlled Meta test

The same log input accepts arbitrary application errors (8–12,000 characters).
Offline mode only recognizes the three demo patterns; unfamiliar failures remain
Unknown with low confidence. Meta mode uses the configured `META_BASE_URL`,
`META_MODEL` (default `muse-spark-1.3`), and backend-only `MODEL_API_KEY`.
The Pydantic result includes an explanation, leading hypothesis, alternative
possible causes, exact log excerpts, confidence, severity, and diagnostic checks.
Evidence confirms only what the supplied logs say, not the true state of a system.
Causes and repairs remain unverified. Docker verification still tests only its
fixed, allowlisted port-conflict sample and cannot execute model-generated commands.

Each Meta analysis makes one request, with a 35-second SDK timeout, a 4,000-token
output budget (including reasoning), and no automatic retries. The SDK timeout
applies to network operations, not a guaranteed total wall-clock deadline.
Rate limits/quota return HTTP 429, timeouts 504, configuration/access errors 503,
and connection, provider, malformed, refused, or ungrounded results 502. Errors
never silently fall back to offline rules. The result badge identifies its source.

Automated tests use in-memory HTTP responses with the real SDK parser and block
real HTTP transports. No live Meta inference was performed during implementation.
The live credentials, account access, latency, cost and model quality remain unverified.

Only when you choose to authorize a paid live test:

1. Stop the existing backend with Ctrl+C. Keep the saved `.env` in demo mode and
   keep your existing key private; do not paste it into the terminal or frontend.
2. In a terminal in `backend`, temporarily enable live mode for that process:

   ```powershell
   $env:DEMO_MODE = 'false'
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

3. With Vite running, refresh the browser. Check META LIVE, then paste this
   synthetic unfamiliar error and click Analyze incident **once**:

   ```text
   worker: OSError: [Errno 28] No space left on device
   Failed while writing report to /tmp/output.csv
   ```

4. Expect a META MODEL result explaining storage exhaustion, quoted log evidence,
   unconfirmed causes, confidence, and checks. A safe API error means the test did
   not succeed; do not repeatedly retry. Health checks do not call Meta.
5. Stop the backend and restore demo mode in that same terminal:

   ```powershell
   $env:DEMO_MODE = 'true'
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

   Refresh and confirm DEMO MODE. Do not overwrite `.env` or commit credentials.

Protocol reference: [Meta structured output documentation](https://dev.meta.ai/docs/cookbook/structured-output).
