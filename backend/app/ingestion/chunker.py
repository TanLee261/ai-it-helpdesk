from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    content: str
    token_count: int


def estimate_token_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def split_long_text(text: str, max_chars: int = 1200, overlap_chars: int = 120) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            break_at = text.rfind("\n", start, end)
            if break_at <= start:
                break_at = text.rfind(" ", start, end)
            if break_at > start:
                end = break_at
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - overlap_chars)
    return [chunk for chunk in chunks if chunk]


def chunk_ticket_text(text: str) -> list[TextChunk]:
    return [TextChunk(chunk_index=1, content=text, token_count=estimate_token_count(text))]


def chunk_markdown_by_heading(text: str, max_chars: int = 1200) -> list[TextChunk]:
    sections = re.split(r"(?=^##\s+)", text, flags=re.MULTILINE)
    raw_chunks: list[str] = []
    prefix = ""

    if sections and not sections[0].lstrip().startswith("##"):
        prefix = sections.pop(0).strip()

    for section in sections:
        section = section.strip()
        if not section:
            continue
        content = f"{prefix}\n\n{section}".strip() if prefix else section
        raw_chunks.extend(split_long_text(content, max_chars=max_chars))

    if not raw_chunks and text.strip():
        raw_chunks = split_long_text(text.strip(), max_chars=max_chars)

    return [
        TextChunk(chunk_index=index, content=content, token_count=estimate_token_count(content))
        for index, content in enumerate(raw_chunks, start=1)
    ]
