from __future__ import annotations

import re

from app.analysis.schema import Evidence, RcaDraft


class InvalidEvidenceError(ValueError):
    pass


_DECIMAL_VALUE = re.compile(r"(?<![A-Za-z0-9])\d+\.\d+(?![A-Za-z0-9])")
_INTEGER_WITH_UNIT = re.compile(
    r"(?<![A-Za-z0-9])\d+(?=\s?(?:%|percent\b|ms\b|milliseconds?\b|seconds?\b|minutes?\b|hours?\b|gb\b|mb\b|kb\b|count\b|°c\b))",
    flags=re.IGNORECASE,
)


def _measured_values(text: str) -> set[str]:
    matches = [match.group() for match in _DECIMAL_VALUE.finditer(text)]
    matches.extend(match.group() for match in _INTEGER_WITH_UNIT.finditer(text))
    return {value.rstrip("0").rstrip(".") if "." in value else value for value in matches}


def _validate_measured_claim(text: str, citation_ids: list[str], evidence: list[Evidence]) -> None:
    cited_evidence = [item for item in evidence if item.evidence_id in citation_ids]
    claimed_values = _measured_values(text)
    supported_values = set().union(*(_measured_values(item.content) for item in cited_evidence))
    if missing_values := claimed_values - supported_values:
        raise InvalidEvidenceError(
            f"Claim contains unsupported measured values: {', '.join(sorted(missing_values))}"
        )


def validate_draft(draft: RcaDraft, evidence: list[Evidence]) -> None:
    allowed = {item.evidence_id for item in evidence}
    operational_ids = {item.evidence_id for item in evidence if item.source_type in {"ticket", "log", "metric"}}
    cited = set(draft.root_cause_evidence_ids)
    for fact in draft.observed_facts:
        if not set(fact.evidence_ids) & operational_ids:
            raise InvalidEvidenceError("Observed facts require ticket, log or metric evidence")
        _validate_measured_claim(fact.fact, fact.evidence_ids, evidence)
        cited.update(fact.evidence_ids)
    for hypothesis in draft.hypotheses:
        if set(hypothesis.supporting_evidence_ids) & set(hypothesis.contradicting_evidence_ids):
            raise InvalidEvidenceError("Evidence cannot support and contradict the same hypothesis")
        _validate_measured_claim(hypothesis.cause, hypothesis.supporting_evidence_ids, evidence)
        cited.update(hypothesis.supporting_evidence_ids)
        cited.update(hypothesis.contradicting_evidence_ids)
    for step in draft.verification_steps:
        cited.update(step.evidence_ids)
    unknown = cited - allowed
    if unknown:
        raise InvalidEvidenceError(f"Unknown evidence IDs: {', '.join(sorted(unknown))}")
    if draft.status == "grounded":
        incident_ids = {item.evidence_id for item in evidence if item.source_type in {"log", "metric"}}
        if not draft.observed_facts or not draft.probable_root_cause or not (set(draft.root_cause_evidence_ids) & incident_ids):
            raise InvalidEvidenceError("Grounded root cause requires operational evidence")
        _validate_measured_claim(draft.probable_root_cause, draft.root_cause_evidence_ids, evidence)
    elif draft.probable_root_cause or draft.root_cause_evidence_ids:
        raise InvalidEvidenceError("Insufficient evidence cannot claim a root cause")
    elif draft.confidence != "low":
        raise InvalidEvidenceError("Insufficient evidence must have low confidence")


def discard_contextual_facts(draft: RcaDraft, evidence: list[Evidence]) -> RcaDraft:
    observable_ids = {item.evidence_id for item in evidence if item.source_type in {"ticket", "log", "metric"}}
    facts = [fact for fact in draft.observed_facts if set(fact.evidence_ids) & observable_ids]
    return draft.model_copy(update={"observed_facts": facts})
