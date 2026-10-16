from __future__ import annotations

from functools import lru_cache

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.retrieval.dense import DenseRetriever
from app.retrieval.candidate_pool import build_candidate_pool
from app.retrieval.lexical import load_candidates, search_bm25
from app.retrieval.query.rewriting import rewrite_query
from app.retrieval.query.routing import route_query
from app.retrieval.query.understanding import understand_query
from app.retrieval.reranker import rerank_candidates
from app.retrieval.rrf import fuse_results, ranked_documents
from app.models.reranker.bge_reranker import BgeReranker
from app.schemas.retrieval import RetrievalFilters, RetrievalRequest, RetrievalResponse, RetrievalResult
from app.services.ticket_service import get_ticket_by_ticket_id


def build_ticket_query(title: str, description: str, service: str, category: str) -> str:
    return " ".join([title, description, service, category]).strip()


@lru_cache(maxsize=1)
def get_dense_retriever() -> DenseRetriever:
    return DenseRetriever()


@lru_cache(maxsize=1)
def get_reranker() -> BgeReranker:
    return BgeReranker()


def retrieve_evidence(db: Session, payload: RetrievalRequest) -> RetrievalResponse:
    query_text = payload.query
    service = payload.service
    category = payload.category

    if payload.ticket_id:
        ticket = get_ticket_by_ticket_id(db, payload.ticket_id)
        if ticket is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        if not query_text:
            query_text = build_ticket_query(ticket.title, ticket.description, ticket.service, ticket.category)
        service = service or ticket.service
        category = category or ticket.category

    assert query_text is not None
    original_query = query_text
    intent = None
    route = None
    if payload.method == "hybrid_rerank":
        understanding = understand_query(query_text)
        decision = route_query(understanding)
        intent, route = understanding.intent, decision.route
        service = service or understanding.service
        if decision.route == "skip":
            return RetrievalResponse(
                query=query_text,
                retrieval_method=payload.method,
                filters=RetrievalFilters(
                    service=service, category=category, version=payload.version,
                    source_types=payload.source_types, access_scope=payload.access_scope,
                ),
                results=[], original_query=original_query, intent=intent, route=route,
            )
        if payload.rewrite:
            query_text = rewrite_query(query_text)

    if payload.method in {"bm25", "hybrid", "hybrid_rerank"}:
        candidates = load_candidates(
            db,
            service=service,
            category=category,
            version=payload.version,
            source_types=payload.source_types,
            access_scope=payload.access_scope,
        )
        bm25_results = search_bm25(query_text, candidates, top_k=payload.candidate_k)
    else:
        bm25_results = []

    if payload.method in {"dense", "hybrid", "hybrid_rerank"}:
        dense_results = get_dense_retriever().search(
            query_text,
            top_k=payload.candidate_k,
            service=service,
            category=category,
            version=payload.version,
            source_types=payload.source_types,
            access_scope=payload.access_scope,
        )
    else:
        dense_results = []

    if payload.method == "hybrid_rerank":
        fused = fuse_results(bm25_results, dense_results, top_k=payload.rerank_k)
        pool = build_candidate_pool(fused, payload.rerank_k, payload.access_scope)
        results = rerank_candidates(query_text, pool, get_reranker(), top_k=payload.top_k)
    elif payload.method == "hybrid":
        results = fuse_results(bm25_results, dense_results, top_k=payload.top_k)
    else:
        results = ranked_documents(
            bm25_results if payload.method == "bm25" else dense_results,
            payload.top_k,
        )
    return RetrievalResponse(
        query=query_text,
        retrieval_method=payload.method,
        filters=RetrievalFilters(
            service=service,
            category=category,
            version=payload.version,
            source_types=payload.source_types,
            access_scope=payload.access_scope,
        ),
        results=[RetrievalResult(**result.__dict__) for result in results],
        original_query=original_query if payload.method == "hybrid_rerank" else None,
        intent=intent,
        route=route,
    )
