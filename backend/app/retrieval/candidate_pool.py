from __future__ import annotations

from typing import Any


def build_candidate_pool(results: list[Any], limit: int, access_scope: str) -> list[Any]:
    pool: list[Any] = []
    seen: set[str] = set()
    for result in results:
        if result.access_scope != access_scope or result.document_id in seen:
            continue
        seen.add(result.document_id)
        pool.append(result)
        if len(pool) >= limit:
            break
    return pool
