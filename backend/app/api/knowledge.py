from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.knowledge import (
    KnowledgeChunkRead,
    KnowledgeDocumentDetail,
    KnowledgeDocumentListResponse,
    KnowledgeIngestRequest,
    KnowledgeIngestResponse,
)
from app.services import knowledge_service
from app.ingestion.enricher import IngestDocument
from app.ingestion.pipeline import ingest_documents
from app.security.rbac import Role, require_roles


router = APIRouter(prefix="/knowledge", tags=["knowledge"], dependencies=[Depends(require_roles(Role.TECHNICIAN, Role.ADMIN))])


@router.post("/ingest", response_model=KnowledgeIngestResponse)
def ingest_knowledge(payload: KnowledgeIngestRequest, db: Session = Depends(get_db)) -> KnowledgeIngestResponse:
    result = ingest_documents(
        db,
        [IngestDocument(
            document_id=payload.document_id,
            title=payload.title,
            source_type=payload.source_type,
            source=payload.source,
            content=payload.content,
            service=payload.service,
            category=payload.category,
            version=payload.version,
            access_scope=payload.access_scope,
        )],
    )
    return KnowledgeIngestResponse(
        document_id=payload.document_id,
        documents_upserted=result.documents_upserted,
        chunks_upserted=result.chunks_upserted,
    )


@router.get("/documents", response_model=KnowledgeDocumentListResponse)
def list_knowledge_documents(
    source_type: Optional[str] = None,
    service: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> KnowledgeDocumentListResponse:
    items, total = knowledge_service.list_documents(
        db,
        source_type=source_type,
        service=service,
        category=category,
        limit=limit,
        offset=offset,
    )
    return KnowledgeDocumentListResponse(total=total, limit=limit, offset=offset, items=items)


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentDetail)
def get_knowledge_document(document_id: str, db: Session = Depends(get_db)) -> KnowledgeDocumentDetail:
    document = knowledge_service.get_document_by_document_id(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge document not found")
    chunks = knowledge_service.list_chunks_for_document(db, document_id)
    return KnowledgeDocumentDetail.model_validate(document).model_copy(update={"chunks": chunks})


@router.get("/chunks/{chunk_id}", response_model=KnowledgeChunkRead)
def get_knowledge_chunk(chunk_id: str, db: Session = Depends(get_db)) -> KnowledgeChunkRead:
    chunk = knowledge_service.get_chunk_by_chunk_id(db, chunk_id)
    if chunk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge chunk not found")
    return chunk
