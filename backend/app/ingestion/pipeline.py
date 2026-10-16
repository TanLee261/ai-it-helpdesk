from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import KnowledgeChunk, KnowledgeDocument, utc_now
from app.ingestion.chunker import chunk_markdown_by_heading, chunk_ticket_text
from app.ingestion.cleaner import clean_text
from app.ingestion.enricher import IngestDocument, content_hash, enrich_chunks
from app.ingestion.loaders.csv_ticket import load_ticket_documents
from app.ingestion.loaders.markdown_sop import load_runbook_documents


@dataclass(frozen=True)
class IngestionResult:
    documents_seen: int
    documents_upserted: int
    chunks_upserted: int


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_ticket_path() -> Path:
    return project_root() / "data" / "processed" / "tickets" / "normalized_tickets.csv"


def default_runbook_dir() -> Path:
    return project_root() / "data" / "processed" / "runbooks"


def chunk_document(document: IngestDocument) -> list[KnowledgeChunk]:
    clean_content = clean_text(document.content)
    clean_document = IngestDocument(
        document_id=document.document_id,
        title=document.title,
        source_type=document.source_type,
        source=document.source,
        content=clean_content,
        service=document.service,
        category=document.category,
        version=document.version,
        access_scope=document.access_scope,
        metadata=document.metadata,
    )
    if document.source_type == "historical_ticket":
        text_chunks = chunk_ticket_text(clean_content)
    else:
        text_chunks = chunk_markdown_by_heading(clean_content)

    return [
        KnowledgeChunk(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            metadata_json=chunk.metadata,
            token_count=chunk.token_count,
        )
        for chunk in enrich_chunks(clean_document, text_chunks)
    ]


def upsert_document(db: Session, document: IngestDocument) -> int:
    clean_content = clean_text(document.content)
    now = utc_now()
    existing = (
        db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.document_id == document.document_id)
        .one_or_none()
    )
    if existing is None:
        existing = KnowledgeDocument(
            document_id=document.document_id,
            title=document.title,
            source_type=document.source_type,
            source=document.source,
            service=document.service,
            category=document.category,
            version=document.version,
            access_scope=document.access_scope,
            content_hash=content_hash(clean_content),
            created_at=now,
            updated_at=now,
        )
        db.add(existing)
    else:
        existing.title = document.title
        existing.source_type = document.source_type
        existing.source = document.source
        existing.service = document.service
        existing.category = document.category
        existing.version = document.version
        existing.access_scope = document.access_scope
        existing.content_hash = content_hash(clean_content)
        existing.updated_at = now

    db.flush()
    db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document.document_id).delete()
    chunks = chunk_document(document)
    db.add_all(chunks)
    return len(chunks)


def ingest_documents(db: Session, documents: list[IngestDocument]) -> IngestionResult:
    chunks_upserted = 0
    for document in documents:
        chunks_upserted += upsert_document(db, document)
    db.commit()
    return IngestionResult(
        documents_seen=len(documents),
        documents_upserted=len(documents),
        chunks_upserted=chunks_upserted,
    )


def ingest_tickets(db: Session, path: Optional[Path] = None, limit: Optional[int] = None) -> IngestionResult:
    documents = load_ticket_documents(path or default_ticket_path(), limit=limit)
    return ingest_documents(db, documents)


def ingest_runbooks(db: Session, directory: Optional[Path] = None) -> IngestionResult:
    documents = load_runbook_documents(directory or default_runbook_dir())
    return ingest_documents(db, documents)


def ingest_all(db: Session, ticket_limit: Optional[int] = None) -> IngestionResult:
    runbook_result = ingest_runbooks(db)
    ticket_result = ingest_tickets(db, limit=ticket_limit)
    return IngestionResult(
        documents_seen=runbook_result.documents_seen + ticket_result.documents_seen,
        documents_upserted=runbook_result.documents_upserted + ticket_result.documents_upserted,
        chunks_upserted=runbook_result.chunks_upserted + ticket_result.chunks_upserted,
    )
