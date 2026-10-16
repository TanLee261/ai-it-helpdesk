from __future__ import annotations

from app.retrieval.lexical import LexicalSearchResult
from app.retrieval.rrf import fuse_results, ranked_documents


def result(document_id: str, chunk_id: str, rank: int) -> LexicalSearchResult:
    return LexicalSearchResult(
        rank=rank,
        score=1.0 / rank,
        chunk_id=chunk_id,
        document_id=document_id,
        content=chunk_id,
        metadata={},
        source_type="runbook",
        source="test",
        service="payment-api",
        category="server_api",
        access_scope="it_internal",
    )


def test_rrf_fuses_by_document_and_retains_best_chunk() -> None:
    bm25 = [result("RB-A", "A-1", 1), result("RB-A", "A-2", 2), result("RB-B", "B-1", 3)]
    dense = [result("RB-B", "B-2", 1), result("RB-A", "A-3", 2)]

    fused = fuse_results(bm25, dense, top_k=5)

    assert [item.document_id for item in fused] == ["RB-A", "RB-B"]
    assert fused[0].chunk_id == "A-1"
    assert fused[0].rank == 1
    assert round(fused[0].score, 8) == round(1 / 61 + 1 / 62, 8)


def test_ranked_documents_removes_duplicate_chunks() -> None:
    ranked = ranked_documents([result("RB-A", "A-1", 1), result("RB-A", "A-2", 2), result("RB-B", "B-1", 3)], 2)
    assert [(item.document_id, item.rank) for item in ranked] == [("RB-A", 1), ("RB-B", 2)]
