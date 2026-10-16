from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import ApprovalRequest, AuditEvent, Ticket
from app.db.session import get_db
from app.main import app
from app.security.rbac import Actor, Role, get_actor


engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine)
client = TestClient(app)


def override_get_db() -> Generator[Session, None, None]:
    with TestingSessionLocal() as db:
        yield db


def override_actor(request: Request) -> Actor:
    return Actor(request.headers.get("X-Actor-Id", "tech-1"), Role(request.headers.get("X-Actor-Role", "technician")), 1)


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_actor] = override_actor
    with TestingSessionLocal() as db:
        db.add(Ticket(ticket_id="TCK-A1", title="Test ticket", description="Test description", service="test-service", category="other", priority="p3", impact="low", urgency="low", status="new", auto_resolve=False))
        db.commit()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_approval_request_requires_technician_and_prevents_employee() -> None:
    payload = {"ticket_id": "TCK-A1", "action": "Restart service", "rationale": "Technician recommends restart"}
    assert client.post("/api/approvals", json=payload, headers={"X-Actor-Role": "employee"}).status_code == 403
    created = client.post("/api/approvals", json=payload, headers={"X-Actor-Id": "tech-1", "X-Actor-Role": "technician"})
    assert created.status_code == 201
    approval_id = created.json()["approval_id"]
    assert client.get("/api/approvals", headers={"X-Actor-Role": "employee"}).status_code == 403
    assert client.post(f"/api/approvals/{approval_id}/decision", json={"decision": "approved", "note": "Looks good"}, headers={"X-Actor-Id": "tech-1", "X-Actor-Role": "technician"}).status_code == 403


def test_approval_audit_and_no_self_approval() -> None:
    created = client.post("/api/approvals", json={"ticket_id": "TCK-A1", "action": "Restart service", "rationale": "Incident requires review"}, headers={"X-Actor-Id": "tech-1", "X-Actor-Role": "technician"})
    approval_id = created.json()["approval_id"]
    decision = {"decision": "approved", "note": "Reviewed; advisory only"}
    assert client.post(f"/api/approvals/{approval_id}/decision", json=decision, headers={"X-Actor-Id": "tech-1", "X-Actor-Role": "technician"}).status_code == 403
    approved = client.post(f"/api/approvals/{approval_id}/decision", json=decision, headers={"X-Actor-Id": "admin-1", "X-Actor-Role": "admin"})
    assert approved.status_code == 200 and approved.json()["status"] == "approved"
    assert client.post(f"/api/approvals/{approval_id}/decision", json=decision, headers={"X-Actor-Id": "admin-2", "X-Actor-Role": "admin"}).status_code == 409
    assert client.get("/api/approvals/audit", headers={"X-Actor-Role": "technician"}).status_code == 403
    audit = client.get("/api/approvals/audit", headers={"X-Actor-Id": "admin-1", "X-Actor-Role": "admin"})
    assert audit.status_code == 200
    assert [row["action"] for row in audit.json()] == ["approval.approved", "approval.requested"]
    with TestingSessionLocal() as db:
        assert len(list(db.scalars(select(AuditEvent)))) == 2


def test_approval_text_is_redacted_and_does_not_execute() -> None:
    created = client.post("/api/approvals", json={"ticket_id": "TCK-A1", "action": "Check config token=abc123", "rationale": "Contact alice@example.com"}, headers={"X-Actor-Id": "tech-1", "X-Actor-Role": "technician"})
    assert created.status_code == 201
    body = created.json()
    assert "abc123" not in body["action"] and "alice@example.com" not in body["rationale"]
    assert body["status"] == "pending"
