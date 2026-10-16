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
        db.add(
            Ticket(
                ticket_id="TCK-00001",
                title="Payment API returns HTTP 500",
                description="Checkout fails when payment-api connection pool is exhausted",
                service="payment-api",
                category="server_api",
                priority="p2",
                impact="high",
                urgency="high",
                status="new",
                auto_resolve=False,
            )
        )
        ingest_documents(
            db,
            [
                IngestDocument(
                    document_id="RB-API-001",
                    title="Kiem tra HTTP 500 tren payment-api",
                    source_type="runbook",
                    source="test",
                    service="payment-api",
                    category="server_api",
                    version="v1",
                    access_scope="it_internal",
                    content=(
                        "# Kiem tra HTTP 500 tren payment-api\n\n"
                        "## Verification Steps\n\n"
                        "Check payment-api error logs, latency, and database connection pool."
                    ),
                ),
                IngestDocument(
                    document_id="RB-NET-001",
                    title="Kiem tra VPN timeout",
                    source_type="runbook",
                    source="test",
                    service="vpn-gateway",
                    category="network",
                    version="v1",
                    access_scope="it_internal",
                    content="Check vpn gateway route and dns.",
                ),
                IngestDocument(
                    document_id="RB-API-002",
                    title="Payment API version two",
                    source_type="runbook",
                    source="test",
                    service="payment-api",
                    category="server_api",
                    version="v2",
                    access_scope="it_internal",
                    content="Check payment-api HTTP 500 connection pool after upgrade.",
                ),
            ],
        )


def teardown_function() -> None:
    app.dependency_overrides.clear()


client = TestClient(app)


def test_retrieve_by_query_with_service_filter() -> None:
    response = client.post(
        "/api/ai/retrieve",
        json={
            "query": "payment api http 500 connection pool",
            "service": "payment-api",
            "version": "v1",
            "source_types": ["runbook"],
            "top_k": 5,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["retrieval_method"] == "bm25"
    assert [item["document_id"] for item in body["results"]] == ["RB-API-001"]


def test_retrieve_by_ticket_id_builds_query_and_filters() -> None:
    response = client.post("/api/ai/retrieve", json={"ticket_id": "TCK-00001", "top_k": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["filters"]["service"] == "payment-api"
    assert "RB-API-001" in [item["document_id"] for item in body["results"]]


def test_bm25_filters_by_version() -> None:
    response = client.post(
        "/api/ai/retrieve",
        json={"query": "payment api http 500", "service": "payment-api", "version": "v2", "top_k": 5},
    )
    assert response.status_code == 200
    assert [item["document_id"] for item in response.json()["results"]] == ["RB-API-002"]


def test_retrieve_dense_method_uses_dense_retriever(monkeypatch) -> None:
    class FakeDenseRetriever:
        def search(self, query: str, **kwargs):
            from app.stores.qdrant_store import VectorSearchResult

            return [
                VectorSearchResult(
                    rank=1,
                    score=0.9,
                    chunk_id="RB-API-001-C001",
                    document_id="RB-API-001",
                    content="Dense result",
                    metadata={"chunk_id": "RB-API-001-C001"},
                    source_type="runbook",
                    source="test",
                    service=kwargs["service"],
                    category=kwargs["category"],
                    access_scope=kwargs["access_scope"],
                )
            ]

    monkeypatch.setattr("app.services.retrieval_service.DenseRetriever", FakeDenseRetriever)
    response = client.post(
        "/api/ai/retrieve",
        json={
            "method": "dense",
            "query": "payment api http 500",
            "service": "payment-api",
            "category": "server_api",
            "top_k": 5,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["retrieval_method"] == "dense"
    assert body["results"][0]["score"] == 0.9


def test_hybrid_fuses_bm25_and_dense_with_same_filters(monkeypatch) -> None:
    from app.services.retrieval_service import get_dense_retriever
    from app.stores.qdrant_store import VectorSearchResult

    class FakeDenseRetriever:
        def search(self, query: str, **kwargs):
            assert kwargs["version"] == "v1"
            assert kwargs["service"] == "payment-api"
            assert kwargs["access_scope"] == "it_internal"
            return [
                VectorSearchResult(
                    rank=1, score=0.9, chunk_id="RB-API-001-C001", document_id="RB-API-001",
                    content="Dense result", metadata={}, source_type="runbook", source="test",
                    service="payment-api", category="server_api", access_scope="it_internal",
                )
            ]

    get_dense_retriever.cache_clear()
    monkeypatch.setattr("app.services.retrieval_service.DenseRetriever", FakeDenseRetriever)
    response = client.post(
        "/api/ai/retrieve",
        json={
            "method": "hybrid", "query": "payment api http 500", "service": "payment-api",
            "version": "v1", "source_types": ["runbook"], "top_k": 5, "candidate_k": 20,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["retrieval_method"] == "hybrid"
    assert body["filters"]["version"] == "v1"
    assert [item["document_id"] for item in body["results"]] == ["RB-API-001"]
    assert body["results"][0]["score"] > 1 / 61
    get_dense_retriever.cache_clear()


def test_e4_chitchat_skips_models() -> None:
    response = client.post("/api/ai/retrieve", json={"method": "hybrid_rerank", "query": "xin chao"})
    assert response.status_code == 200
    assert response.json()["route"] == "skip"
    assert response.json()["results"] == []


def test_e4_rewrites_and_reranks_with_citations(monkeypatch) -> None:
    from app.services.retrieval_service import get_dense_retriever, get_reranker
    from app.stores.qdrant_store import VectorSearchResult

    class FakeDenseRetriever:
        def search(self, query: str, **kwargs):
            assert "payment-api" in query and "HTTP 500" in query
            return [VectorSearchResult(
                rank=1, score=0.8, chunk_id="RB-API-002-C001", document_id="RB-API-002",
                content="Upgrade steps", metadata={}, source_type="runbook", source="test",
                service="payment-api", category="server_api", access_scope="it_internal",
            )]

    class FakeReranker:
        def score_pairs(self, query: str, passages: list[str]) -> list[float]:
            assert "Hay phan tich RCA" not in query
            return [2.0 if "upgrade" in passage.lower() else 0.1 for passage in passages]

    get_dense_retriever.cache_clear()
    get_reranker.cache_clear()
    monkeypatch.setattr("app.services.retrieval_service.DenseRetriever", FakeDenseRetriever)
    monkeypatch.setattr("app.services.retrieval_service.BgeReranker", FakeReranker)
    response = client.post("/api/ai/retrieve", json={
        "method": "hybrid_rerank", "rewrite": True,
        "query": "Service payment-api HTTP 500. Hay phan tich RCA dua tren ticket, log, metric va runbook lien quan.",
        "service": "payment-api", "source_types": ["runbook"], "top_k": 2, "candidate_k": 20,
    })
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "new_incident" and body["route"] == "retrieve"
    assert body["query"] != body["original_query"]
    assert body["results"][0]["document_id"] == "RB-API-002"
    assert body["results"][0]["chunk_id"] == "RB-API-002-C001"
    get_dense_retriever.cache_clear()
    get_reranker.cache_clear()
