import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import demo_mode, model_name
from .demo import diagnose_demo
from .meta_model import MetaDiagnosisError, diagnose_with_meta
from .safety import redact_secrets
from .schemas import AnalyzeRequest, AnalyzeResponse
from .schemas import VerifyRequest, VerifyResponse
from .verification import verify_port_conflict

logger = logging.getLogger(__name__)
app = FastAPI(title="FailureForge AI", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "demo" if demo_mode() else "meta", "model": model_name()}


@app.post("/api/verify-fix", response_model=VerifyResponse)
def verify_fix(req: VerifyRequest):
    return verify_port_conflict()


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    # Do not log raw log contents or send known credentials to the model.
    safe_logs = redact_secrets(req.logs)
    if demo_mode():
        result = diagnose_demo(safe_logs)
        return AnalyzeResponse(
            mode="demo", diagnosis=result,
            note="Offline demo pattern matching — no Meta API call was made. Results are not verified.",
        )
    try:
        result = diagnose_with_meta(safe_logs, redact_secrets(req.app_name))
    except MetaDiagnosisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from None
    except Exception as exc:
        # Keep token values and third-party error details out of browser responses.
        logger.warning("Model request failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="Meta Model API request failed. Check the API key, credits, model access and server logs.",
        ) from exc
    return AnalyzeResponse(
        mode="meta", diagnosis=result,
        note="AI-generated hypothesis, not a verified fix. Review evidence before taking action.",
    )
