from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class AnalyzeRequest(BaseModel):
    logs: str = Field(min_length=8, max_length=12000)
    app_name: str = Field(default="My application", max_length=80)


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


class AnalyzeResponse(BaseModel):
    mode: Literal["demo", "meta"]
    diagnosis: Diagnosis
    note: str


class VerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: Literal["port-conflict"]


class VerifyResponse(BaseModel):
    scenario: Literal["port-conflict"] = "port-conflict"
    status: Literal["passed", "failed", "error", "timeout", "unavailable", "busy"]
    docker_ran: bool = False
    before: dict = Field(default_factory=dict)
    after: dict = Field(default_factory=dict)
    logs: str = ""
    errors: list[str] = Field(default_factory=list)
    cleanup_succeeded: bool | None = None
    note: str = "Tests only the controlled sample; does not verify or modify your application. No Meta API calls."
