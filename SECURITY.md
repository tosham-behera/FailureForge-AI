# Keep your Meta API key safe

## Before you run the app

1. Copy `backend/.env.example` to `backend/.env`.
2. Leave `DEMO_MODE=true` while building the UI and debugging locally. Demo mode makes no Meta API calls.
3. When you are ready for real testing, set `DEMO_MODE=false` and put the secret in `backend/.env` as `MODEL_API_KEY=...`.
4. **Never paste your key into frontend files, a React `VITE_` variable, a screenshot, an AI coding-agent prompt, or a public GitHub issue.** Only the local FastAPI backend should read it.
5. Keep `.env.example` as a placeholder-only template, with no real keys.

## Before your first GitHub push

From the project root, run:

```powershell
git status --short
git check-ignore -v backend/.env
```

`git check-ignore` should print a rule from `.gitignore`, showing that `backend/.env` is excluded. If it doesn't, stop and check where your repo root and `.gitignore` are located. If you have not created `backend/.env` yet, create it from the example first.

Then stage and inspect exactly what will be uploaded:

```powershell
git add .
git diff --cached --name-only
```

Confirm that `backend/.env`, `.env.local`, private keys, and any sensitive local files are **not** listed. Use `git diff --cached` to inspect content before you commit.

**Important:** `.gitignore` prevents Git from adding matching *untracked* files. It does **not** untrack secrets already committed or staged. If an `.env` is already tracked, run `git rm --cached backend/.env` (preserves the local file) and commit its removal. If a real key was ever pushed to GitHub, **revoke/rotate it immediately**: deleting it from the latest commit does not make that key safe again.

## Protect API credits

- Start with `DEMO_MODE=true`.
- Use real Meta API calls only for a few planned integration tests.
- Don't expose a live API-powered backend publicly without authentication, rate limits, and spend controls.
- The current backend only performs **basic redaction** of known secret patterns in logs. Do not send confidential production logs, access tokens, or personal data to it.
