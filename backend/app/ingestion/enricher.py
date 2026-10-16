from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Optional

from app.ingestion.chunker import TextChunk


@dataclass(frozen=True)
class IngestDocument:
    document_id: str
    title: str
    source_type: str
    source: str
    content: str
    service: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    access_scope: str = "it_internal"
    metadata: Optional[dict[str, Any]] = None


@dataclass(frozen=True)
class EnrichedChunk:
    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    token_count: int
    metadata: dict[str, Any]


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def enrich_chunks(document: IngestDocument, chunks: list[TextChunk]) -> list[EnrichedChunk]:
    base_metadata = {
        "document_id": document.document_id,
        "title": document.title,
        "source_type": document.source_type,
        "source": document.source,
        "service": document.service,
        "category": document.category,
        "version": document.version,
        "access_scope": document.access_scope,
    }
    if document.metadata:
        base_metadata.update(document.metadata)

    enriched: list[EnrichedChunk] = []
    for chunk in chunks:
        chunk_id = f"{document.document_id}-C{chunk.chunk_index:03d}"
        metadata = dict(base_metadata)
        metadata["chunk_id"] = chunk_id
        metadata["chunk_index"] = chunk.chunk_index
        enriched.append(
            EnrichedChunk(
                chunk_id=chunk_id,
                document_id=document.document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                token_count=chunk.token_count,
                metadata=metadata,
            )
        )
    return enriched
