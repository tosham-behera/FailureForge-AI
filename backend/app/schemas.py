from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class LogSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=12000)

    @model_validator(mode="after")
    def safe_text_file(self):
        if any(c in self.name for c in '/\\:') or '..' in self.name or not self.name.lower().endswith(('.log', '.txt')):
            raise ValueError("Use a plain .log or .txt filename without paths")
        if len(self.content.encode('utf-8')) > 16384:
            raise ValueError("Each file must be at most 16 KiB")
        if any(ord(c) < 32 and c not in '\n\r\t' for c in self.content + self.name):
            raise ValueError("Only text logs are accepted")
        return self


class AnalyzeRequest(BaseModel):
    logs: str = Field(default="", max_length=12000)
    app_name: str = Field(default="My application", max_length=80)
    sources: list[LogSource] = Field(default_factory=list, max_length=4)

    @model_validator(mode="after")
    def bounded_sources(self):
        text = self.logs + ''.join(source.content for source in self.sources)
        if not 8 <= len(text.strip()) <= 20000 or len(text.encode('utf-8')) > 32768:
            raise ValueError("Supply 8–20,000 characters and at most 32 KiB total evidence")
        if sum(len(t.splitlines()) for t in [self.logs, *[s.content for s in self.sources]]) > 600:
            raise ValueError("At most 600 log lines are supported per incident")
        if len({s.name for s in self.sources}) != len(self.sources):
            raise ValueError("Source filenames must be unique")
        return self


class HypothesisSupport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hypothesis: str
    evidence: list[str]


class Diagnosis(BaseModel):
    """The exact shape we ask Meta's model to return."""
    model_config = ConfigDict(extra="forbid")

    failure_type: str
    severity: Literal["low", "medium", "high"]
    confidence: Literal["low", "medium", "high"]
    summary: str
    probable_root_cause: str
    possible_causes: list[str] = Field(default_factory=list)
    evidence: list[str]
    recommended_checks: list[str]
    questions: list[str] = Field(default_factory=lambda: [
        "Where does the failing service run, and what dependencies does it use?",
        "What changed before the failure, and what additional logs are available?",
    ], min_length=2, max_length=3)
    what_changed: str = "Initial diagnosis; no previous investigation round."
    hypothesis_support: list[HypothesisSupport] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    mode: Literal["demo", "meta"]
    diagnosis: Diagnosis
    note: str
    model: str = "offline-rules"
    input_evidence: str = ""
    timeline: list[dict] = Field(default_factory=list)
    evidence_locations: list[dict] = Field(default_factory=list)


class InvestigationTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence: str = Field(min_length=1, max_length=24000)
    result: AnalyzeResponse


class InvestigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_name: str = Field(default="My application", max_length=80)
    evidence: str = Field(min_length=8, max_length=6000)
    history: list[InvestigationTurn] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def bounded_history(self):
        if len(self.model_dump_json()) > 60000:
            raise ValueError("Investigation context exceeds 60,000 characters; start a new incident with a concise summary.")
        if not self.evidence.strip():
            raise ValueError("Additional evidence cannot be blank")
        return self


class VerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: Literal["port-conflict", "database-connectivity"]


class VerifyResponse(BaseModel):
    scenario: Literal["port-conflict", "database-connectivity"] = "port-conflict"
    status: Literal["passed", "failed", "error", "timeout", "unavailable", "busy"]
    docker_ran: bool = False
    before: dict = Field(default_factory=dict)
    after: dict = Field(default_factory=dict)
    logs: str = ""
    errors: list[str] = Field(default_factory=list)
    cleanup_succeeded: bool | None = None
    note: str = "Tests only the controlled sample; does not verify or modify your application. No Meta API calls."


class VerificationRecord(BaseModel):
    round: int = Field(ge=1, le=5)
    result: VerifyResponse


class ReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_name: str = Field(max_length=80)
    history: list[InvestigationTurn] = Field(min_length=1, max_length=5)
    verifications: list[VerificationRecord] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def bounded_report(self):
        if len(self.model_dump_json()) > 250000:
            raise ValueError("Report exceeds 250,000 characters; shorten evidence")
        return self
