from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path

from app.analysis.schema import Evidence
from app.core.config import ROOT_DIR
from app.ingestion.cleaner import clean_text


LOG_PATH = ROOT_DIR / "data/processed/logs/incident_logs.jsonl"
METRIC_PATH = ROOT_DIR / "data/processed/metrics/incident_metrics.csv"
SYNTHETIC_LOG_PATH = ROOT_DIR / "data/synthetic/telemetry-v1/incident_logs.jsonl"
SYNTHETIC_METRIC_PATH = ROOT_DIR / "data/synthetic/telemetry-v1/incident_metrics.csv"
REAL_LOG_PATH = ROOT_DIR / "data/real-telemetry/logs.jsonl"
REAL_METRIC_PATH = ROOT_DIR / "data/real-telemetry/metrics.csv"
LEAK_MARKERS = ("root cause candidate", "runbook candidates attached", "metric anomaly linked to")


def _in_window(value: str, start: datetime, end: datetime) -> bool:
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return start <= timestamp <= end


def load_logs(
    service: str,
    start: datetime,
    end: datetime,
    limit: int = 12,
    ticket_id: str | None = None,
    path: Path | None = None,
) -> list[Evidence]:
    if path is not None:
        paths = [path]
    elif os.getenv("ENABLE_REAL_TELEMETRY", "false").lower() == "true":
        paths = [REAL_LOG_PATH]
    else:
        paths = [LOG_PATH, SYNTHETIC_LOG_PATH]
    result: list[Evidence] = []
    for source_path in paths:
        if not source_path.exists():
            continue
        with source_path.open(encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                message = row["message"]
                if row["service"] != service or not _in_window(row["timestamp"], start, end):
                    continue
                if row.get("provenance") == "synthetic_ticket_informed" and ticket_id and row.get("ticket_id") != ticket_id:
                    continue
                if any(marker in message.lower() for marker in LEAK_MARKERS):
                    continue
                provenance = _provenance_label(row.get("provenance"))
                result.append(Evidence(
                    evidence_id=row["log_id"], source_type="log", service=service,
                    timestamp=datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
                    content=clean_text(f"{provenance}{row['level']}: {message}"),
                ))
    return sorted(result, key=lambda item: item.timestamp or start)[:limit]


def load_metrics(
    service: str,
    start: datetime,
    end: datetime,
    limit: int = 10,
    ticket_id: str | None = None,
    path: Path | None = None,
) -> list[Evidence]:
    if path is not None:
        paths = [path]
    elif os.getenv("ENABLE_REAL_TELEMETRY", "false").lower() == "true":
        paths = [REAL_METRIC_PATH]
    else:
        paths = [METRIC_PATH, SYNTHETIC_METRIC_PATH]
    result: list[Evidence] = []
    for source_path in paths:
        if not source_path.exists():
            continue
        with source_path.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                if row["service"] != service or not _in_window(row["timestamp"], start, end):
                    continue
                if row.get("provenance") == "synthetic_ticket_informed" and ticket_id and row.get("ticket_id") != ticket_id:
                    continue
                provenance = _provenance_label(row.get("provenance"))
                result.append(Evidence(
                    evidence_id=row["metric_id"], source_type="metric", service=service,
                    timestamp=datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
                    content=clean_text(f"{provenance}{row['metric_name']}={row['value']} {row['unit']}"),
                ))
    return sorted(result, key=lambda item: item.timestamp or start)[:limit]


def _provenance_label(value: str | None) -> str:
    if value == "synthetic_ticket_informed":
        return "SYNTHETIC DEMO DATA: "
    if value == "production_export":
        return "READ-ONLY OPERATIONAL EXPORT: "
    return ""
