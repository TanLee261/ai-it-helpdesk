from __future__ import annotations

from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Ticket
from app.db.session import get_db
from app.security.rbac import Actor, Role, get_actor
from app.main import app


engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_ticket(db: Session) -> None:
    db.add(
        Ticket(
            ticket_id="TCK-00001",
            source_ticket_id="seed-source",
            title="VPN cannot connect",
            description="User cannot connect to VPN from home network",
            service="vpn-gateway",
            category="network",
            raw_category="Network",
            sub_category="VPN Issue",
            priority="p2",
            impact="medium",
            urgency="high",
            assigned_team="Network Support",
            auto_resolve=False,
            status="new",
            requester_email_redacted="redacted",
            source="test",
        )
    )
    db.commit()


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        seed_ticket(db)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_actor] = lambda: Actor("test-tech", Role.TECHNICIAN, 1)


def teardown_function() -> None:
    app.dependency_overrides.clear()


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_prometheus_metrics_endpoint() -> None:
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "helpdesk_http_requests_total" in response.text
    assert 'route="/health"' in response.text


def test_list_tickets() -> None:
    response = client.get("/api/tickets")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["ticket_id"] == "TCK-00001"


def test_get_ticket_detail() -> None:
    response = client.get("/api/tickets/TCK-00001")
    assert response.status_code == 200
    assert response.json()["service"] == "vpn-gateway"


def test_create_ticket() -> None:
    response = client.post(
        "/api/tickets",
        json={
            "title": "Payment API returns 500",
            "description": "Checkout fails with HTTP 500 for several users",
            "service": "payment-api",
            "category": "server_api",
            "priority": "p2",
            "impact": "high",
            "urgency": "high",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["ticket_id"] == "TCK-00002"
    assert body["status"] == "new"


def test_update_ticket_status() -> None:
    response = client.patch("/api/tickets/TCK-00001/status", json={"status": "in_progress"})
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
