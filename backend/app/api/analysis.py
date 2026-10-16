from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analysis.schema import AnalysisRequest, AnalysisResponse
from app.analysis.service import analyze_incident
from app.db.session import get_db
from app.security.rbac import Role, require_roles


router = APIRouter(prefix="/ai", tags=["ai-analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
def analyze(payload: AnalysisRequest, db: Session = Depends(get_db), _actor=Depends(require_roles(Role.TECHNICIAN, Role.ADMIN))) -> AnalysisResponse:
    return analyze_incident(db, payload)
