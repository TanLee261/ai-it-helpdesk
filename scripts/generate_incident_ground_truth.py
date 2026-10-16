from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
TICKETS_FILE = ROOT_DIR / "data" / "processed" / "tickets" / "normalized_tickets.csv"
ERROR_DESCRIPTIONS_FILE = ROOT_DIR / "data" / "processed" / "tickets" / "error_descriptions.csv"
RUNBOOK_DIR = ROOT_DIR / "data" / "processed" / "runbooks"
INCIDENTS_FILE = ROOT_DIR / "data" / "eval" / "incidents.jsonl"
LOGS_FILE = ROOT_DIR / "data" / "processed" / "logs" / "incident_logs.jsonl"
METRICS_FILE = ROOT_DIR / "data" / "processed" / "metrics" / "incident_metrics.csv"
LOG_EVENTS_PER_INCIDENT = 20
METRIC_ROWS_PER_INCIDENT = 10


TARGET_BY_CATEGORY = {
    "network": 17,
    "server_api": 17,
    "database": 16,
}


# Scenario labels are synthetic assumptions and must never be treated as verified RCA.
ROOT_CAUSE_BY_SERVICE = {
    "edge-gateway": "edge gateway saturation causing intermittent connectivity",
    "file-server": "network share permission or mount failure",
    "dns-service": "stale DNS resolver cache or failed upstream lookup",
    "vpn-gateway": "VPN tunnel authentication or profile mismatch",
    "proxy-service": "proxy rule or certificate inspection failure",
    "endpoint-device": "endpoint device driver, firmware, or hardware malfunction",
    "auth-service": "identity provider policy mismatch or account lock",
    "customer-api": "application configuration regression causing request failures",
    "notification-api": "notification provider authentication or rate limit failure",
    "payment-api": "payment API dependency failure",
    "primary-db": "primary database storage or transaction failure",
    "reporting-db": "reporting database resource saturation",
    "customer-db": "customer database consistency or lookup failure",
    "backup-service": "backup job failure or snapshot retention issue",
}


METRIC_BY_SERVICE = {
    "edge-gateway": ("packet_loss_percent", 18.5, "percent"),
    "file-server": ("share_mount_error_rate", 22.0, "percent"),
    "dns-service": ("dns_lookup_failure_rate", 16.0, "percent"),
    "vpn-gateway": ("vpn_tunnel_failure_rate", 19.0, "percent"),
    "proxy-service": ("proxy_5xx_rate", 12.5, "percent"),
    "endpoint-device": ("device_error_count", 12.0, "count"),
    "auth-service": ("auth_failure_rate", 14.0, "percent"),
    "customer-api": ("api_error_rate", 11.5, "percent"),
    "notification-api": ("notification_delivery_failure_rate", 13.0, "percent"),
    "payment-api": ("payment_error_rate", 12.0, "percent"),
    "primary-db": ("db_storage_error_rate", 9.0, "percent"),
    "reporting-db": ("db_cpu_utilization", 96.0, "percent"),
    "customer-db": ("db_lookup_error_rate", 8.5, "percent"),
    "backup-service": ("backup_job_failure_count", 7.0, "count"),
}


def read_tickets() -> list[dict]:
    with TICKETS_FILE.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_error_descriptions_by_service() -> dict[str, list[dict]]:
    descriptions: dict[str, list[dict]] = defaultdict(list)
    with ERROR_DESCRIPTIONS_FILE.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if is_incident_text(row.get("description", "")):
                descriptions[row["service"]].append(row)
    return descriptions


def is_incident_text(text: str) -> bool:
    lowered = text.lower()
    if "user_input_text" in lowered:
        return False
    informational_phrases = [
        "learn more",
        "seek information",
        "provide more information",
        "recommended security measures",
        "securing medical data",
        "need to ensure compliance",
        "seek advice",
        "writing to seek",
        "i am writing to seek",
        "brand engagement",
        "online footprint",
        "marketing firm",
        "strategies such as",
        "latest trends",
        "established practices",
        "interested in learning",
        "could boost",
        "could you provide",
        "could you offer",
        "advice on this topic",
    ]
    if any(phrase in lowered for phrase in informational_phrases):
        return False
    incident_terms = [
        "issue",
        "problem",
        "error",
        "failure",
        "failing",
        "unable",
        "cannot",
        "not working",
        "expired",
        "slow",
        "down",
        "locked",
        "reset",
        "connectivity",
        "data loss",
        "crash",
        "timeout",
        "vpn",
        "wifi",
        "login",
        "password",
        "printer",
        "performance",
    ]
    return any(term in lowered for term in incident_terms)


def is_incident_candidate(ticket: dict) -> bool:
    text = f"{ticket.get('title', '')} {ticket.get('description', '')}".lower()
    return is_incident_text(text)


def table_value(content: str, key: str) -> str:
    pattern = rf"^\| {re.escape(key)} \| (?P<value>.+?) \|$"
    match = re.search(pattern, content, flags=re.MULTILINE)
    return match.group("value").strip() if match else ""


def load_runbooks_by_service() -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for path in sorted(RUNBOOK_DIR.glob("RB-*.md")):
        content = path.read_text(encoding="utf-8")
        service = table_value(content, "service")
        if service:
            result[service].append(path.stem)
    return result


def select_tickets(tickets: list[dict]) -> list[dict]:
    selected: list[dict] = []
    used_ids: set[str] = set()

    for category, target in TARGET_BY_CATEGORY.items():
        category_tickets = [
            ticket
            for ticket in tickets
            if ticket["category"] == category and is_incident_candidate(ticket)
        ]
        by_service: dict[str, list[dict]] = defaultdict(list)
        for ticket in category_tickets:
            by_service[ticket["service"]].append(ticket)

        services = sorted(by_service, key=lambda service: (-len(by_service[service]), service))
        index_by_service = {service: 0 for service in services}

        while len([ticket for ticket in selected if ticket["category"] == category]) < target:
            progressed = False
            for service in services:
                service_rows = by_service[service]
                cursor = index_by_service[service]
                if cursor >= len(service_rows):
                    continue
                ticket = service_rows[cursor]
                index_by_service[service] += 1
                if ticket["ticket_id"] in used_ids:
                    continue
                selected.append(ticket)
                used_ids.add(ticket["ticket_id"])
                progressed = True
                if len([item for item in selected if item["category"] == category]) >= target:
                    break
            if not progressed:
                raise RuntimeError(f"Not enough tickets for category {category}")

    return selected


def incident_split(index: int) -> str:
    if index <= 35:
        return "train"
    if index <= 42:
        return "dev"
    return "test"


def make_event_window(index: int) -> tuple[str, str]:
    start = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc) + timedelta(hours=index * 3)
    end = start + timedelta(minutes=15)
    return start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z")


def evidence_ids(incident_index: int) -> tuple[list[str], list[str]]:
    return (
        [f"LOG-{incident_index:04d}-{event_index:03d}" for event_index in range(1, LOG_EVENTS_PER_INCIDENT + 1)],
        [f"MET-{incident_index:04d}-{metric_index:03d}" for metric_index in range(1, METRIC_ROWS_PER_INCIDENT + 1)],
    )


def build_log_events(incident: dict) -> list[dict]:
    service = incident["service"]
    start_text = incident["event_window"].split("/")[0]
    start = datetime.fromisoformat(start_text.replace("Z", "+00:00"))
    log_ids = incident["log_evidence_ids"]
    templates = [
        ("INFO", f"{service} health probe completed"),
        ("INFO", f"{service} request volume recorded before alert window"),
        ("WARN", f"{service} response time increased above recent baseline"),
        ("WARN", f"{service} retry count increased for an affected request"),
        ("ERROR", f"{service} request returned an error response"),
        ("WARN", f"{service} dependent request completed more slowly than baseline"),
        ("ERROR", f"{service} repeated request failure observed"),
        ("ERROR", f"{service} health check returned a degraded status"),
        ("INFO", f"{service} diagnostic counters collected"),
        ("WARN", f"{service} retry activity continued"),
        ("INFO", f"{service} deployment history check requested"),
        ("WARN", f"{service} error rate remained above baseline"),
        ("ERROR", f"{service} request timeout observed"),
        ("INFO", f"{service} upstream health check completed"),
        ("WARN", f"{service} response latency remained elevated"),
        ("ERROR", f"{service} additional request failure observed"),
        ("INFO", f"{service} technician review requested"),
        ("WARN", f"{service} service health remains degraded"),
        ("INFO", f"{service} diagnostic collection completed"),
        ("INFO", f"{service} monitoring window closed"),
    ]
    events: list[dict] = []
    for offset, (level, message) in enumerate(templates):
        timestamp = start + timedelta(seconds=offset * 35)
        events.append(
            {
                "log_id": log_ids[offset],
                "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
                "service": service,
                "level": level,
                "incident_id": incident["incident_id"],
                "message": message,
            }
        )
    return events


def build_metric_rows(incident: dict) -> list[dict]:
    service = incident["service"]
    metric_name, anomalous_value, unit = METRIC_BY_SERVICE.get(service, ("error_rate", 10.0, "percent"))
    start = datetime.fromisoformat(incident["event_window"].split("/")[0].replace("Z", "+00:00"))
    metric_ids = incident["metric_evidence_ids"]
    samples = [
        ("baseline", -15, metric_name, anomalous_value * 0.25, unit, False),
        ("baseline", -10, "latency_p95_ms", 420.0, "ms", False),
        ("baseline", -5, metric_name, anomalous_value * 0.45, unit, False),
        ("anomaly_ramp", 0, metric_name, anomalous_value * 0.85, unit, True),
        ("anomaly_ramp", 3, "latency_p95_ms", 2100.0, "ms", True),
        ("peak_anomaly", 6, metric_name, anomalous_value, unit, True),
        ("peak_anomaly", 9, "latency_p95_ms", 4200.0, "ms", True),
        ("recovery_start", 12, metric_name, anomalous_value * 0.75, unit, True),
        ("recovery", 17, "latency_p95_ms", 1200.0, "ms", False),
        ("recovery", 22, metric_name, anomalous_value * 0.35, unit, False),
    ]
    return [
        {
            "metric_id": metric_ids[index],
            "timestamp": (start + timedelta(minutes=offset)).isoformat().replace("+00:00", "Z"),
            "service": service,
            "incident_id": incident["incident_id"],
            "metric_name": name,
            "value": round(value, 3),
            "unit": sample_unit,
            "is_anomaly": str(is_anomaly).lower(),
            "phase": phase,
        }
        for index, (phase, offset, name, value, sample_unit, is_anomaly) in enumerate(samples)
    ]


def generate() -> tuple[int, int, int]:
    tickets = read_tickets()
    descriptions_by_service = read_error_descriptions_by_service()
    runbooks_by_service = load_runbooks_by_service()
    selected = select_tickets(tickets)

    INCIDENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)

    incidents: list[dict] = []
    log_events: list[dict] = []
    metric_rows: list[dict] = []

    for index, ticket in enumerate(selected, start=1):
        incident_id = f"INC-{index:04d}"
        start, end = make_event_window(index)
        log_ids, metric_ids = evidence_ids(index)
        service = ticket["service"]
        matching_descriptions = descriptions_by_service.get(service, [])
        description = matching_descriptions[(index - 1) % len(matching_descriptions)] if matching_descriptions else None
        runbook_ids = runbooks_by_service.get(service, [])
        if not runbook_ids:
            runbook_ids = ["RB-API-001"] if ticket["category"] == "server_api" else ["RB-NET-001"]

        incident = {
            "incident_id": incident_id,
            "category": ticket["category"],
            "raw_category": ticket["raw_category"],
            "sub_category": description["sub_category"] if description else ticket["sub_category"],
            "service": service,
            "symptoms": description["description"] if description else ticket["description"],
            "event_window": f"{start}/{end}",
            "source": "synthetic_assumption_generated_from_helpdesk_ticket",
            "root_cause_label": ROOT_CAUSE_BY_SERVICE.get(service, "service degradation requiring technician validation"),
            "label_status": "synthetic_assumption_not_expert_verified",
            "ticket_ids": [ticket["ticket_id"]],
            "description_ids": [description["description_id"]] if description else [],
            "log_evidence_ids": log_ids,
            "metric_evidence_ids": metric_ids,
            "runbook_ids": runbook_ids[:2],
            "split": incident_split(index),
        }
        incidents.append(incident)
        log_events.extend(build_log_events(incident))
        metric_rows.extend(build_metric_rows(incident))

    with INCIDENTS_FILE.open("w", encoding="utf-8") as handle:
        for incident in incidents:
            handle.write(json.dumps(incident, ensure_ascii=False) + "\n")

    with LOGS_FILE.open("w", encoding="utf-8") as handle:
        for event in log_events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    with METRICS_FILE.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["metric_id", "timestamp", "service", "incident_id", "metric_name", "value", "unit", "is_anomaly", "phase"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metric_rows)

    return len(incidents), len(log_events), len(metric_rows)


if __name__ == "__main__":
    incident_count, log_count, metric_count = generate()
    print(f"Generated {incident_count} incidents -> {INCIDENTS_FILE}")
    print(f"Generated {log_count} linked log evidence events -> {LOGS_FILE}")
    print(f"Generated {metric_count} linked metric evidence rows -> {METRICS_FILE}")
