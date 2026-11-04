# Security and credit protection

Demo development needs no key. Process DEMO_MODE=true overrides private dotenv settings without changing the file. Never overwrite existing environment files. Keep credentials backend-only, never in React, VITE variables, screenshots, logs or repository content.

Live calls require explicit Analyze or Continue actions; there are no automatic provider retries. Use synthetic logs for owner-authorized live tests. Do not expose this prototype publicly without authentication, rate limits and spend controls.

Uploads are bounded UTF-8 text with plain filenames, never saved to the server or executed. Logs and prior model output are untrusted prompt data. Redaction is best-effort: review evidence and reports before sharing. Docker accepts only two fixed fixtures; see [isolation](SAFE_FIX_VERIFICATION.md).

## Before publishing

Inspect paths without displaying secret contents:

```bash
git status --short
git check-ignore backend/.env frontend/.env.local
git ls-files '*.env' '*.pem' '*.key'
```

Environment paths should be ignored and tracked secret paths absent. Stage explicitly reviewed source/documentation paths, then inspect git diff --cached --name-only and staged source changes. Do not blindly stage everything. This regression session did not read or stage the existing untracked backend/.env.example; privately review it before publishing.

Ignore rules do not protect already committed secrets. If a credential was published, revoke it and review history. Reports are client-supplied snapshots, not authenticated audit records. No API keys were read or modified during this resumed session.
