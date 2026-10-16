from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INCIDENTS_FILE = ROOT_DIR / "data/eval/incidents.jsonl"
TICKETS_FILE = ROOT_DIR / "data/processed/tickets/normalized_tickets.csv"
LOGS_FILE = ROOT_DIR / "data/processed/logs/incident_logs.jsonl"
METRICS_FILE = ROOT_DIR / "data/processed/metrics/incident_metrics.csv"
OUTPUT_FILE = ROOT_DIR / "data/eval/incident_link_audit.csv"
TOKEN_RE = re.compile(r"[a-z0-9]+")
PLACEHOLDER = ("user_input_text", "<redacted>", "placeholder")


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def token_overlap(left: str, right: str) -> float:
    left_tokens = set(TOKEN_RE.findall(left.lower()))
    right_tokens = set(TOKEN_RE.findall(right.lower()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def audit() -> list[dict]:
    incidents = read_jsonl(INCIDENTS_FILE)
    logs = read_jsonl(LOGS_FILE)
    with TICKETS_FILE.open(encoding="utf-8", newline="") as stream:
        tickets = {row["ticket_id"]: row for row in csv.DictReader(stream)}
    with METRICS_FILE.open(encoding="utf-8", newline="") as stream:
        metrics = list(csv.DictReader(stream))
    previous_reviews = {}
    if OUTPUT_FILE.exists():
        with OUTPUT_FILE.open(encoding="utf-8", newline="") as stream:
            previous_reviews = {row["incident_id"]: row for row in csv.DictReader(stream)}

    logs_by_incident: dict[str, list[dict]] = defaultdict(list)
    for log in logs:
        logs_by_incident[log.get("incident_id", "")].append(log)

    rows = []
    label_count_by_service: dict[str, Counter] = defaultdict(Counter)
    for incident in incidents:
        label_count_by_service[incident["service"]][incident["root_cause_label"]] += 1

    for incident in incidents:
        ticket_id = incident.get("ticket_ids", [""])[0]
        ticket = tickets.get(ticket_id, {})
        ticket_text = f"{ticket.get('title', '')} {ticket.get('description', '')}"
        symptoms = incident.get("symptoms", "")
        overlap = token_overlap(symptoms, ticket_text)
        window_start, window_end = map(parse_time, incident["event_window"].split("/"))

        incident_logs = logs_by_incident.get(incident["incident_id"], [])
        valid_logs = [
            row for row in incident_logs
            if row.get("service") == incident.get("service")
            and window_start <= parse_time(row["timestamp"]) <= window_end
        ]
        incident_metrics = [
            row for row in metrics
            if row.get("service") == incident.get("service")
            and window_start <= parse_time(row["timestamp"]) <= window_end
        ]
        flags = []
        if not ticket:
            flags.append("ticket_missing")
        if ticket and ticket.get("service") != incident.get("service"):
            flags.append("ticket_service_metadata_mismatch")
        if ticket and ticket.get("category") != incident.get("category"):
            flags.append("ticket_category_metadata_mismatch")
        if any(marker in ticket_text.casefold() for marker in PLACEHOLDER):
            flags.append("placeholder_ticket_text")
        if overlap < 0.03:
            flags.append("low_ticket_symptom_overlap_review_required")
        if len(valid_logs) != len(incident_logs):
            flags.append("log_service_or_window_mismatch")
        if not incident_metrics:
            flags.append("no_in_window_metric")
        if len(label_count_by_service[incident["service"]]) == 1:
            flags.append("cause_label_constant_for_service")

        review = previous_reviews.get(incident["incident_id"], {})
        rows.append({
            "incident_id": incident["incident_id"],
            "legacy_split": incident.get("split", ""),
            "category": incident.get("category", ""),
            "service": incident.get("service", ""),
            "ticket_id": ticket_id,
            "ticket_service": ticket.get("service", ""),
            "ticket_category": ticket.get("category", ""),
            "ticket_symptom_jaccard": round(overlap, 4),
            "log_count": len(incident_logs),
            "valid_log_service_window_count": len(valid_logs),
            "in_window_metric_count": len(incident_metrics),
            "in_window_metric_names": "|".join(sorted({row["metric_name"] for row in incident_metrics})),
            "label_status": incident.get("label_status", ""),
            "audit_flags": "|".join(flags),
            "review_decision": review.get("review_decision", "unreviewed"),
            "reviewed_by": review.get("reviewed_by", ""),
            "review_rationale": review.get("review_rationale", ""),
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter(flag for row in rows for flag in row["audit_flags"].split("|") if flag)
    print(json.dumps({
        "incidents_audited": len(rows),
        "flag_counts": dict(counts),
        "audit_file": str(OUTPUT_FILE),
        "warning": "Flags are review cues, not automatic exclusions or ground-truth decisions. Token overlap is only a heuristic.",
    }, ensure_ascii=False, indent=2))
    return rows


if __name__ == "__main__":
    audit()
