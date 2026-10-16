from __future__ import annotations

from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.security.rbac import Actor, Role, get_actor
from app.ingestion.enricher import IngestDocument
from app.ingestion.pipeline import ingest_documents
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


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_actor] = lambda: Actor("test-tech", Role.TECHNICIAN, 1)
    with TestingSessionLocal() as db:
        ingest_documents(
            db,
            [
                IngestDocument(
                    document_id="RB-TEST-001",
                    title="Kiem tra VPN timeout",
                    source_type="runbook",
                    source="test",
                    service="vpn-gateway",
                    category="network",
                    version="v1",
                    access_scope="it_internal",
                    content=(
                        "# Kiem tra VPN timeout\n\n"
                        "## Metadata\n\nservice: vpn-gateway\n\n"
                        "## Verification Steps\n\n"
                        "1. Check VPN gateway logs.\n"
                        "2. Check DNS and routing.\n"
                    ),
                )
            ],
        )


def teardown_function() -> None:
    app.dependency_overrides.clear()


client = TestClient(app)


def test_list_knowledge_documents() -> None:
    response = client.get("/api/knowledge/documents")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["document_id"] == "RB-TEST-001"


def test_get_knowledge_document_detail() -> None:
    response = client.get("/api/knowledge/documents/RB-TEST-001")
    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == "RB-TEST-001"
    assert body["chunks"][0]["chunk_id"] == "RB-TEST-001-C001"


def test_get_knowledge_chunk() -> None:
    response = client.get("/api/knowledge/chunks/RB-TEST-001-C001")
    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == "RB-TEST-001"
    assert "VPN" in body["content"]


def test_ingest_uploaded_text_redacts_secrets_and_persists_chunks() -> None:
    response = client.post(
        "/api/knowledge/ingest",
        json={
            "document_id": "RB-UPLOAD-001",
            "title": "Uploaded runbook",
            "source_type": "runbook",
            "source": "uploaded.md",
            "service": "vpn-gateway",
            "category": "network",
            "content": "# VPN response\n\n## Steps\n\nCheck API_KEY=sample-secret and vpn-gateway status.",
        },
    )
    assert response.status_code == 200
    assert response.json()["chunks_upserted"] == 1
    chunk = client.get("/api/knowledge/chunks/RB-UPLOAD-001-C001").json()
    assert "[REDACTED_SECRET]" in chunk["content"]
    assert "sample-secret" not in chunk["content"]


def test_ingest_rejects_path_like_document_id() -> None:
    response = client.post(
        "/api/knowledge/ingest",
        json={
            "document_id": "../private",
            "title": "Invalid document id",
            "source_type": "runbook",
            "source": "file.md",
            "content": "# Example",
        },
    )
    assert response.status_code == 422


def test_vite_origin_is_allowed_by_cors() -> None:
    response = client.options(
        "/api/tickets",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
