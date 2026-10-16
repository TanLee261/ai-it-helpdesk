from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.models import KnowledgeChunk, KnowledgeDocument  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.embedding.bge_m3 import BgeM3EmbeddingModel  # noqa: E402
from app.stores.qdrant_store import QdrantVectorStore, stable_point_id  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Qdrant vector index from knowledge_chunks.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum chunks to index. 0 means all chunks.")
    parser.add_argument("--batch-size", type=int, default=16, help="Embedding/upsert batch size.")
    parser.add_argument("--recreate", action="store_true", help="Delete and recreate the Qdrant collection.")
    return parser.parse_args()


def load_chunk_rows(limit: int) -> list[tuple[KnowledgeChunk, KnowledgeDocument]]:
    with SessionLocal() as db:
        query = (
            db.query(KnowledgeChunk, KnowledgeDocument)
            .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.document_id)
            .order_by(KnowledgeChunk.id.asc())
        )
        if limit:
            query = query.limit(limit)
        return list(query.all())


def update_point_ids(chunk_point_ids: list[tuple[str, str]]) -> None:
    with SessionLocal() as db:
        for chunk_id, point_id in chunk_point_ids:
            chunk = db.query(KnowledgeChunk).filter(KnowledgeChunk.chunk_id == chunk_id).one_or_none()
            if chunk is not None:
                chunk.qdrant_point_id = point_id
        db.commit()


def main() -> None:
    args = parse_args()
    rows = load_chunk_rows(args.limit)
    embedding_model = BgeM3EmbeddingModel()
    vector_store = QdrantVectorStore()
    vector_store.ensure_collection(recreate=args.recreate)

    total = 0
    point_updates: list[tuple[str, str]] = []
    for start in range(0, len(rows), args.batch_size):
        batch = rows[start : start + args.batch_size]
        texts = [chunk.content for chunk, _document in batch]
        vectors = embedding_model.embed_texts(texts)
        points = []
        for (chunk, document), vector in zip(batch, vectors):
            point_id = stable_point_id(chunk.chunk_id)
            payload = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "metadata": chunk.metadata_json,
                "source_type": document.source_type,
                "source": document.source,
                "service": document.service,
                "category": document.category,
                "version": document.version,
                "access_scope": document.access_scope,
            }
            points.append({"id": point_id, "vector": vector, "payload": payload})
            point_updates.append((chunk.chunk_id, point_id))
        vector_store.upsert_points(points)
        total += len(points)
        print(f"Indexed {total}/{len(rows)} chunks")

    update_point_ids(point_updates)
    print(f"Built Qdrant index for {total} chunks using {embedding_model.model_name}")


if __name__ == "__main__":
    main()
