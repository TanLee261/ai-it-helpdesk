from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import KnowledgeChunk, KnowledgeDocument


def list_documents(
    db: Session,
    source_type: Optional[str] = None,
    service: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[KnowledgeDocument], int]:
    query = db.query(KnowledgeDocument)
    if source_type:
        query = query.filter(KnowledgeDocument.source_type == source_type)
    if service:
        query = query.filter(KnowledgeDocument.service == service)
    if category:
        query = query.filter(KnowledgeDocument.category == category)
    total = query.count()
    items = (
        query.order_by(KnowledgeDocument.document_id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def get_document_by_document_id(db: Session, document_id: str) -> Optional[KnowledgeDocument]:
    return (
        db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.document_id == document_id)
        .one_or_none()
    )


def list_chunks_for_document(db: Session, document_id: str) -> list[KnowledgeChunk]:
    return (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.document_id == document_id)
        .order_by(KnowledgeChunk.chunk_index.asc())
        .all()
    )


def get_chunk_by_chunk_id(db: Session, chunk_id: str) -> Optional[KnowledgeChunk]:
    return db.query(KnowledgeChunk).filter(KnowledgeChunk.chunk_id == chunk_id).one_or_none()
