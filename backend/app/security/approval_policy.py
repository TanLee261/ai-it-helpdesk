from __future__ import annotations


def validate_advisory_action(action: str, rationale: str) -> None:
    if not action.strip() or not rationale.strip():
        raise ValueError("Action and rationale are required")
    if len(action) > 1000 or len(rationale) > 3000:
        raise ValueError("Action or rationale exceeds the allowed length")
