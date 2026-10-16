from __future__ import annotations

import re
from typing import Optional

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.db.models import Ticket, TicketComment, utc_now
from app.schemas.ticket import TicketCreate


def _next_ticket_id(db: Session) -> str:
    ticket_ids = db.scalars(select(Ticket.ticket_id).where(Ticket.ticket_id.like("TCK-%"))).all()
    max_number = 0
    for ticket_id in ticket_ids:
        match = re.fullmatch(r"TCK-(\d+)", ticket_id)
        if match:
            max_number = max(max_number, int(match.group(1)))
    return f"TCK-{max_number + 1:05d}"


def create_ticket(db: Session, payload: TicketCreate, created_by_user_id: int | None = None) -> Ticket:
    ticket = Ticket(
        ticket_id=_next_ticket_id(db),
        title=payload.title,
        description=payload.description,
        service=payload.service,
        category=payload.category,
        raw_category=payload.raw_category,
        sub_category=payload.sub_category,
        priority=payload.priority,
        impact=payload.impact,
        urgency=payload.urgency,
        assigned_team=payload.assigned_team,
        auto_resolve=False,
        status="new",
        source="api",
        created_by_user_id=created_by_user_id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def _filtered_ticket_query(
    *,
    status: Optional[str] = None,
    category: Optional[str] = None,
    service: Optional[str] = None,
    priority: Optional[str] = None,
) -> Select[tuple[Ticket]]:
    query = select(Ticket)
    if status:
        query = query.where(Ticket.status == status)
    if category:
        query = query.where(Ticket.category == category)
    if service:
        query = query.where(Ticket.service == service)
    if priority:
        query = query.where(Ticket.priority == priority)
    return query


def list_tickets(
    db: Session,
    *,
    status: Optional[str] = None,
    category: Optional[str] = None,
    service: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    owner_user_id: int | None = None,
) -> tuple[list[Ticket], int]:
    base_query = _filtered_ticket_query(status=status, category=category, service=service, priority=priority)
    if owner_user_id is not None:
        base_query = base_query.where(Ticket.created_by_user_id == owner_user_id)
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    items = db.scalars(base_query.order_by(Ticket.created_at.desc(), Ticket.id.desc()).limit(limit).offset(offset)).all()
    return list(items), total


def get_ticket_by_ticket_id(db: Session, ticket_id: str) -> Optional[Ticket]:
    return db.scalar(select(Ticket).where(Ticket.ticket_id == ticket_id))


def update_ticket_status(db: Session, ticket_id: str, status: str) -> Optional[Ticket]:
    ticket = get_ticket_by_ticket_id(db, ticket_id)
    if ticket is None:
        return None
    ticket.status = status
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def publish_technician_response(db: Session, ticket: Ticket, response: str, technician_user_id: int) -> Ticket:
    ticket.technician_response = response.strip()
    ticket.response_sent_at = utc_now()
    ticket.response_reviewed_by_user_id = technician_user_id
    ticket.updated_at = utc_now()
    db.flush()
    return ticket


def list_comments(db: Session, ticket_id: str) -> list[TicketComment]:
    return list(db.scalars(select(TicketComment).where(TicketComment.ticket_id == ticket_id).order_by(TicketComment.created_at.asc())))


def add_comment(
    db: Session,
    *,
    ticket_id: str,
    user_id: int,
    user_name: str,
    user_role: str,
    content: str,
    comment_type: str = "comment",
) -> TicketComment:
    comment = TicketComment(
        ticket_id=ticket_id,
        user_id=user_id,
        user_name=user_name,
        user_role=user_role,
        comment_type=comment_type,
        content=content.strip(),
    )
    db.add(comment)
    db.flush()
    return comment

