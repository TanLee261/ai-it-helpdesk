from __future__ import annotations

import re
from pathlib import Path

from app.ingestion.enricher import IngestDocument


METADATA_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$")


def parse_markdown_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    in_metadata = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "## Metadata":
            in_metadata = True
            continue
        if in_metadata and stripped.startswith("## ") and stripped != "## Metadata":
            break
        if not in_metadata or not stripped.startswith("|"):
            continue
        if "---" in stripped or "Field" in stripped:
            continue
        match = METADATA_ROW_RE.match(stripped)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            metadata[key] = value
    return metadata


def load_runbook_document(path: Path) -> IngestDocument:
    text = path.read_text(encoding="utf-8")
    metadata = parse_markdown_metadata(text)
    document_id = metadata.get("document_id", path.stem)
    title = metadata.get("title") or text.splitlines()[0].lstrip("# ").strip() or document_id
    return IngestDocument(
        document_id=document_id,
        title=title,
        source_type="runbook",
        source=str(path),
        content=text,
        service=metadata.get("service") or None,
        category=metadata.get("category") or None,
        version=metadata.get("version") or "v1",
        access_scope=metadata.get("access_scope") or "it_internal",
        metadata={
            "related_ticket_ids": metadata.get("related_ticket_ids", ""),
            "source_label": metadata.get("source", "synthetic"),
        },
    )


def load_runbook_documents(directory: Path) -> list[IngestDocument]:
    return [load_runbook_document(path) for path in sorted(directory.glob("*.md"))]
