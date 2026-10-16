from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class RetrievalRequest(BaseModel):
    query: Optional[str] = Field(default=None, min_length=2)
    ticket_id: Optional[str] = Field(default=None, min_length=3)
    method: Literal["bm25", "dense", "hybrid", "hybrid_rerank"] = "bm25"
    rewrite: bool = False
    service: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    source_types: list[str] = Field(default_factory=lambda: ["runbook", "historical_ticket"])
    access_scope: str = "it_internal"
    top_k: int = Field(default=5, ge=1, le=50)
    candidate_k: int = Field(default=50, ge=5, le=200)
    rerank_k: int = Field(default=20, ge=1, le=50)

    @model_validator(mode="after")
    def require_query_or_ticket_id(self) -> "RetrievalRequest":
        if not self.query and not self.ticket_id:
            raise ValueError("Either query or ticket_id is required")
        if self.method == "hybrid_rerank" and "candidate_k" not in self.model_fields_set:
            self.candidate_k = 20
        if self.candidate_k < self.top_k:
            raise ValueError("candidate_k must be at least top_k")
        if self.method == "hybrid_rerank" and self.rerank_k < self.top_k:
            raise ValueError("rerank_k must be at least top_k")
        return self


class RetrievalFilters(BaseModel):
    service: Optional[str]
    category: Optional[str]
    version: Optional[str]
    source_types: list[str]
    access_scope: str


class RetrievalResult(BaseModel):
    rank: int
    score: float
    chunk_id: str
    document_id: str
    source_type: str
    source: str
    service: Optional[str]
    category: Optional[str]
    access_scope: str
    content: str
    metadata: dict[str, Any]


class RetrievalResponse(BaseModel):
    query: str
    retrieval_method: str
    filters: RetrievalFilters
    results: list[RetrievalResult]
    original_query: Optional[str] = None
    intent: Optional[str] = None
    route: Optional[str] = None
