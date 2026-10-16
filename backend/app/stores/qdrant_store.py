from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Optional

from app.core.config import get_settings


@dataclass(frozen=True)
class VectorSearchResult:
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


def stable_point_id(chunk_id: str) -> str:
    digest = hashlib.md5(chunk_id.encode("utf-8")).hexdigest()
    return f"{digest[:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"


class QdrantVectorStore:
    def __init__(self, url: Optional[str] = None, collection_name: Optional[str] = None) -> None:
        settings = get_settings()
        self.url = url or settings.qdrant_url
        self.collection_name = collection_name or settings.qdrant_collection
        self.dimension = settings.embedding_dimension

    @property
    def client(self):
        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:
            raise RuntimeError(
                "qdrant-client is required for dense retrieval. "
                "Install backend dependencies with: python3 -m pip install -e 'backend[dev]'"
            ) from exc
        return QdrantClient(url=self.url, check_compatibility=False)

    def ensure_collection(self, recreate: bool = False) -> None:
        from qdrant_client import models

        client = self.client
        exists = client.collection_exists(self.collection_name)
        if exists and recreate:
            client.delete_collection(self.collection_name)
            exists = False
        if not exists:
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.dimension,
                    distance=models.Distance.COSINE,
                ),
            )

    def upsert_points(self, points: list[dict[str, Any]]) -> None:
        from qdrant_client import models

        qdrant_points = [
            models.PointStruct(
                id=point["id"],
                vector=point["vector"],
                payload=point["payload"],
            )
            for point in points
        ]
        if qdrant_points:
            self.client.upsert(collection_name=self.collection_name, points=qdrant_points)

    def build_filter(
        self,
        *,
        service: Optional[str] = None,
        category: Optional[str] = None,
        version: Optional[str] = None,
        source_types: Optional[list[str]] = None,
        access_scope: str = "it_internal",
    ):
        from qdrant_client import models

        conditions = []
        if service:
            conditions.append(models.FieldCondition(key="service", match=models.MatchValue(value=service)))
        if category:
            conditions.append(models.FieldCondition(key="category", match=models.MatchValue(value=category)))
        if version:
            conditions.append(models.FieldCondition(key="version", match=models.MatchValue(value=version)))
        if access_scope:
            conditions.append(models.FieldCondition(key="access_scope", match=models.MatchValue(value=access_scope)))
        if source_types:
            conditions.append(models.FieldCondition(key="source_type", match=models.MatchAny(any=source_types)))
        if not conditions:
            return None
        return models.Filter(must=conditions)

    def search(
        self,
        query_vector: list[float],
        *,
        top_k: int = 5,
        service: Optional[str] = None,
        category: Optional[str] = None,
        version: Optional[str] = None,
        source_types: Optional[list[str]] = None,
        access_scope: str = "it_internal",
    ) -> list[VectorSearchResult]:
        query_filter = self.build_filter(
            service=service,
            category=category,
            version=version,
            source_types=source_types,
            access_scope=access_scope,
        )
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
        results: list[VectorSearchResult] = []
        for rank, hit in enumerate(response.points, start=1):
            payload = hit.payload or {}
            results.append(
                VectorSearchResult(
                    rank=rank,
                    score=round(float(hit.score), 6),
                    chunk_id=payload["chunk_id"],
                    document_id=payload["document_id"],
                    content=payload.get("content", ""),
                    metadata=payload.get("metadata", {}),
                    source_type=payload.get("source_type", ""),
                    source=payload.get("source", ""),
                    service=payload.get("service"),
                    category=payload.get("category"),
                    access_scope=payload.get("access_scope", ""),
                )
            )
        return results
