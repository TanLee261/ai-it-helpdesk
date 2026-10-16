from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ApprovalRequest, Ticket, utc_now
from app.db.session import get_db
from app.schemas.approval import ApprovalCreate, ApprovalDecision, ApprovalRead, AuditEventRead
from app.security.approval_policy import validate_advisory_action
from app.security.audit import list_events, record_event
from app.security.rbac import Actor, Role, require_roles
from app.security.redaction import redact_for_audit


router = APIRouter(prefix="/approvals", tags=["approvals-and-audit"])


@router.post("", response_model=ApprovalRead, status_code=status.HTTP_201_CREATED)
def create_approval(
    payload: ApprovalCreate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_roles(Role.TECHNICIAN, Role.ADMIN)),
) -> ApprovalRequest:
    try:
        validate_advisory_action(payload.action, payload.rationale)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if db.scalar(select(Ticket.id).where(Ticket.ticket_id == payload.ticket_id)) is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    approval = ApprovalRequest(
        approval_id=f"APR-{uuid4().hex[:12].upper()}", ticket_id=payload.ticket_id,
        action=redact_for_audit(payload.action), rationale=redact_for_audit(payload.rationale),
        requested_by=actor.actor_id, status="pending",
    )
    db.add(approval)
    db.flush()
    record_event(db, actor, "approval.requested", "approval", approval.approval_id, {"ticket_id": approval.ticket_id})
    db.commit()
    db.refresh(approval)
    return approval


@router.get("", response_model=list[ApprovalRead])
def get_approvals(
    approval_status: str | None = Query(default=None, alias="status", pattern="^(pending|approved|rejected)$"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_roles(Role.TECHNICIAN, Role.ADMIN)),
) -> list[ApprovalRequest]:
    query = select(ApprovalRequest).order_by(ApprovalRequest.created_at.desc()).limit(limit)
    if approval_status:
        query = query.where(ApprovalRequest.status == approval_status)
    return list(db.scalars(query))


@router.post("/{approval_id}/decision", response_model=ApprovalRead)
def decide_approval(
    approval_id: str,
    payload: ApprovalDecision,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_roles(Role.TECHNICIAN, Role.ADMIN)),
) -> ApprovalRequest:
    approval = db.scalar(
        select(ApprovalRequest).where(ApprovalRequest.approval_id == approval_id).with_for_update()
    )
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail="Approval request has already been decided")
    if approval.requested_by == actor.actor_id:
        raise HTTPException(status_code=403, detail="Requester cannot approve or reject their own request")
    approval.status = payload.decision
    approval.decided_by = actor.actor_id
    approval.decision_note = redact_for_audit(payload.note)
    approval.decided_at = utc_now()
    record_event(
        db, actor, f"approval.{payload.decision}", "approval", approval.approval_id,
        {"ticket_id": approval.ticket_id, "requested_by": approval.requested_by},
    )
    db.commit()
    db.refresh(approval)
    return approval


@router.get("/audit", response_model=list[AuditEventRead])
def get_audit_events(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_roles(Role.ADMIN)),
) -> list[AuditEventRead]:
    return list_events(db, limit=limit)
