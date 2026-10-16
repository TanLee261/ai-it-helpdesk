from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditEvent
from app.ingestion.cleaner import clean_text
from app.security.rbac import Actor


def record_event(
    db: Session,
    actor: Actor,
    action: str,
    resource_type: str,
    resource_id: str,
    metadata: dict | None = None,
) -> AuditEvent:
    safe_metadata = {
        clean_text(str(key))[:80]: clean_text(str(value))[:500]
        for key, value in (metadata or {}).items()
    }
    event = AuditEvent(
        event_id=f"AUD-{uuid4().hex}",
        actor_id=clean_text(actor.actor_id)[:120],
        actor_role=actor.role.value,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=safe_metadata,
    )
    db.add(event)
    db.flush()
    return event


def list_events(db: Session, limit: int = 100) -> list[AuditEvent]:
    query = select(AuditEvent).order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).limit(limit)
    return list(db.scalars(query))
