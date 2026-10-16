from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
TICKETS_FILE = ROOT_DIR / "data/processed/tickets/normalized_tickets.csv"
SCENARIOS_FILE = ROOT_DIR / "data/specs/ticket_telemetry_scenarios.json"
OUTPUT_DIR = ROOT_DIR / "data/synthetic/telemetry-v1"
PROVENANCE = "synthetic_ticket_informed"
BASE_START = datetime(2026, 10, 16, 3, 0, tzinfo=timezone.utc)


def load_tickets() -> dict[str, dict[str, str]]:
    with TICKETS_FILE.open(encoding="utf-8-sig", newline="") as stream:
        return {row["ticket_id"]: row for row in csv.DictReader(stream)}


def load_scenarios() -> list[dict]:
    return json.loads(SCENARIOS_FILE.read_text(encoding="utf-8"))


def validate_scenarios(scenarios: list[dict], tickets: dict[str, dict[str, str]]) -> None:
    seen: set[str] = set()
    for scenario in scenarios:
        ticket_id = scenario["ticket_id"]
        if ticket_id in seen:
            raise ValueError(f"Duplicate ticket in scenario specs: {ticket_id}")
        seen.add(ticket_id)
        ticket = tickets.get(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket not found: {ticket_id}")
        if not scenario["required_terms"] or not any(
            term.casefold() in f"{ticket['title']} {ticket['description']}".casefold()
            for term in scenario["required_terms"]
        ):
            raise ValueError(f"Ticket text no longer matches scenario: {ticket_id}")
        if len(scenario["metrics"]) != 2:
            raise ValueError(f"Each scenario must define exactly two symptom metrics: {ticket_id}")


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_logs(scenario: dict, ticket: dict[str, str], incident_id: str, start: datetime) -> list[dict]:
    events = []
    for index, minute in enumerate((0, 2, 4, 6, 8, 10, 12, 14), start=1):
        observation_index = min((index - 1) // 3, len(scenario["log_observations"]) - 1)
        observation = scenario["log_observations"][observation_index]
        level = "INFO" if index in (1, 7, 8) else "WARN" if index in (2, 3, 6) else "ERROR"
        events.append({
            "log_id": f"SYNLOG-{ticket['ticket_id']}-{index:02d}",
            "timestamp": iso(start + timedelta(minutes=minute)),
            "service": ticket["service"],
            "level": level,
            "incident_id": incident_id,
            "ticket_id": ticket["ticket_id"],
            "provenance": PROVENANCE,
            "message": observation,
        })
    return events


def build_metrics(scenario: dict, ticket: dict[str, str], incident_id: str, start: datetime) -> list[dict]:
    samples = []
    positions = ((-5, "baseline", "baseline", False), (4, "ramp", "anomaly_ramp", True), (8, "peak", "peak_anomaly", True), (13, "recovery", "recovery", False))
    for metric_index, metric in enumerate(scenario["metrics"], start=1):
        ramp = metric["baseline"] + (metric["peak"] - metric["baseline"]) * 0.65
        for sample_index, (minute, value_key, phase, is_anomaly) in enumerate(positions, start=1):
            samples.append({
                "metric_id": f"SYNMET-{ticket['ticket_id']}-{metric_index:02d}-{sample_index:02d}",
                "timestamp": iso(start + timedelta(minutes=minute)),
                "service": ticket["service"],
                "incident_id": incident_id,
                "ticket_id": ticket["ticket_id"],
                "metric_name": metric["name"],
                "value": round(ramp, 3) if value_key == "ramp" else metric[value_key],
                "unit": metric["unit"],
                "is_anomaly": str(is_anomaly).lower(),
                "phase": phase,
                "provenance": PROVENANCE,
            })
    return samples


def generate() -> dict:
    tickets = load_tickets()
    scenarios = load_scenarios()
    validate_scenarios(scenarios, tickets)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logs: list[dict] = []
    metrics: list[dict] = []
    manifest = []
    for index, scenario in enumerate(scenarios):
        ticket = tickets[scenario["ticket_id"]]
        incident_id = f"SYN-{ticket['ticket_id']}"
        start = BASE_START + timedelta(minutes=index * 30)
        end = start + timedelta(minutes=15)
        logs.extend(build_logs(scenario, ticket, incident_id, start))
        metrics.extend(build_metrics(scenario, ticket, incident_id, start))
        manifest.append({
            "incident_id": incident_id,
            "ticket_id": ticket["ticket_id"],
            "service": ticket["service"],
            "symptom": scenario["symptom"],
            "window_start_utc": iso(start),
            "window_end_utc": iso(end),
            "window_start_local_vietnam": (start + timedelta(hours=7)).strftime("%Y-%m-%dT%H:%M"),
            "window_end_local_vietnam": (end + timedelta(hours=7)).strftime("%Y-%m-%dT%H:%M"),
            "provenance": PROVENANCE,
            "root_cause": None,
            "root_cause_note": "No root cause was generated or verified.",
        })

    logs_path = OUTPUT_DIR / "incident_logs.jsonl"
    with logs_path.open("w", encoding="utf-8") as stream:
        for row in logs:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")

    metrics_path = OUTPUT_DIR / "incident_metrics.csv"
    fields = list(metrics[0])
    with metrics_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(metrics)

    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps({
        "dataset_name": "ticket-informed-synthetic-telemetry-v1",
        "provenance": PROVENANCE,
        "usage": "MVP demo and pipeline testing only; not real operational telemetry or verified RCA ground truth.",
        "scenario_count": len(manifest),
        "log_count": len(logs),
        "metric_count": len(metrics),
        "scenarios": manifest,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"scenarios": len(manifest), "logs": len(logs), "metrics": len(metrics), "manifest": str(manifest_path)}


if __name__ == "__main__":
    print(json.dumps(generate(), ensure_ascii=False, indent=2))
