from __future__ import annotations

import re


INSTRUCTION_LIKE_RE = re.compile(
    r"(?i)(ignore (all )?(previous|prior|system) instructions|"
    r"reveal (the )?(system prompt|secrets|credentials)|"
    r"you are now (the )?(system|assistant)|"
    r"bỏ qua (mọi )?(chỉ dẫn|hướng dẫn)|tiết lộ (prompt|mật khẩu))"
)


def contains_instruction_like_text(text: str) -> bool:
    return bool(INSTRUCTION_LIKE_RE.search(text or ""))
