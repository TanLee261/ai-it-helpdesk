from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.analysis.log_filter import load_logs, load_metrics
from app.analysis.prompt_builder import SYSTEM_PROMPT, build_user_prompt
from app.analysis.report import build_report
from app.analysis.schema import AnalysisRequest, AnalysisResponse, Evidence, RcaDraft
from app.analysis.trace import write_analysis_trace
from app.analysis.validator import InvalidEvidenceError, discard_contextual_facts, validate_draft
from app.ingestion.cleaner import clean_text
from app.models.llm.ollama import InvalidLlmResponseError, LlmUnavailableError, OllamaRcaGenerator
from app.schemas.retrieval import RetrievalRequest
from app.services.retrieval_service import retrieve_evidence
from app.services.ticket_service import get_ticket_by_ticket_id


@lru_cache(maxsize=1)
def get_generator() -> OllamaRcaGenerator:
    return OllamaRcaGenerator()


def analyze_incident(db: Session, payload: AnalysisRequest) -> AnalysisResponse:
    ticket = get_ticket_by_ticket_id(db, payload.ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    evidence = [Evidence(
        evidence_id=ticket.ticket_id, source_type="ticket", service=ticket.service,
        content=clean_text(f"Title: {ticket.title}\nDescription: {ticket.description}")[:800],
    )]
    runbook_quota = (payload.top_k + 1) // 2
    history_quota = payload.top_k - runbook_quota
    retrieved_by_type: dict[str, list] = {}
    for source_type in ("runbook", "historical_ticket"):
        response = retrieve_evidence(db, RetrievalRequest(
            ticket_id=ticket.ticket_id, method=payload.retrieval_method,
            service=ticket.service, category=ticket.category,
            source_types=[source_type], access_scope="it_internal",
            top_k=payload.top_k, candidate_k=30, rerank_k=20,
        ))
        retrieved_by_type[source_type] = [
            item for item in response.results
            if item.document_id != f"KT-{ticket.ticket_id}"
        ]

    selected = []
    for source_type, quota in (("runbook", runbook_quota), ("historical_ticket", history_quota)):
        selected.extend(retrieved_by_type[source_type][:quota])
    # Backfill unused quota from the other source when one pool is sparse.
    selected_ids = {item.chunk_id for item in selected}
    for source_type in ("runbook", "historical_ticket"):
        for item in retrieved_by_type[source_type]:
            if len(selected) >= payload.top_k:
                break
            if item.chunk_id not in selected_ids:
                selected.append(item)
                selected_ids.add(item.chunk_id)
    for item in selected:
        evidence.append(Evidence(
            evidence_id=item.chunk_id, source_type=item.source_type,
            service=ticket.service, content=clean_text(item.content)[:800],
        ))
    evidence.extend(load_logs(ticket.service, payload.window_start, payload.window_end, ticket_id=ticket.ticket_id))
    evidence.extend(load_metrics(ticket.service, payload.window_start, payload.window_end, ticket_id=ticket.ticket_id))

    operational = [item for item in evidence if item.source_type in {"log", "metric"}]
    if not operational:
        draft = RcaDraft(
            status="insufficient_evidence", observed_facts=[], hypotheses=[],
            confidence="low", missing_evidence=["Logs or metrics for the selected service and time window"],
            verification_steps=[], proposed_actions=[],
        )
        return build_report(payload, ticket.service, evidence, draft, model=None)

    generator = get_generator()
    prompt = build_user_prompt(
        ticket.ticket_id, ticket.service,
        payload.window_start.isoformat(), payload.window_end.isoformat(), evidence,
    )
    started = perf_counter()
    raw_response = None
    validation_error = None
    try:
        if hasattr(generator, "generate_with_trace"):
            draft, raw_response = generator.generate_with_trace(SYSTEM_PROMPT, prompt)
        else:
            draft = generator.generate(SYSTEM_PROMPT, prompt)
        draft = discard_contextual_facts(draft, evidence)
        validate_draft(draft, evidence)
        draft = suppress_unsupported_rollback(draft, evidence)
    except LlmUnavailableError as exc:
        _record_analysis_trace(payload, evidence, prompt, raw_response, None, generator.model, started, str(exc))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except InvalidEvidenceError as exc:
        validation_error = str(exc)
        safe_draft = RcaDraft(
            status="insufficient_evidence", observed_facts=[], hypotheses=[],
            confidence="low", missing_evidence=[f"RCA validation failed: {exc}"],
            verification_steps=[], proposed_actions=[],
        )
        response = build_report(payload, ticket.service, evidence, safe_draft, model=generator.model)
        _record_analysis_trace(payload, evidence, prompt, raw_response, response, generator.model, started, validation_error)
        return response
    except InvalidLlmResponseError as exc:
        _record_analysis_trace(payload, evidence, prompt, raw_response, None, generator.model, started, str(exc))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    response = build_report(payload, ticket.service, evidence, draft, model=generator.model)
    _record_analysis_trace(payload, evidence, prompt, raw_response, response, generator.model, started, validation_error)
    return response


def _record_analysis_trace(payload, evidence, prompt, raw_response, response, model, started, validation_error) -> None:
    write_analysis_trace({
        "ticket_id": payload.ticket_id,
        "window_start": payload.window_start.isoformat(),
        "window_end": payload.window_end.isoformat(),
        "retrieval_method": payload.retrieval_method,
        "top_k": payload.top_k,
        "model": model,
        "retrieved_evidence": [
            {"evidence_id": item.evidence_id, "source_type": item.source_type}
            for item in evidence
        ],
        "prompt_evidence_ids": [item.evidence_id for item in evidence],
        "prompt_sha256": sha256(prompt.encode("utf-8")).hexdigest(),
        "raw_llm_response": raw_response,
        "validated_response": response.model_dump(mode="json") if response is not None else None,
        "validation_error": validation_error,
        "latency_ms": round((perf_counter() - started) * 1000, 2),
    })


def suppress_unsupported_rollback(draft: RcaDraft, evidence: list[Evidence]) -> RcaDraft:
    rollback_terms = ("rollback", "roll back", "revert configuration", "revert config", "hoàn tác", "quay lại cấu hình", "khôi phục cấu hình")
    change_terms = ("deployment", "config", "configuration", "change", "triển khai", "cấu hình", "thay đổi")
    completion_terms = ("completed", "applied", "changed", "deployed", "updated", "đã áp dụng", "đã thay đổi", "đã triển khai", "đã cập nhật")
    operational_text = " ".join(
        item.content.lower() for item in evidence if item.source_type in {"log", "metric"}
    )
    has_change_evidence = any(term in operational_text for term in change_terms) and any(
        term in operational_text for term in completion_terms
    )
    actions = [
        action for action in draft.proposed_actions
        if has_change_evidence or not any(term in action.lower() for term in rollback_terms)
    ]
    if len(actions) == len(draft.proposed_actions):
        return draft
    missing = list(draft.missing_evidence)
    note = "Verified evidence of a recent deployment or configuration change before considering rollback"
    if note not in missing:
        missing.append(note)
    return draft.model_copy(update={"proposed_actions": actions, "missing_evidence": missing})
