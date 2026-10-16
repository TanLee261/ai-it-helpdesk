from __future__ import annotations

from typing import Optional

from app.models.embedding.bge_m3 import BgeM3EmbeddingModel
from app.stores.qdrant_store import QdrantVectorStore, VectorSearchResult


class DenseRetriever:
    def __init__(
        self,
        embedding_model: Optional[BgeM3EmbeddingModel] = None,
        vector_store: Optional[QdrantVectorStore] = None,
    ) -> None:
        self.embedding_model = embedding_model or BgeM3EmbeddingModel()
        self.vector_store = vector_store or QdrantVectorStore()

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        service: Optional[str] = None,
        category: Optional[str] = None,
        version: Optional[str] = None,
        source_types: Optional[list[str]] = None,
        access_scope: str = "it_internal",
    ) -> list[VectorSearchResult]:
        query_vector = self.embedding_model.embed_text(query)
        return self.vector_store.search(
            query_vector,
            top_k=top_k,
            service=service,
            category=category,
            version=version,
            source_types=source_types,
            access_scope=access_scope,
        )
