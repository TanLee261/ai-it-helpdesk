from __future__ import annotations

import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.models import Ticket  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402


TICKETS_CSV = ROOT_DIR / "data" / "processed" / "tickets" / "normalized_tickets.csv"
DEFAULT_LIMIT = int(os.getenv("SEED_TICKET_LIMIT", "1000"))
STATUS_SEQUENCE = (
    ["resolved"] * 70
    + ["new"] * 15
    + ["in_progress"] * 10
    + ["closed"] * 5
)


def parse_bool(value: str) -> bool:
    return value.strip().upper() == "TRUE"


def status_for_index(index: int) -> str:
    return STATUS_SEQUENCE[index % len(STATUS_SEQUENCE)]


def seed_tickets(limit: int = DEFAULT_LIMIT) -> int:
    with TICKETS_CSV.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))[:limit]

    inserted = 0
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        existing_ids = {ticket_id for (ticket_id,) in db.query(Ticket.ticket_id).all()}
        for index, row in enumerate(rows):
            if row["ticket_id"] in existing_ids:
                continue
            ticket = Ticket(
                ticket_id=row["ticket_id"],
                source_ticket_id=row.get("source_ticket_id") or None,
                title=row["title"][:255] or row["description"][:72],
                description=row["description"],
                service=row["service"],
                category=row["category"],
                raw_category=row.get("raw_category") or None,
                sub_category=row.get("sub_category") or None,
                priority=row["priority"],
                impact=row["impact"],
                urgency=row["urgency"],
                assigned_team=row.get("assigned_team") or None,
                auto_resolve=parse_bool(row.get("auto_resolve", "")),
                status=status_for_index(index),
                requester_email_redacted=row.get("requester_email_redacted") or "redacted",
                verified_root_cause=row.get("verified_root_cause") or None,
                resolution=row.get("resolution") or None,
                source=row.get("source") or "seed",
                created_at=now,
                updated_at=now,
            )
            db.add(ticket)
            inserted += 1
        db.commit()
    return inserted


if __name__ == "__main__":
    count = seed_tickets()
    print(f"Seeded {count} tickets from {TICKETS_CSV}")
