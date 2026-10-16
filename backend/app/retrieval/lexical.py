from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import KnowledgeChunk, KnowledgeDocument


TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


@dataclass(frozen=True)
class LexicalCandidate:
    chunk_id: str
    document_id: str
    content: str
    metadata: dict
    source_type: str
    source: str
    service: Optional[str]
    category: Optional[str]
    access_scope: str


@dataclass(frozen=True)
class LexicalSearchResult:
    rank: int
    score: float
    chunk_id: str
    document_id: str
    content: str
    metadata: dict
    source_type: str
    source: str
    service: Optional[str]
    category: Optional[str]
    access_scope: str


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text or "")]


def load_candidates(
    db: Session,
    *,
    service: Optional[str] = None,
    category: Optional[str] = None,
    version: Optional[str] = None,
    source_types: Optional[list[str]] = None,
    access_scope: str = "it_internal",
) -> list[LexicalCandidate]:
    query = db.query(KnowledgeChunk, KnowledgeDocument).join(
        KnowledgeDocument,
        KnowledgeChunk.document_id == KnowledgeDocument.document_id,
    )
    if service:
        query = query.filter(KnowledgeDocument.service == service)
    if category:
        query = query.filter(KnowledgeDocument.category == category)
    if version:
        query = query.filter(KnowledgeDocument.version == version)
    if source_types:
        query = query.filter(KnowledgeDocument.source_type.in_(source_types))
    if access_scope:
        query = query.filter(KnowledgeDocument.access_scope == access_scope)

    candidates: list[LexicalCandidate] = []
    for chunk, document in query.all():
        candidates.append(
            LexicalCandidate(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                content=chunk.content,
                metadata=chunk.metadata_json,
                source_type=document.source_type,
                source=document.source,
                service=document.service,
                category=document.category,
                access_scope=document.access_scope,
            )
        )
    return candidates


def search_bm25(
    query_text: str,
    candidates: list[LexicalCandidate],
    *,
    top_k: int = 5,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[LexicalSearchResult]:
    query_terms = tokenize(query_text)
    if not query_terms or not candidates:
        return []

    tokenized_docs = [tokenize(candidate.content) for candidate in candidates]
    doc_lengths = [len(tokens) for tokens in tokenized_docs]
    avg_doc_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0.0
    doc_freq: Counter[str] = Counter()
    for tokens in tokenized_docs:
        doc_freq.update(set(tokens))

    total_docs = len(candidates)
    scored: list[tuple[float, LexicalCandidate]] = []
    for candidate, tokens, doc_length in zip(candidates, tokenized_docs, doc_lengths):
        term_freq = Counter(tokens)
        score = 0.0
        for term in query_terms:
            if term_freq[term] == 0:
                continue
            idf = math.log(1 + (total_docs - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
            numerator = term_freq[term] * (k1 + 1)
            denominator = term_freq[term] + k1 * (1 - b + b * doc_length / max(avg_doc_length, 1.0))
            score += idf * numerator / denominator
        if score > 0:
            scored.append((score, candidate))

    scored.sort(key=lambda item: item[0], reverse=True)
    results: list[LexicalSearchResult] = []
    for rank, (score, candidate) in enumerate(scored[:top_k], start=1):
        results.append(
            LexicalSearchResult(
                rank=rank,
                score=round(score, 6),
                chunk_id=candidate.chunk_id,
                document_id=candidate.document_id,
                content=candidate.content,
                metadata=candidate.metadata,
                source_type=candidate.source_type,
                source=candidate.source,
                service=candidate.service,
                category=candidate.category,
                access_scope=candidate.access_scope,
            )
        )
    return results
