from __future__ import annotations

from app.ingestion.cleaner import clean_text, redact_sensitive_text


def redact_for_audit(value: str) -> str:
    return clean_text(redact_sensitive_text(value))
