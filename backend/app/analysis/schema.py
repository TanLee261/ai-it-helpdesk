from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AnalysisRequest(BaseModel):
    ticket_id: str = Field(min_length=3)
    window_start: datetime
    window_end: datetime
    retrieval_method: Literal["bm25", "hybrid", "hybrid_rerank"] = "bm25"
    top_k: int = Field(default=3, ge=1, le=10)

    @model_validator(mode="after")
    def check_window(self) -> "AnalysisRequest":
        if self.window_start.tzinfo is None or self.window_end.tzinfo is None:
            raise ValueError("window_start and window_end must include a timezone")
        if self.window_start >= self.window_end:
            raise ValueError("window_start must precede window_end")
        if (self.window_end - self.window_start).total_seconds() > 86400:
            raise ValueError("time window must not exceed 24 hours")
        return self


class Evidence(BaseModel):
    evidence_id: str
    source_type: Literal["ticket", "historical_ticket", "runbook", "log", "metric"]
    content: str
    service: str
    timestamp: datetime | None = None


class CitedFact(BaseModel):
    fact: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)


class Hypothesis(BaseModel):
    cause: str = Field(min_length=1)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)


class VerificationStep(BaseModel):
    step: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)


class RcaDraft(BaseModel):
    status: Literal["grounded", "insufficient_evidence"]
    observed_facts: list[CitedFact]
    hypotheses: list[Hypothesis]
    probable_root_cause: str | None = None
    root_cause_evidence_ids: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"]
    missing_evidence: list[str]
    verification_steps: list[VerificationStep]
    proposed_actions: list[str]


class AnalysisResponse(RcaDraft):
    ticket_id: str
    service: str
    window_start: datetime
    window_end: datetime
    evidence: list[Evidence]
    model: str | None = None
    review_required: bool = True
