from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import tempfile
from urllib.request import Request, urlopen
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.ingestion.cleaner import clean_text  # noqa: E402


OUTPUT_DIR = ROOT / "data/real-telemetry"


def parse_timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp must include timezone: {value!r}")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def read_records(path: Path) -> Iterable[tuple[int, dict[str, str]]]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            yield from enumerate(csv.DictReader(stream), start=2)
        return
    if path.suffix.lower() in {".jsonl", ".ndjson"}:
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if line.strip():
                    yield line_number, json.loads(line)
        return
    raise ValueError(f"Unsupported input format: {path.suffix}; use CSV or JSONL")


def stable_id(prefix: str, source_system: str, source_record_id: str, timestamp: str, payload: str) -> str:
    raw = "|".join((source_system, source_record_id, timestamp, payload))
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20]}"


def field(row: dict, name: str, path: Path, line: int) -> str:
    value = row.get(name)
    if value is None or not str(value).strip():
        raise ValueError(f"{path.name}:{line}: required field {name!r} is empty")
    return str(value).strip()


def service_name(raw: str, service_map: dict[str, str], path: Path, line: int) -> str:
    canonical = service_map.get(raw)
    if not canonical:
        raise ValueError(f"{path.name}:{line}: unmapped service {raw!r}; add it to the service map")
    return canonical


def normalize_logs(args, service_map: dict[str, str]) -> int:
    output = args.output_dir / "logs.jsonl"
    written = 0
    with output.open("w", encoding="utf-8") as target:
        for line, row in read_records(args.logs):
            timestamp = parse_timestamp(field(row, args.timestamp_field, args.logs, line))
            raw_service = field(row, args.service_field, args.logs, line)
            source_id = str(row.get(args.record_id_field, line)).strip()
            message = clean_text(field(row, args.message_field, args.logs, line))
            level = clean_text(str(row.get(args.level_field, "INFO") or "INFO")).upper()
            record = {
                "log_id": stable_id("LOG", args.source_system, source_id, timestamp, message),
                "timestamp": timestamp,
                "service": service_name(raw_service, service_map, args.logs, line),
                "level": level,
                "message": message,
                "provenance": "production_export",
                "source_system": args.source_system,
                "source_record_id": source_id,
            }
            target.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1
    return written


def normalize_metrics(args, service_map: dict[str, str]) -> int:
    output = args.output_dir / "metrics.csv"
    columns = ["metric_id", "timestamp", "service", "metric_name", "value", "unit", "provenance", "source_system", "source_record_id"]
    written = 0
    with output.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=columns)
        writer.writeheader()
        for line, row in read_records(args.metrics):
            timestamp = parse_timestamp(field(row, args.timestamp_field, args.metrics, line))
            raw_service = field(row, args.service_field, args.metrics, line)
            source_id = str(row.get(args.record_id_field, line)).strip()
            name = clean_text(field(row, args.metric_name_field, args.metrics, line))
            value = clean_text(field(row, args.value_field, args.metrics, line))
            unit = clean_text(str(row.get(args.unit_field, "") or ""))
            metric_id = stable_id("MET", args.source_system, source_id, timestamp, f"{name}={value} {unit}")
            writer.writerow({
                "metric_id": metric_id,
                "timestamp": timestamp,
                "service": service_name(raw_service, service_map, args.metrics, line),
                "metric_name": name,
                "value": value,
                "unit": unit,
                "provenance": "production_export",
                "source_system": args.source_system,
                "source_record_id": source_id,
            })
            written += 1
    return written


def push_logs_to_loki(path: Path, loki_url: str) -> int:
    streams: dict[tuple[str, str], list[list[str]]] = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            timestamp_ns = str(int(datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).timestamp() * 1_000_000_000))
            labels = (row["service"], row["level"])
            streams.setdefault(labels, []).append([
                timestamp_ns,
                json.dumps({"log_id": row["log_id"], "message": row["message"], "source_system": row["source_system"]}, ensure_ascii=False),
            ])
    payload = {"streams": [
        {"stream": {"service": service, "level": level, "source": "helpdesk-readonly-import"}, "values": values}
        for (service, level), values in streams.items()
    ]}
    if not payload["streams"]:
        return 0
    request = Request(
        loki_url.rstrip("/") + "/loki/api/v1/push",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        if response.status not in (200, 204):
            raise RuntimeError(f"Loki returned HTTP {response.status}")
    return sum(len(values) for values in streams.values())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Normalize authorized telemetry exports for local, read-only RCA evaluation.")
    parser.add_argument("--logs", type=Path, required=True, help="CSV or JSONL log export")
    parser.add_argument("--metrics", type=Path, required=True, help="CSV or JSONL metric export")
    parser.add_argument("--service-map", type=Path, required=True, help="JSON source-service to canonical-service map")
    parser.add_argument("--source-system", required=True, help="Source identifier, e.g. datadog-prod-readonly")
    parser.add_argument("--loki-url", help="Optional local Loki base URL; sends the redacted imported logs to Loki")
    parser.add_argument("--timestamp-field", default="timestamp")
    parser.add_argument("--service-field", default="service")
    parser.add_argument("--record-id-field", default="event_id")
    parser.add_argument("--message-field", default="message")
    parser.add_argument("--level-field", default="level")
    parser.add_argument("--metric-name-field", default="metric_name")
    parser.add_argument("--value-field", default="value")
    parser.add_argument("--unit-field", default="unit")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.logs.is_file() or not args.metrics.is_file() or not args.service_map.is_file():
        raise SystemExit("Logs, metrics, and service-map paths must exist as files")
    service_map = json.loads(args.service_map.read_text(encoding="utf-8"))
    if not isinstance(service_map, dict) or not service_map:
        raise SystemExit("Service map must be a non-empty JSON object")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_paths = [OUTPUT_DIR / "logs.jsonl", OUTPUT_DIR / "metrics.csv"]
    if any(path.exists() for path in final_paths):
        raise SystemExit("Normalized outputs already exist; move them aside before importing to avoid accidental replacement")
    try:
        with tempfile.TemporaryDirectory(prefix="import-", dir=OUTPUT_DIR) as staging:
            args.output_dir = Path(staging)
            log_count = normalize_logs(args, service_map)
            metric_count = normalize_metrics(args, service_map)
            (Path(staging) / "logs.jsonl").replace(final_paths[0])
            (Path(staging) / "metrics.csv").replace(final_paths[1])
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Import stopped: {exc}") from exc
    loki_count = push_logs_to_loki(final_paths[0], args.loki_url) if args.loki_url else 0
    print(json.dumps({
        "logs_written": log_count,
        "metrics_written": metric_count,
        "logs_sent_to_loki": loki_count,
        "output_dir": str(OUTPUT_DIR),
        "provenance": "production_export",
        "warning": "Review access scope, redaction, time coverage, and service mapping before enabling API reads.",
    }, indent=2))


if __name__ == "__main__":
    main()
