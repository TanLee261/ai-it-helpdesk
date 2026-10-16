from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INCIDENTS_FILE = ROOT_DIR / "data/eval/incidents.jsonl"
SPLITS_FILE = ROOT_DIR / "data/eval/benchmark_v2_splits.csv"
TICKETS_FILE = ROOT_DIR / "data/processed/tickets/normalized_tickets.csv"
LOGS_FILE = ROOT_DIR / "data/processed/logs/incident_logs.jsonl"
METRICS_FILE = ROOT_DIR / "data/processed/metrics/incident_metrics.csv"
RUNBOOK_DIR = ROOT_DIR / "data/processed/runbooks"
OUTPUT_FILE = ROOT_DIR / "data/eval/incident_evidence_review_v3.csv"

REVIEW_FIELDS = [
    "evidence_review_status",
    "ticket_link_valid",
    "service_match",
    "symptom_match",
    "runbook_relevant",
    "logs_valid",
    "metrics_valid",
    "evidence_sufficiency",
    "reviewed_root_cause",
    "verified_evidence_ids",
    "review_rationale",
    "reviewed_by",
    "reviewed_at",
]
FIELDS = [
    "incident_id", "legacy_split", "v2_split", "category", "service", "ticket_id",
    "reported_symptoms", "event_window", "ticket_service", "ticket_category",
    "ticket_title", "ticket_description", "runbook_ids", "runbook_titles",
    "in_window_log_count", "in_window_log_ids", "log_examples",
    "in_window_metric_count", "in_window_metric_ids", "metric_samples",
    "log_provenance", "log_evidence_scope", "metric_provenance", "metric_evidence_scope",
    *REVIEW_FIELDS,
]


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def runbook_title(document_id: str) -> str:
    path = RUNBOOK_DIR / f"{document_id}.md"
    if not path.exists():
        return "[MISSING]"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "[TITLE MISSING]"


def load_previous_reviews(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    return {
        row["incident_id"]: row
        for row in read_csv(path)
        if row.get("incident_id")
    }


def build_rows(previous_path: Path) -> list[dict[str, str]]:
    incidents = read_jsonl(INCIDENTS_FILE)
    tickets = {row["ticket_id"]: row for row in read_csv(TICKETS_FILE)}
    logs = read_jsonl(LOGS_FILE)
    metrics = read_csv(METRICS_FILE)
    splits = {row["incident_id"]: row["split"] for row in read_csv(SPLITS_FILE)} if SPLITS_FILE.exists() else {}
    previous = load_previous_reviews(previous_path)

    logs_by_incident: dict[str, list[dict]] = {}
    for row in logs:
        logs_by_incident.setdefault(row.get("incident_id", ""), []).append(row)
    metrics_by_incident: dict[str, list[dict[str, str]]] = {}
    for row in metrics:
        metrics_by_incident.setdefault(row.get("incident_id", ""), []).append(row)

    rows = []
    for incident in sorted(incidents, key=lambda row: (row["category"], row["incident_id"])):
        incident_id = incident["incident_id"]
        ticket_id = incident.get("ticket_ids", [""])[0]
        ticket = tickets.get(ticket_id, {})
        window_start, window_end = map(parse_time, incident["event_window"].split("/"))
        incident_logs = [
            row for row in logs_by_incident.get(incident_id, [])
            if row.get("service") == incident.get("service")
            and window_start <= parse_time(row["timestamp"]) <= window_end
        ]
        incident_metrics = [
            row for row in metrics_by_incident.get(incident_id, [])
            if row.get("service") == incident.get("service")
            and window_start <= parse_time(row["timestamp"]) <= window_end
        ]
        runbook_ids = incident.get("runbook_ids", [])
        log_examples = [
            f"{row['timestamp']} [{row.get('level', '')}] {row.get('message', '')}"
            for row in incident_logs[:3]
        ]
        metric_samples = [
            f"{row['timestamp']} {row['metric_name']}={row['value']} {row.get('unit', '')} "
            f"(anomaly={row.get('is_anomaly', '')}, phase={row.get('phase', '')})"
            for row in incident_metrics[:8]
        ]
        base = {
            "incident_id": incident_id,
            "legacy_split": incident.get("split", ""),
            "v2_split": splits.get(incident_id, ""),
            "category": incident.get("category", ""),
            "service": incident.get("service", ""),
            "ticket_id": ticket_id,
            "reported_symptoms": incident.get("symptoms", ""),
            "event_window": incident.get("event_window", ""),
            "ticket_service": ticket.get("service", ""),
            "ticket_category": ticket.get("category", ""),
            "ticket_title": ticket.get("title", "[MISSING TICKET]"),
            "ticket_description": ticket.get("description", ""),
            "runbook_ids": "|".join(runbook_ids),
            "runbook_titles": "|".join(runbook_title(doc_id) for doc_id in runbook_ids),
            "in_window_log_count": str(len(incident_logs)),
            "in_window_log_ids": "|".join(row["log_id"] for row in incident_logs),
            "log_examples": "\n".join(log_examples),
            "in_window_metric_count": str(len(incident_metrics)),
            "in_window_metric_ids": "|".join(row["metric_id"] for row in incident_metrics),
            "metric_samples": "\n".join(metric_samples),
            "log_provenance": "synthetic_template_generated",
            "log_evidence_scope": "Generic service-health, latency, retry, and error signals; not independently observed or root-cause-specific.",
            "metric_provenance": "synthetic_service_profile_generated",
            "metric_evidence_scope": "Generated metric profile tied to the scenario service; supports a simulated anomaly pattern, not independent operational confirmation.",
        }
        old_review = previous.get(incident_id, {})
        for field in REVIEW_FIELDS:
            default = "unreviewed" if field in {"evidence_review_status", "evidence_sufficiency"} else ""
            base[field] = old_review.get(field, default)
        rows.append(base)
    return rows


def prepare(output: Path = OUTPUT_FILE) -> int:
    rows = build_rows(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Prepared blind evidence review: {len(rows)} incidents -> {output}")
    print("Root-cause labels and model predictions are intentionally omitted; review evidence before assigning a cause.")
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare a blind evidence review sheet without root-cause labels.")
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE)
    args = parser.parse_args()
    prepare(args.output)
