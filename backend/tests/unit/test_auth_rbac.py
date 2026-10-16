from __future__ import annotations

from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Ticket, User
from app.db.session import get_db
from app.main import app
from app.security.passwords import hash_password


engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine)
client = TestClient(app)


def override_get_db() -> Generator[Session, None, None]:
    with TestingSessionLocal() as db:
        yield db


def setup_function() -> None:
    client.cookies.clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestingSessionLocal() as db:
        db.add_all([
            User(id=1, username="admin", email="admin@example.com", full_name="Admin", role="admin", password_hash=hash_password("AdminStart12345"), is_active=True, must_change_password=False),
            User(id=2, username="tech", email="tech@example.com", full_name="Tech User", role="technician", password_hash=hash_password("TempTech12345"), is_active=True, must_change_password=True),
            User(id=3, username="alice", email="alice@example.com", full_name="Alice Employee", role="employee", password_hash=hash_password("TempAlice12345"), is_active=True, must_change_password=True),
            User(id=4, username="bob", email="bob@example.com", full_name="Bob Employee", role="employee", password_hash=hash_password("TempBob12345"), is_active=True, must_change_password=False),
            Ticket(ticket_id="TCK-OLD", title="Old ticket", description="Existing seeded historical record", service="mail", category="other", priority="p3", impact="low", urgency="low", status="new", auto_resolve=False, verified_root_cause="internal cause", resolution="internal resolution"),
        ])
        db.commit()


def teardown_function() -> None:
    app.dependency_overrides.clear()
    client.cookies.clear()


def login(username: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    assert "helpdesk_session" in client.cookies
    return response.json()["user"]


def test_authentication_ignores_forged_role_headers_and_requires_session() -> None:
    unauthenticated = client.get("/api/tickets", headers={"X-Actor-Id": "attacker", "X-Actor-Role": "admin"})
    assert unauthenticated.status_code == 401
    login("alice", "TempAlice12345")
    assert client.get("/api/users", headers={"X-Actor-Role": "admin"}).status_code == 403
    assert client.post("/api/ai/retrieve", headers={"X-Actor-Role": "technician"}, json={}).status_code == 403


def test_first_login_requires_password_change_before_access() -> None:
    user = login("alice", "TempAlice12345")
    assert user["must_change_password"] is True
    assert client.get("/api/tickets").status_code == 403
    changed = client.post("/api/auth/change-password", json={"current_password": "TempAlice12345", "new_password": "AliceSecure45678"})
    assert changed.status_code == 200 and changed.json()["must_change_password"] is False
    assert client.get("/api/tickets").status_code == 200


def test_employee_can_only_see_own_tickets_and_public_fields() -> None:
    login("alice", "TempAlice12345")
    assert client.post("/api/auth/change-password", json={"current_password": "TempAlice12345", "new_password": "AliceSecure45678"}).status_code == 200
    created = client.post("/api/tickets", json={"title": "VPN failure", "description": "My VPN disconnects", "service": "vpn", "category": "network", "priority": "p2", "impact": "medium", "urgency": "high"})
    assert created.status_code == 201
    own_id = created.json()["ticket_id"]
    assert created.json()["verified_root_cause"] is None and created.json()["resolution"] is None
    with TestingSessionLocal() as db:
        bob = db.get(User, 4)
        db.add(Ticket(ticket_id="TCK-BOB", title="Bob ticket", description="Private to Bob", service="mail", category="other", priority="p3", impact="low", urgency="low", status="new", auto_resolve=False, created_by_user_id=bob.id))
        db.commit()
    own_list = client.get("/api/tickets").json()
    assert {row["ticket_id"] for row in own_list["items"]} == {own_id}
    assert client.get("/api/tickets/TCK-BOB").status_code == 404
    assert client.get("/api/tickets/TCK-OLD").status_code == 404
    # Employee cannot set technician-only statuses
    assert client.patch(f"/api/tickets/{own_id}/status", json={"status": "resolved"}).status_code == 403
    # Employee cannot modify another user's ticket status
    assert client.patch("/api/tickets/TCK-BOB/status", json={"status": "closed"}).status_code == 404
    # Employee can add supplementary information to own ticket
    comment_resp = client.post(f"/api/tickets/{own_id}/comments", json={"content": "Added screenshots of the disconnection prompt."})
    assert comment_resp.status_code == 201
    assert comment_resp.json()["content"] == "Added screenshots of the disconnection prompt."
    # Employee cannot comment on other user's ticket
    assert client.post("/api/tickets/TCK-BOB/comments", json={"content": "Forbidden note"}).status_code == 404
    # Employee can confirm resolution by closing own ticket
    assert client.patch(f"/api/tickets/{own_id}/status", json={"status": "closed"}).status_code == 200
    assert client.get(f"/api/tickets/{own_id}").json()["status"] == "closed"


def test_admin_creates_technicians_technician_creates_employees_and_reviewed_reply_is_owner_visible() -> None:
    login("admin", "AdminStart12345")
    created_tech = client.post("/api/users", json={"username": "tech-two", "email": "tech2@example.com", "full_name": "Second Tech", "role": "technician"})
    assert created_tech.status_code == 201 and created_tech.json()["temporary_password"]
    client.cookies.clear()
    login("tech", "TempTech12345")
    assert client.get("/api/users").status_code == 403
    assert client.post("/api/auth/change-password", json={"current_password": "TempTech12345", "new_password": "TechSecure45678"}).status_code == 200
    assert client.post("/api/users", json={"username": "tech-three", "email": "tech3@example.com", "full_name": "Third Tech", "role": "technician"}).status_code == 403
    employee = client.post("/api/users", json={"username": "carol", "email": "carol@example.com", "full_name": "Carol Employee", "role": "employee"})
    assert employee.status_code == 201
    temp_password = employee.json()["temporary_password"]
    client.cookies.clear()
    login("carol", temp_password)
    assert client.post("/api/auth/change-password", json={"current_password": temp_password, "new_password": "CarolSecure45678"}).status_code == 200
    ticket = client.post("/api/tickets", json={"title": "Email outage", "description": "Cannot send email", "service": "mail", "category": "other", "priority": "p2", "impact": "high", "urgency": "high"}).json()
    ticket_id = ticket["ticket_id"]
    client.cookies.clear()
    login("tech", "TechSecure45678")
    response = client.patch(f"/api/tickets/{ticket_id}/response", json={"response": "We reviewed the available evidence. Email delivery is restored; continue monitoring."})
    assert response.status_code == 200 and response.json()["response_sent_at"]
    client.cookies.clear()
    login("carol", "CarolSecure45678")
    visible = client.get(f"/api/tickets/{ticket_id}").json()
    assert "reviewed the available evidence" in visible["technician_response"]
    assert visible["response_sent_at"] is not None


def test_logout_revokes_session() -> None:
    login("admin", "AdminStart12345")
    assert client.post("/api/auth/logout").status_code == 204
    client.cookies.clear()
    assert client.get("/api/auth/me").status_code == 401


def test_account_lockout_after_consecutive_failed_logins() -> None:
    for i in range(4):
        resp = client.post("/api/auth/login", json={"username": "bob", "password": "WrongPassword!"})
        assert resp.status_code == 401
    # 5th attempt locks the account
    resp5 = client.post("/api/auth/login", json={"username": "bob", "password": "WrongPassword!"})
    assert resp5.status_code == 401
    # 6th attempt is rejected with 403 Forbidden even with correct password
    resp6 = client.post("/api/auth/login", json={"username": "bob", "password": "TempBob12345"})
    assert resp6.status_code == 403
    assert "locked" in resp6.json()["detail"].lower()


def test_password_reset_and_role_boundaries() -> None:
    login("tech", "TempTech12345")
    client.post("/api/auth/change-password", json={"current_password": "TempTech12345", "new_password": "TechSecure45678"})

    # Technician cannot reset Admin password
    assert client.post("/api/users/1/reset-password").status_code == 403
    # Technician cannot reset other Technician password
    assert client.post("/api/users/2/reset-password").status_code == 403
    # Technician CAN reset Employee password (user 3 - alice)
    reset_resp = client.post("/api/users/3/reset-password")
    assert reset_resp.status_code == 200
    new_temp_pw = reset_resp.json()["temporary_password"]
    assert new_temp_pw
    assert reset_resp.json()["user"]["must_change_password"] is True

    # Old password no longer works
    client.cookies.clear()
    assert client.post("/api/auth/login", json={"username": "alice", "password": "TempAlice12345"}).status_code == 401
    # New temp password works and requires password change
    login("alice", new_temp_pw)
    assert client.get("/api/tickets").status_code == 403
    assert client.post("/api/auth/change-password", json={"current_password": new_temp_pw, "new_password": "AliceBrandNew123"}).status_code == 200
    assert client.get("/api/tickets").status_code == 200

