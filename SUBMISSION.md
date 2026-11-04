# FailureForge AI — submission summary

FailureForge AI turns application logs into an interactive investigation with explicit evidence and controlled experiments. Developers upload multiple logs, inspect structured hypotheses and supporting lines, answer targeted questions, and retain each updated diagnosis. A timeline groups comparable timestamps and highlights repetition without claiming correlation proves causation.

React/Vite talks to FastAPI. Meta Muse Spark 1.3 provides structured diagnosis and follow-up reasoning through the existing Meta Model API adapter. Bounded context, explicit request buttons, safe errors and offline demo mode control cost. The model cannot execute commands.

Two allowlisted Docker fixtures reproduce port conflicts and a missing simulated TCP dependency, apply predefined sample recovery actions, and record before/after results with cleanup. These experiments do not repair the real application. Markdown export combines investigation history, evidence, recommendations, model/mode, sample findings and limitations.

Verified locally: 62 backend tests including two real Docker integrations, 11 frontend tests, production build, and browser workflow from multiple uploads through two rounds, both Docker scenarios and report download. Provider behavior in this regression uses mocks; multi-turn live Meta quality remains unverified. No live calls were made. This is a local hackathon prototype without persistent case storage or production authentication.

See [README](README.md) and [verification record](VERIFICATION.md).
