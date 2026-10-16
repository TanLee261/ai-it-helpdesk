from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_it_helpdesk"
DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_QDRANT_COLLECTION = "knowledge_chunks"
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-m3"
DEFAULT_EMBEDDING_DIMENSION = 1024
DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "qwen3.5:4b"


def load_dotenv_if_present() -> None:
    env_file = ROOT_DIR / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#") or "=" not in clean:
            continue
        key, value = clean.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    app_name: str
    env: str
    database_url: str
    qdrant_url: str
    qdrant_collection: str
    embedding_model: str
    embedding_dimension: int
    reranker_model: str
    ollama_url: str
    ollama_model: str
    ollama_timeout_seconds: int


@lru_cache
def get_settings() -> Settings:
    load_dotenv_if_present()
    return Settings(
        app_name=os.getenv("APP_NAME", "AI IT Helpdesk"),
        env=os.getenv("ENV", "dev"),
        database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        qdrant_url=os.getenv("QDRANT_URL", DEFAULT_QDRANT_URL),
        qdrant_collection=os.getenv("QDRANT_COLLECTION", DEFAULT_QDRANT_COLLECTION),
        embedding_model=os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        embedding_dimension=int(os.getenv("EMBEDDING_DIMENSION", str(DEFAULT_EMBEDDING_DIMENSION))),
        reranker_model=os.getenv("RERANKER_MODEL", DEFAULT_RERANKER_MODEL),
        ollama_url=os.getenv("OLLAMA_URL", DEFAULT_OLLAMA_URL),
        ollama_model=os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
        ollama_timeout_seconds=int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180")),
    )
