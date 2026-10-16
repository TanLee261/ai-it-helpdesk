from __future__ import annotations

import re


BOILERPLATE = (
    re.compile(r"\bHay phan tich RCA dua tren ticket, log, metric va runbook lien quan\.?", re.IGNORECASE),
    re.compile(r"\bHãy phân tích RCA dựa trên ticket, log, metric và runbook liên quan\.?", re.IGNORECASE),
    re.compile(r"\bcan tim bang chung nao de xac minh su co tren\b", re.IGNORECASE),
    re.compile(r"\bcần tìm bằng chứng nào để xác minh sự cố trên\b", re.IGNORECASE),
    re.compile(r"\bTechnician nen kiem tra cac buoc nao cho\b", re.IGNORECASE),
    re.compile(r"\bKỹ thuật viên nên kiểm tra các bước nào cho\b", re.IGNORECASE),
)


def rewrite_query(query: str) -> str:
    rewritten = query
    for pattern in BOILERPLATE:
        rewritten = pattern.sub(" ", rewritten)
    rewritten = re.sub(r"\s+", " ", rewritten).strip(" .?;:")
    return rewritten if len(rewritten) >= 3 else query
