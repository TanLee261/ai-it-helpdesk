from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Optional


@dataclass(frozen=True)
class FusedResult:
    rank: int
    score: float
    chunk_id: str
    document_id: str
    content: str
    metadata: dict[str, Any]
    source_type: str
    source: str
    service: Optional[str]
    category: Optional[str]
    access_scope: str


def ranked_documents(results: list[Any], top_k: int) -> list[Any]:
    seen: set[str] = set()
    documents: list[Any] = []
    for result in results:
        if result.document_id in seen:
            continue
        seen.add(result.document_id)
        documents.append(replace(result, rank=len(documents) + 1))
        if len(documents) >= top_k:
            break
    return documents


def fuse_results(
    bm25_results: list[Any],
    dense_results: list[Any],
    *,
    top_k: int,
    rrf_k: int = 60,
) -> list[FusedResult]:
    if rrf_k < 1:
        raise ValueError("rrf_k must be positive")

    scores: dict[str, float] = {}
    evidence: dict[str, Any] = {}
    first_seen: dict[str, int] = {}
    for branch in (bm25_results, dense_results):
        for result in ranked_documents(branch, len(branch)):
            document_id = result.document_id
            scores[document_id] = scores.get(document_id, 0.0) + 1.0 / (rrf_k + result.rank)
            if document_id not in evidence:
                evidence[document_id] = result
                first_seen[document_id] = len(first_seen)

    ordered_ids = sorted(scores, key=lambda document_id: (-scores[document_id], first_seen[document_id]))
    fused: list[FusedResult] = []
    for document_id in ordered_ids[:top_k]:
        result = evidence[document_id]
        fused.append(
            FusedResult(
                rank=len(fused) + 1,
                score=round(scores[document_id], 8),
                chunk_id=result.chunk_id,
                document_id=document_id,
                content=result.content,
                metadata=result.metadata,
                source_type=result.source_type,
                source=result.source,
                service=result.service,
                category=result.category,
                access_scope=result.access_scope,
            )
        )
    return fused
