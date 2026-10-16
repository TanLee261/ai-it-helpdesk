from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INCIDENTS_FILE = ROOT_DIR / "data/eval/incidents.jsonl"
REVIEW_FILE = ROOT_DIR / "data/eval/rca_review.csv"
FIELDS = [
    "incident_id", "split", "service", "ticket_id", "evidence_sufficiency",
    "sufficiency_rationale", "model_status", "probable_root_cause",
    "rca_correct", "fact_count", "unsupported_fact_count", "review_notes",
]


def read_incidents() -> list[dict]:
    with INCIDENTS_FILE.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def prepare() -> None:
    existing = {}
    if REVIEW_FILE.exists():
        with REVIEW_FILE.open(encoding="utf-8", newline="") as stream:
            existing = {row["incident_id"]: row for row in csv.DictReader(stream)}

    rows = []
    for incident in read_incidents():
        if incident["split"] != "test":
            continue
        row = existing.get(incident["incident_id"], {})
        rows.append({
            "incident_id": incident["incident_id"],
            "split": incident["split"],
            "service": incident["service"],
            "ticket_id": incident["ticket_ids"][0],
            "evidence_sufficiency": row.get("evidence_sufficiency", "unreviewed"),
            "sufficiency_rationale": row.get("sufficiency_rationale", ""),
            "model_status": row.get("model_status", ""),
            "probable_root_cause": row.get("probable_root_cause", ""),
            "rca_correct": row.get("rca_correct", ""),
            "fact_count": row.get("fact_count", ""),
            "unsupported_fact_count": row.get("unsupported_fact_count", ""),
            "review_notes": row.get("review_notes", ""),
        })
    REVIEW_FILE.parent.mkdir(parents=True, exist_ok=True)
    with REVIEW_FILE.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Prepared {len(rows)} test-incident review rows at {REVIEW_FILE}")


def evaluate() -> None:
    with REVIEW_FILE.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))

    reviewed_sufficiency = [row for row in rows if row["evidence_sufficiency"] in {"sufficient", "insufficient"}]
    insufficient = [
        row for row in reviewed_sufficiency
        if row["evidence_sufficiency"] == "insufficient" and row["model_status"].strip()
    ]
    abstained = [row for row in insufficient if row["model_status"] == "insufficient_evidence"]
    sufficient = [row for row in reviewed_sufficiency if row["evidence_sufficiency"] == "sufficient"]
    rca_reviewed = [row for row in sufficient if row["rca_correct"].lower() in {"yes", "no"}]

    fact_rows = [row for row in rows if row["fact_count"].strip() and row["unsupported_fact_count"].strip()]
    fact_count = sum(int(row["fact_count"]) for row in fact_rows)
    unsupported_count = sum(int(row["unsupported_fact_count"]) for row in fact_rows)
    metrics = {
        "test_incidents": len(rows),
        "reviewed_evidence_sufficiency": len(reviewed_sufficiency),
        "correct_abstention_rate": {
            "value": len(abstained) / len(insufficient) if insufficient else None,
            "numerator": len(abstained), "denominator": len(insufficient),
        },
        "rca_accuracy_on_sufficient_evidence": {
            "value": sum(row["rca_correct"].lower() == "yes" for row in rca_reviewed) / len(rca_reviewed) if rca_reviewed else None,
            "numerator": sum(row["rca_correct"].lower() == "yes" for row in rca_reviewed),
            "denominator": len(rca_reviewed),
        },
        "unsupported_fact_rate": {
            "value": unsupported_count / fact_count if fact_count else None,
            "numerator": unsupported_count, "denominator": fact_count,
        },
        "sufficiency_label_counts": dict(Counter(row["evidence_sufficiency"] for row in rows)),
        "note": "Manual review required; null means there is not enough reviewed data to calculate the metric.",
    }
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare and score manual RCA evaluation labels.")
    parser.add_argument("command", choices=["prepare", "evaluate"])
    args = parser.parse_args()
    prepare() if args.command == "prepare" else evaluate()
