from __future__ import annotations

from app.analysis.schema import AnalysisRequest, AnalysisResponse, Evidence, RcaDraft


def build_report(payload: AnalysisRequest, service: str, evidence: list[Evidence], draft: RcaDraft, model: str | None) -> AnalysisResponse:
    return AnalysisResponse(
        **draft.model_dump(), ticket_id=payload.ticket_id, service=service,
        window_start=payload.window_start, window_end=payload.window_end,
        evidence=evidence, model=model, review_required=True,
    )
