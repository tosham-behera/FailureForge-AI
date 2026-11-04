import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .limits import RequestSizeLimit

from .config import demo_mode, model_name
from .demo import diagnose_demo
from .meta_model import MetaDiagnosisError, diagnose_with_meta
from .safety import redact_secrets
from .schemas import AnalyzeRequest, AnalyzeResponse
from .schemas import VerifyRequest, VerifyResponse
from .schemas import InvestigationRequest
from .safety import redact_tree
from .verification import verify_scenario
from .evidence import prepare_evidence, locate_evidence, investigation_events
from .schemas import ReportRequest
from .report import incident_report

logger = logging.getLogger(__name__)
app = FastAPI(title="FailureForge AI", version="0.1.0")
app.add_middleware(RequestSizeLimit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # FastAPI's default errors echo input values, which may contain credentials.
    message = exc.errors()[0]['msg'] if exc.errors() else 'Invalid request'
    return JSONResponse(status_code=422, content={'detail': 'Invalid input: ' + message})


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "demo" if demo_mode() else "meta", "model": model_name()}


@app.post("/api/report")
def report(req: ReportRequest):
    return {"filename": "failureforge-incident-report.md", "markdown": incident_report(req)}


@app.post("/api/verify-fix", response_model=VerifyResponse)
def verify_fix(req: VerifyRequest):
    return verify_scenario(req.scenario)


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    # Do not log raw log contents or send known credentials to the model.
    try:
        safe_logs, timeline = prepare_evidence(req)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    if demo_mode():
        result = diagnose_demo(safe_logs)
        return AnalyzeResponse(
            mode="demo", diagnosis=result, input_evidence=safe_logs, timeline=timeline,
            evidence_locations=locate_evidence(result, timeline),
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
        mode="meta", diagnosis=result, model=model_name(), input_evidence=safe_logs, timeline=timeline,
        evidence_locations=locate_evidence(result, timeline),
        note="AI-generated hypothesis, not a verified fix. Review evidence before taking action.",
    )


@app.post("/api/investigate", response_model=AnalyzeResponse)
def investigate(req: InvestigationRequest):
    evidence = redact_secrets(req.evidence)
    history = redact_tree([{'evidence':turn.evidence, 'result':turn.result.model_dump(
        exclude={'timeline', 'evidence_locations', 'input_evidence'})} for turn in req.history])
    if demo_mode():
        combined = "\n".join(turn["evidence"] for turn in history) + "\n" + evidence
        result = diagnose_demo(combined)
        result.what_changed = "Additional evidence recorded. Offline rules cannot reason through investigation history; hypotheses remain unverified."
        if "docker" in evidence.lower() and result.failure_type == "Connection refused":
            result.probable_root_cause = "Separate containers may require a shared network and a service hostname instead of localhost. This is an offline hypothesis."
            result.questions = ["Do both containers share a Docker network?", "What database hostname and port does the application use (omit credentials)?"]
            result.what_changed = "New evidence mentions Docker; container networking is now an additional possibility under offline rules."
        return AnalyzeResponse(mode="demo", diagnosis=result, input_evidence=evidence,
                               note="Offline investigation rules; no Meta request or verification was performed.")
    try:
        result = diagnose_with_meta(evidence, redact_secrets(req.app_name), history)
    except MetaDiagnosisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from None
    except Exception:
        raise HTTPException(status_code=502, detail="Investigation failed. Previous results are preserved; try again later.") from None
    prior_events = investigation_events(history, evidence)
    return AnalyzeResponse(mode="meta", diagnosis=result, model=model_name(), input_evidence=evidence,
                           evidence_locations=locate_evidence(result, prior_events),
                           note="Updated AI hypotheses; supplied observations are not independently verified. No tools were run.")
