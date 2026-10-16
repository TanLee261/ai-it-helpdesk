from __future__ import annotations

import csv
import json
import argparse
from collections import Counter, defaultdict
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INCIDENTS_FILE = ROOT_DIR / "data" / "eval" / "incidents.jsonl"
EVAL_JSONL = ROOT_DIR / "data" / "eval" / "evaluation_queries.jsonl"
EVAL_CSV = ROOT_DIR / "data" / "eval" / "evaluation_queries.csv"
TICKETS_FILE = ROOT_DIR / "data" / "processed" / "tickets" / "normalized_tickets.csv"
RUNBOOK_DIR = ROOT_DIR / "data" / "processed" / "runbooks"
LOGS_FILE = ROOT_DIR / "data" / "processed" / "logs" / "incident_logs.jsonl"
METRICS_FILE = ROOT_DIR / "data" / "processed" / "metrics" / "incident_metrics.csv"


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_csv_ids(path: Path, column: str) -> set[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row[column] for row in csv.DictReader(handle)}


def read_split_assignments(path: Path | None) -> dict[str, str] | None:
    if path is None:
        return None
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row["incident_id"]: row["split"] for row in csv.DictReader(handle)}


def validate(eval_jsonl: Path = EVAL_JSONL, eval_csv: Path = EVAL_CSV, split_file: Path | None = None) -> int:
    errors: list[str] = []
    incidents = load_jsonl(INCIDENTS_FILE)
    queries = load_jsonl(eval_jsonl)
    split_assignments = read_split_assignments(split_file)

    ticket_ids = load_csv_ids(TICKETS_FILE, "ticket_id")
    runbook_ids = {path.stem for path in RUNBOOK_DIR.glob("RB-*.md")}
    log_ids = {row["log_id"] for row in load_jsonl(LOGS_FILE)}
    metric_ids = load_csv_ids(METRICS_FILE, "metric_id")
    evidence_ids = ticket_ids | runbook_ids | log_ids | metric_ids
    incident_by_id = {incident["incident_id"]: incident for incident in incidents}

    if not eval_csv.exists():
        errors.append(f"missing CSV copy {eval_csv}")
    if len(queries) < 100 or len(queries) > 150:
        errors.append(f"expected 100-150 queries, found {len(queries)}")

    query_ids = [query.get("eval_id", "") for query in queries]
    duplicates = [eval_id for eval_id, count in Counter(query_ids).items() if count > 1]
    if duplicates:
        errors.append(f"duplicate eval_id values: {duplicates[:5]}")

    query_count_by_incident: dict[str, int] = defaultdict(int)
    split_by_incident: dict[str, set[str]] = defaultdict(set)
    query_type_counter: Counter[str] = Counter()

    required_fields = {
        "eval_id",
        "incident_id",
        "query_type",
        "question",
        "service",
        "category",
        "split",
        "relevant_ticket_ids",
        "runbook_ids",
        "log_evidence_ids",
        "metric_evidence_ids",
        "evidence_ids",
        "expected_root_cause",
    }

    for query in queries:
        missing = sorted(required_fields - set(query))
        if missing:
            errors.append(f"{query.get('eval_id', '<unknown>')}: missing {missing}")
            continue

        incident = incident_by_id.get(query["incident_id"])
        if incident is None:
            errors.append(f"{query['eval_id']}: incident_id does not exist: {query['incident_id']}")
            continue

        query_count_by_incident[query["incident_id"]] += 1
        split_by_incident[query["incident_id"]].add(query["split"])
        query_type_counter[query["query_type"]] += 1

        expected_split = (
            split_assignments.get(query["incident_id"])
            if split_assignments is not None
            else incident["split"]
        )
        if expected_split is None:
            errors.append(f"{query['eval_id']}: incident missing from supplied split file")
        elif query["split"] != expected_split:
            errors.append(f"{query['eval_id']}: split does not match selected split file")
        if split_assignments is not None and query["incident_id"] in query["question"]:
            errors.append(f"{query['eval_id']}: question contains incident ID")
        if query["expected_root_cause"] != incident["root_cause_label"]:
            errors.append(f"{query['eval_id']}: expected_root_cause does not match incident")
        if query["expected_root_cause"].lower() in query["question"].lower():
            errors.append(f"{query['eval_id']}: question leaks expected root cause")

        for field in ["relevant_ticket_ids", "runbook_ids", "log_evidence_ids", "metric_evidence_ids", "evidence_ids"]:
            values = query.get(field, [])
            if not isinstance(values, list) or not values:
                errors.append(f"{query['eval_id']}: {field} must be a non-empty list")
                continue
            for value in values:
                if value not in evidence_ids:
                    errors.append(f"{query['eval_id']}: unknown evidence id {value}")

    for incident_id, count in query_count_by_incident.items():
        if count != 3:
            errors.append(f"{incident_id}: expected 3 evaluation queries, found {count}")
    for incident_id, splits in split_by_incident.items():
        if len(splits) != 1:
            errors.append(f"{incident_id}: queries span multiple splits {sorted(splits)}")

    if errors:
        print("Evaluation set validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    split_counts = Counter(query["split"] for query in queries)
    print(f"Evaluation validation passed: {len(queries)} queries")
    print(f"Split counts: {dict(split_counts)}")
    print(f"Query type counts: {dict(query_type_counter)}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate evaluation query files and evidence references.")
    parser.add_argument("--eval-jsonl", type=Path, default=EVAL_JSONL)
    parser.add_argument("--eval-csv", type=Path, default=EVAL_CSV)
    parser.add_argument("--split-file", type=Path)
    args = parser.parse_args()
    raise SystemExit(validate(args.eval_jsonl, args.eval_csv, args.split_file))
