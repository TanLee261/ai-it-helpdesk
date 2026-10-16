from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INCIDENTS_FILE = ROOT_DIR / "data/eval/incidents.jsonl"
SPLITS_FILE = ROOT_DIR / "data/eval/benchmark_v2_splits.csv"
REVIEW_FILE = ROOT_DIR / "data/eval/benchmark_v2_review.csv"
SEED = 20261014
SPLIT_FIELDS = ["incident_id", "category", "service", "ticket_id", "split"]
REVIEW_FIELDS = [
    "incident_id", "category", "service", "ticket_id", "split",
    "evidence_sufficiency", "sufficiency_rationale", "model_status",
    "probable_root_cause", "rca_correct", "fact_count",
    "unsupported_fact_count", "review_notes",
]


def load_incidents() -> list[dict]:
    with INCIDENTS_FILE.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def stratified_assignments(incidents: list[dict]) -> dict[str, str]:
    rng = random.Random(SEED)
    assignments: dict[str, str] = {}
    by_category: dict[str, list[dict]] = {}
    for incident in incidents:
        by_category.setdefault(incident["category"], []).append(incident)

    for category, group in sorted(by_category.items()):
        shuffled = sorted(group, key=lambda item: item["incident_id"])
        rng.shuffle(shuffled)
        size = len(shuffled)
        counts = {
            "train": round(size * 0.70),
            "dev": round(size * 0.15),
        }
        counts["test"] = size - counts["train"] - counts["dev"]
        cursor = 0
        for split in ("train", "dev", "test"):
            for incident in shuffled[cursor:cursor + counts[split]]:
                assignments[incident["incident_id"]] = split
            cursor += counts[split]
    return assignments


def prepare(force: bool = False) -> None:
    if not force and (SPLITS_FILE.exists() or REVIEW_FILE.exists()):
        raise SystemExit(
            "V2 benchmark files already exist; refusing to overwrite them. "
            "Archive your review or rerun with --force to regenerate."
        )
    incidents = load_incidents()
    assignments = stratified_assignments(incidents)
    split_rows = []
    review_rows = []
    for incident in sorted(incidents, key=lambda item: item["incident_id"]):
        split = assignments[incident["incident_id"]]
        common = {
            "incident_id": incident["incident_id"],
            "category": incident["category"],
            "service": incident["service"],
            "ticket_id": incident["ticket_ids"][0],
            "split": split,
        }
        split_rows.append(common)
        if split == "test":
            review_rows.append({
                **common,
                "evidence_sufficiency": "unreviewed",
                "sufficiency_rationale": "",
                "model_status": "",
                "probable_root_cause": "",
                "rca_correct": "",
                "fact_count": "",
                "unsupported_fact_count": "",
                "review_notes": "",
            })

    SPLITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SPLITS_FILE.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=SPLIT_FIELDS)
        writer.writeheader()
        writer.writerows(split_rows)
    with REVIEW_FILE.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(review_rows)

    counts = Counter(row["split"] for row in split_rows)
    by_split_category = Counter((row["split"], row["category"]) for row in split_rows)
    print(json.dumps({
        "seed": SEED,
        "incidents": len(split_rows),
        "split_counts": dict(counts),
        "category_by_split": {f"{split}/{category}": count for (split, category), count in sorted(by_split_category.items())},
        "test_review_rows": len(review_rows),
        "split_file": str(SPLITS_FILE),
        "review_file": str(REVIEW_FILE),
        "note": "Existing incidents and legacy review were not modified; V2 review starts unreviewed to avoid carrying labels across changed test membership.",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare a deterministic, category-stratified RCA benchmark split.")
    parser.add_argument("--force", action="store_true", help="Overwrite V2 split and review files (destroys V2 manual annotations).")
    args = parser.parse_args()
    prepare(force=args.force)
