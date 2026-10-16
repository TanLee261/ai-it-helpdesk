from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.services.retrieval_service import retrieve_evidence
from app.security.rbac import Role, require_roles


router = APIRouter(prefix="/ai", tags=["ai-retrieval"])


@router.post("/retrieve", response_model=RetrievalResponse)
def retrieve(payload: RetrievalRequest, db: Session = Depends(get_db), _actor=Depends(require_roles(Role.TECHNICIAN, Role.ADMIN))) -> RetrievalResponse:
    return retrieve_evidence(db, payload)
