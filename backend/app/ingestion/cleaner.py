from __future__ import annotations

import re


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
SECRET_RE = re.compile(
    r"(?i)\b(password|passwd|pwd|token|api[_-]?key|secret)\b\s*[:=]\s*['\"]?[^'\"\s]+"
)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def redact_sensitive_text(text: str) -> str:
    text = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = IP_RE.sub("[REDACTED_IP]", text)
    return SECRET_RE.sub(lambda match: f"{match.group(1)}=[REDACTED_SECRET]", text)


def clean_text(text: str) -> str:
    return normalize_text(redact_sensitive_text(text or ""))
