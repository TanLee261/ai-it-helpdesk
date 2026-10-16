from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
TICKETS_FILE = ROOT_DIR / "data" / "processed" / "tickets" / "normalized_tickets.csv"
RUNBOOK_DIR = ROOT_DIR / "data" / "processed" / "runbooks"
INCIDENTS_FILE = ROOT_DIR / "data" / "eval" / "incidents.jsonl"
LOGS_FILE = ROOT_DIR / "data" / "processed" / "logs" / "incident_logs.jsonl"
METRICS_FILE = ROOT_DIR / "data" / "processed" / "metrics" / "incident_metrics.csv"
EXPECTED_LOGS_PER_INCIDENT = 20
EXPECTED_METRICS_PER_INCIDENT = 10


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_ticket_ids() -> set[str]:
    with TICKETS_FILE.open("r", encoding="utf-8", newline="") as handle:
        return {row["ticket_id"] for row in csv.DictReader(handle)}


def load_metric_ids() -> set[str]:
    with METRICS_FILE.open("r", encoding="utf-8", newline="") as handle:
        return {row["metric_id"] for row in csv.DictReader(handle)}


def validate() -> int:
    errors: list[str] = []
    incidents = load_jsonl(INCIDENTS_FILE)
    logs = load_jsonl(LOGS_FILE)
    metrics = load_metric_ids()
    ticket_ids = load_ticket_ids()
    runbook_ids = {path.stem for path in RUNBOOK_DIR.glob("RB-*.md")}
    runbook_text = {path.stem: path.read_text(encoding="utf-8").casefold() for path in RUNBOOK_DIR.glob("RB-*.md")}
    log_ids = {row["log_id"] for row in logs}
    log_count_by_incident: dict[str, int] = {}
    metric_count_by_incident: dict[str, int] = {}
    for row in logs:
        incident_id = row.get("incident_id", "")
        log_count_by_incident[incident_id] = log_count_by_incident.get(incident_id, 0) + 1
    with METRICS_FILE.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            incident_id = row.get("incident_id", "")
            metric_count_by_incident[incident_id] = metric_count_by_incident.get(incident_id, 0) + 1

    if len(incidents) != 50:
        errors.append(f"expected 50 incidents, found {len(incidents)}")
    expected_log_count = len(incidents) * EXPECTED_LOGS_PER_INCIDENT
    if len(logs) != expected_log_count:
        errors.append(f"expected {expected_log_count} linked logs, found {len(logs)}")

    required_fields = {
        "incident_id",
        "category",
        "service",
        "symptoms",
        "event_window",
        "root_cause_label",
        "label_status",
        "ticket_ids",
        "log_evidence_ids",
        "metric_evidence_ids",
        "runbook_ids",
        "split",
    }

    for incident in incidents:
        missing = sorted(required_fields - set(incident))
        if missing:
            errors.append(f"{incident.get('incident_id', '<unknown>')}: missing {missing}")
            continue
        for ticket_id in incident["ticket_ids"]:
            if ticket_id not in ticket_ids:
                errors.append(f"{incident['incident_id']}: missing ticket {ticket_id}")
        for log_id in incident["log_evidence_ids"]:
            if log_id not in log_ids:
                errors.append(f"{incident['incident_id']}: missing log evidence {log_id}")
        if log_count_by_incident.get(incident["incident_id"], 0) != EXPECTED_LOGS_PER_INCIDENT:
            errors.append(
                f"{incident['incident_id']}: expected {EXPECTED_LOGS_PER_INCIDENT} linked logs, "
                f"found {log_count_by_incident.get(incident['incident_id'], 0)}"
            )
        if metric_count_by_incident.get(incident["incident_id"], 0) != EXPECTED_METRICS_PER_INCIDENT:
            errors.append(
                f"{incident['incident_id']}: expected {EXPECTED_METRICS_PER_INCIDENT} linked metrics, "
                f"found {metric_count_by_incident.get(incident['incident_id'], 0)}"
            )
        if incident["label_status"] != "synthetic_assumption_not_expert_verified":
            errors.append(f"{incident['incident_id']}: synthetic cause label must be marked unverified")
        for metric_id in incident["metric_evidence_ids"]:
            if metric_id not in metrics:
                errors.append(f"{incident['incident_id']}: missing metric evidence {metric_id}")
        for runbook_id in incident["runbook_ids"]:
            if runbook_id not in runbook_ids:
                errors.append(f"{incident['incident_id']}: missing runbook {runbook_id}")

        root_cause = incident["root_cause_label"].casefold()
        incident_logs = [row for row in logs if row.get("incident_id") == incident["incident_id"]]
        if any(root_cause in row.get("message", "").casefold() for row in incident_logs):
            errors.append(f"{incident['incident_id']}: root-cause label leaked into operational logs")
        if any(runbook_id in row.get("message", "") for row in incident_logs for runbook_id in incident["runbook_ids"]):
            errors.append(f"{incident['incident_id']}: expected runbook IDs leaked into operational logs")
        if any(root_cause in runbook_text.get(runbook_id, "") for runbook_id in incident["runbook_ids"]):
            errors.append(f"{incident['incident_id']}: exact synthetic cause label leaked into a linked runbook")

    if errors:
        print("Incident ground truth validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    split_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for incident in incidents:
        split_counts[incident["split"]] = split_counts.get(incident["split"], 0) + 1
        category_counts[incident["category"]] = category_counts.get(incident["category"], 0) + 1

    print(f"Incident validation passed: {len(incidents)} incidents")
    print(f"Split counts: {split_counts}")
    print(f"Category counts: {category_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate())
