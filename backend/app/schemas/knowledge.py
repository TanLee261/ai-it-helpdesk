from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class KnowledgeIngestRequest(BaseModel):
    document_id: str = Field(min_length=3, max_length=80)
    title: str = Field(min_length=3, max_length=255)
    source_type: Literal["runbook", "historical_ticket", "log"]
    source: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1, max_length=100_000)
    service: Optional[str] = Field(default=None, max_length=80)
    category: Optional[str] = Field(default=None, max_length=40)
    version: Optional[str] = Field(default="v1", max_length=40)
    access_scope: str = Field(default="it_internal", min_length=1, max_length=80)

    @field_validator("document_id")
    @classmethod
    def validate_document_id(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{2,79}", value):
            raise ValueError("document_id may contain only letters, numbers, hyphens, and underscores")
        return value

    @field_validator("access_scope")
    @classmethod
    def validate_access_scope(cls, value: str) -> str:
        if value != "it_internal":
            raise ValueError("Uploads are restricted to the it_internal scope")
        return value


class KnowledgeIngestResponse(BaseModel):
    document_id: str
    documents_upserted: int
    chunks_upserted: int


class KnowledgeDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: str
    title: str
    source_type: str
    source: str
    service: Optional[str]
    category: Optional[str]
    version: Optional[str]
    access_scope: str
    content_hash: str
    created_at: datetime
    updated_at: datetime


class KnowledgeChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    metadata_json: dict[str, Any]
    token_count: int
    qdrant_point_id: Optional[str]
    created_at: datetime


class KnowledgeDocumentListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[KnowledgeDocumentRead]


class KnowledgeDocumentDetail(KnowledgeDocumentRead):
    chunks: list[KnowledgeChunkRead] = Field(default_factory=list)
