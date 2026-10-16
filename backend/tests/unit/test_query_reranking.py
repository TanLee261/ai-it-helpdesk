from __future__ import annotations

from app.retrieval.candidate_pool import build_candidate_pool
from app.retrieval.query.rewriting import rewrite_query
from app.retrieval.query.routing import route_query
from app.retrieval.query.understanding import understand_query
from app.retrieval.reranker import rerank_candidates
from app.retrieval.rrf import FusedResult
from app.schemas.retrieval import RetrievalRequest


def candidate(document_id: str, scope: str = "it_internal") -> FusedResult:
    return FusedResult(
        rank=1, score=0.1, chunk_id=f"{document_id}-C001", document_id=document_id,
        content=document_id, metadata={}, source_type="runbook", source="test",
        service="payment-api", category="server_api", access_scope=scope,
    )


def test_query_rewrite_preserves_service_and_error_code() -> None:
    query = "Service payment-api co dau hieu HTTP 500. Hay phan tich RCA dua tren ticket, log, metric va runbook lien quan."
    understanding = understand_query(query)
    rewritten = rewrite_query(query)

    assert understanding.service == "payment-api"
    assert "HTTP 500" in understanding.error_codes
    assert understanding.intent == "new_incident"
    assert "payment-api" in rewritten and "HTTP 500" in rewritten
    assert "Hay phan tich RCA" not in rewritten


def test_chitchat_is_not_sent_to_retrieval() -> None:
    assert route_query(understand_query("xin chao")).route == "skip"
    assert route_query(understand_query("xin chào")).route == "skip"


def test_accented_vietnamese_query_keeps_entities() -> None:
    query = "Dịch vụ payment-api trả HTTP 500. Hãy phân tích RCA dựa trên ticket, log, metric và runbook liên quan."
    understood = understand_query(query)
    rewritten = rewrite_query(query)
    assert understood.intent == "new_incident"
    assert understood.service == "payment-api"
    assert "HTTP 500" in understood.error_codes
    assert "payment-api" in rewritten and "HTTP 500" in rewritten
    assert "Hãy phân tích RCA" not in rewritten


def test_e4_uses_tuned_candidate_depth_by_default() -> None:
    assert RetrievalRequest(query="payment api", method="hybrid_rerank").candidate_k == 20
    assert RetrievalRequest(query="payment api", method="hybrid_rerank", candidate_k=50).candidate_k == 50
    assert RetrievalRequest(query="payment api", method="hybrid").candidate_k == 50


def test_candidate_pool_filters_scope_and_deduplicates_documents() -> None:
    pool = build_candidate_pool(
        [candidate("RB-1"), candidate("RB-1"), candidate("RB-2", "admin_only")],
        limit=5,
        access_scope="it_internal",
    )
    assert [item.document_id for item in pool] == ["RB-1"]


def test_reranker_uses_model_scores_and_keeps_citation_ids() -> None:
    class FakeModel:
        def score_pairs(self, query: str, passages: list[str]) -> list[float]:
            assert passages == ["RB-1", "RB-2"]
            return [0.2, 2.0]

    results = rerank_candidates("payment-api HTTP 500", [candidate("RB-1"), candidate("RB-2")], FakeModel(), top_k=2)
    assert [(item.document_id, item.chunk_id, item.rank) for item in results] == [
        ("RB-2", "RB-2-C001", 1), ("RB-1", "RB-1-C001", 2),
    ]
