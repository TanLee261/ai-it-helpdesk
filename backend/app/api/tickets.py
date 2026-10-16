from __future__ import annotations

import hashlib
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Ticket
from app.schemas.ticket import (
    TechnicianResponseUpdate,
    TicketCommentCreate,
    TicketCommentRead,
    TicketCreate,
    TicketListResponse,
    TicketRead,
    TicketUpdateStatus,
)
from app.security.audit import record_event
from app.security.rbac import Actor, Role, get_actor, require_roles
from app.services import ticket_service


router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db), actor: Actor = Depends(get_actor)) -> TicketRead:
    ticket = ticket_service.create_ticket(db, payload, created_by_user_id=actor.user_id)
    record_event(db, actor, "ticket.created", "ticket", ticket.ticket_id, {"title": ticket.title, "service": ticket.service})
    return _visible_ticket(ticket, actor)


@router.get("", response_model=TicketListResponse)
def list_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    service: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> TicketListResponse:
    items, total = ticket_service.list_tickets(
        db,
        status=status,
        category=category,
        service=service,
        priority=priority,
        limit=limit,
        offset=offset,
        owner_user_id=actor.user_id if actor.role == Role.EMPLOYEE else None,
    )
    return TicketListResponse(total=total, limit=limit, offset=offset, items=[_visible_ticket(item, actor) for item in items])


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: str, db: Session = Depends(get_db), actor: Actor = Depends(get_actor)) -> TicketRead:
    ticket = ticket_service.get_ticket_by_ticket_id(db, ticket_id)
    if ticket is None or (actor.role == Role.EMPLOYEE and ticket.created_by_user_id != actor.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return _visible_ticket(ticket, actor)


@router.patch("/{ticket_id}/status", response_model=TicketRead)
def update_ticket_status(
    ticket_id: str,
    payload: TicketUpdateStatus,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> TicketRead:
    ticket = ticket_service.get_ticket_by_ticket_id(db, ticket_id)
    if ticket is None or (actor.role == Role.EMPLOYEE and ticket.created_by_user_id != actor.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if actor.role == Role.EMPLOYEE:
        # Employees can confirm resolution by closing the ticket, or resume investigating if supplementary info provided
        if payload.status not in ("closed", "in_progress"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees can only close resolved tickets or resume in_progress when providing details",
            )

    old_status = ticket.status
    ticket = ticket_service.update_ticket_status(db, ticket_id, payload.status)
    record_event(
        db,
        actor,
        "ticket.status_updated",
        "ticket",
        ticket.ticket_id,
        {"old_status": old_status, "new_status": payload.status},
    )
    db.commit()
    return _visible_ticket(ticket, actor)


@router.get("/{ticket_id}/comments", response_model=list[TicketCommentRead])
def list_ticket_comments(
    ticket_id: str,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> list[TicketCommentRead]:
    ticket = ticket_service.get_ticket_by_ticket_id(db, ticket_id)
    if ticket is None or (actor.role == Role.EMPLOYEE and ticket.created_by_user_id != actor.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    comments = ticket_service.list_comments(db, ticket_id)
    return [TicketCommentRead.model_validate(c) for c in comments]


@router.post("/{ticket_id}/comments", response_model=TicketCommentRead, status_code=status.HTTP_201_CREATED)
def add_ticket_comment(
    ticket_id: str,
    payload: TicketCommentCreate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> TicketCommentRead:
    ticket = ticket_service.get_ticket_by_ticket_id(db, ticket_id)
    if ticket is None or (actor.role == Role.EMPLOYEE and ticket.created_by_user_id != actor.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    comment_type = payload.comment_type or ("supplementary_info" if actor.role == Role.EMPLOYEE else "technician_note")
    comment = ticket_service.add_comment(
        db,
        ticket_id=ticket.ticket_id,
        user_id=actor.user_id,
        user_name=actor.actor_id,
        user_role=actor.role.value,
        content=payload.content,
        comment_type=comment_type,
    )

    # If employee supplements info while waiting, move status back to in_progress
    if actor.role == Role.EMPLOYEE and ticket.status == "waiting_for_employee":
        ticket.status = "in_progress"
        db.add(ticket)

    record_event(
        db,
        actor,
        "ticket.comment_added",
        "ticket",
        ticket.ticket_id,
        {"comment_id": comment.id, "comment_type": comment_type},
    )
    db.commit()
    db.refresh(comment)
    return TicketCommentRead.model_validate(comment)


@router.patch("/{ticket_id}/response", response_model=TicketRead)
def publish_response(
    ticket_id: str,
    payload: TechnicianResponseUpdate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_roles(Role.TECHNICIAN, Role.ADMIN)),
) -> TicketRead:
    ticket = ticket_service.get_ticket_by_ticket_id(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    updated = ticket_service.publish_technician_response(db, ticket, payload.response, actor.user_id)
    # When publishing official response, transition status to resolved if not closed
    if updated.status not in ("resolved", "closed"):
        updated.status = "resolved"
    record_event(
        db,
        actor,
        "ticket.response_published",
        "ticket",
        ticket.ticket_id,
        {
            "reviewed_by": actor.actor_id,
            "response_sha256": hashlib.sha256(payload.response.strip().encode()).hexdigest(),
        },
    )
    db.commit()
    db.refresh(updated)
    return updated


def _visible_ticket(ticket: Ticket, actor: Actor) -> TicketRead:
    item = TicketRead.model_validate(ticket)
    if actor.role == Role.EMPLOYEE:
        return item.model_copy(update={"verified_root_cause": None, "resolution": None, "assigned_team": None})
    return item

