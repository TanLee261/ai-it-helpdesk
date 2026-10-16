from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal, Optional


Intent = Literal["support_question", "new_incident", "compare_incidents", "escalate", "chitchat"]
ERROR_CODE = re.compile(r"\b(?:HTTP\s*[45]\d\d|[45]\d\d|[A-Z][A-Z0-9_]*[-_][A-Z0-9_-]+)\b", re.IGNORECASE)
SERVICE = re.compile(r"\b(?:service|dich vu)\s+([a-z][a-z0-9_-]+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class QueryUnderstanding:
    intent: Intent
    service: Optional[str]
    error_codes: tuple[str, ...]


def understand_query(query: str) -> QueryUnderstanding:
    lower = unicodedata.normalize("NFKD", query.lower().replace("đ", "d"))
    lower = "".join(character for character in lower if not unicodedata.combining(character)).strip()
    if re.search(r"\b(so sanh|compare)\b", lower):
        intent: Intent = "compare_incidents"
    elif re.search(r"\b(escalate|chuyen cap|bao dong)\b", lower):
        intent = "escalate"
    elif re.search(r"\b(incident|su co|root cause|rca)\b", lower):
        intent = "new_incident"
    elif re.fullmatch(r"(hi|hello|xin chao|chao ban|cam on|thanks)[!.?\s]*", lower):
        intent = "chitchat"
    else:
        intent = "support_question"
    match = SERVICE.search(lower)
    return QueryUnderstanding(
        intent=intent,
        service=match.group(1).lower() if match else None,
        error_codes=tuple(dict.fromkeys(code.upper() for code in ERROR_CODE.findall(query))),
    )
