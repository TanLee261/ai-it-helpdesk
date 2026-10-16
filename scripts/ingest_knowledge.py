from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from app.ingestion.pipeline import ingest_all, ingest_runbooks, ingest_tickets  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest tickets and runbooks into knowledge tables.")
    parser.add_argument(
        "--source",
        choices=["tickets", "runbooks", "all"],
        default="all",
        help="Knowledge source to ingest.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Ticket limit for tickets/all ingestion. Use 0 to ingest all tickets.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ticket_limit = None if args.limit == 0 else args.limit
    with SessionLocal() as db:
        if args.source == "tickets":
            result = ingest_tickets(db, limit=ticket_limit)
        elif args.source == "runbooks":
            result = ingest_runbooks(db)
        else:
            result = ingest_all(db, ticket_limit=ticket_limit)

    print(
        "Ingested "
        f"{result.documents_upserted} documents, "
        f"{result.chunks_upserted} chunks "
        f"from {result.documents_seen} input documents."
    )


if __name__ == "__main__":
    main()
