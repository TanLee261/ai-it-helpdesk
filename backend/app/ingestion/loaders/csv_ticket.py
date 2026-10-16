from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from app.ingestion.enricher import IngestDocument


def row_to_ticket_document(row: dict[str, str]) -> IngestDocument:
    ticket_id = row["ticket_id"].strip()
    title = row.get("title", "").strip() or ticket_id
    description = row.get("description", "").strip()
    content = "\n".join(
        [
            f"Ticket ID: {ticket_id}",
            f"Title: {title}",
            f"Description: {description}",
            f"Service: {row.get('service', '').strip()}",
            f"Category: {row.get('category', '').strip()}",
            f"Priority: {row.get('priority', '').strip()}",
            f"Impact: {row.get('impact', '').strip()}",
            f"Urgency: {row.get('urgency', '').strip()}",
            f"Assigned team: {row.get('assigned_team', '').strip()}",
            f"Status: {row.get('status', '').strip()}",
            f"Verified root cause: {row.get('verified_root_cause', '').strip()}",
            f"Resolution: {row.get('resolution', '').strip()}",
        ]
    )
    return IngestDocument(
        document_id=f"KT-{ticket_id}",
        title=title,
        source_type="historical_ticket",
        source=row.get("source", "").strip() or "data/processed/tickets/normalized_tickets.csv",
        content=content,
        service=row.get("service", "").strip() or None,
        category=row.get("category", "").strip() or None,
        version="v1",
        access_scope="it_internal",
        metadata={
            "ticket_id": ticket_id,
            "source_ticket_id": row.get("source_ticket_id", "").strip(),
            "raw_category": row.get("raw_category", "").strip(),
            "sub_category": row.get("sub_category", "").strip(),
        },
    )


def load_ticket_documents(path: Path, limit: Optional[int] = None) -> list[IngestDocument]:
    documents: list[IngestDocument] = []
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            documents.append(row_to_ticket_document(row))
            if limit is not None and len(documents) >= limit:
                break
    return documents
