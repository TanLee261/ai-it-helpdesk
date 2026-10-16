from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.models.reranker.base import RerankerModel


def rerank_candidates(
    query: str,
    candidates: list[Any],
    model: RerankerModel,
    *,
    top_k: int,
) -> list[Any]:
    if not candidates:
        return []
    scores = model.score_pairs(query, [candidate.content for candidate in candidates])
    if len(scores) != len(candidates):
        raise ValueError("Reranker returned a different number of scores than candidates")
    ordered = sorted(enumerate(candidates), key=lambda item: (-scores[item[0]], item[0]))
    return [
        replace(candidate, rank=rank, score=round(scores[index], 6))
        for rank, (index, candidate) in enumerate(ordered[:top_k], start=1)
    ]
