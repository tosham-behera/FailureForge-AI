# Regression verification — November 4, 2026 IST

Resumed existing implementation and working-tree changes after checkpoint 51c6bb7. No feature rewrite or new dependency was needed. Updated outdated documentation and captured the actual browser workflow.

| Check | Result | Evidence |
|---|---|---|
| Backend suite, Docker enabled | 62 passed, one deprecation warning | Real application, mocked provider |
| Frontend tests | 11 passed | Node test runner |
| Production build | Passed | Installed Vite |
| Three offline samples | HTTP 200 and rendered diagnoses | Browser/backend |
| Multiple uploads/timeline | Two sources, repeated count 2, clock and undated groups | Browser/backend |
| Investigation | Two preserved rounds, updated networking hypothesis/questions | Browser, offline rules |
| Port conflict | passed, docker_ran true, cleanup_succeeded true | Real Docker tests and browser endpoint |
| Database connectivity | passed, docker_ran true, cleanup_succeeded true | Real Docker tests and browser endpoint |
| Report export | Download contains both rounds, sources, sample runs, limitations | Browser download checked on disk |
| Rate-limit recovery | Error visible; both previous rounds and typed evidence retained | Browser with mocked HTTP 429; route removed afterward |
| Docker cleanup | No failureforge-verify containers remaining | Docker container listing |
| Meta protocol/errors/source attribution | Tests pass | Mock HTTP through actual SDK parser |

## Failed attempts and limitations

The first Docker-enabled run had 61 passes and one database fixture timeout before Docker execution was confirmed. Image inspection succeeded; the immediate full rerun passed all 62 tests and both subsequent browser Docker calls passed. This is consistent with transient Docker startup latency, not proof of a fixture logic defect. Existing five-second CLI timeouts remain; no automatic retry was added.

An earlier shell-tool launch selected WSL instead of Git Bash: the opt-in flag did not reach Windows Python (60 passed, two skipped), and Node was unavailable there. Invoking the installed Git Bash executable from the native shell resolved the tooling issue.

Starlette TestClient emits an httpx deprecation warning; no dependencies were changed. Independent clean-machine dependency installation and live multi-turn Meta calls were not performed. Existing environment startup/build work. Earlier live single-request results are owner-reported, not revalidated here.

No environment/credential files were read or modified in this resumed session. Ignore checks cover backend/.env and frontend/.env.local; tracked .env/.pem/.key paths were absent. The untracked environment example remains unreviewed. Changes remain uncommitted for owner review.
