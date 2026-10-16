from __future__ import annotations

import csv
import argparse
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INCIDENTS_FILE = ROOT_DIR / "data" / "eval" / "incidents.jsonl"
SPLITS_FILE = ROOT_DIR / "data" / "eval" / "benchmark_v2_splits.csv"


def load_incidents() -> list[dict]:
    with INCIDENTS_FILE.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def compact_ids(values: list[str], limit: int) -> list[str]:
    return values[:limit]


def evidence_ids_for_eval(incident: dict) -> list[str]:
    return (
        incident["runbook_ids"]
        + compact_ids(incident["log_evidence_ids"], 5)
        + compact_ids(incident["metric_evidence_ids"], 5)
    )


def build_questions(
    incident: dict,
    incident_index: int,
    *,
    language: str = "vi",
    split: str | None = None,
) -> list[dict]:
    service = incident["service"]
    category = incident["category"]
    symptoms = incident["symptoms"]
    event_window = incident["event_window"]
    evidence_ids = evidence_ids_for_eval(incident)

    if language == "en":
        templates = [
            {
                "query_type": "rca",
                "question": (
                    f"Investigate the reported symptoms on {service}: {symptoms}. "
                    "Which ticket, runbook, and operational evidence should be reviewed?"
                ),
                "notes": "English RCA-style retrieval query; labels are not included in question text.",
            },
            {
                "query_type": "evidence_retrieval",
                "question": (
                    f"For {service} during {event_window}, retrieve the most relevant ticket and runbook "
                    f"evidence for these symptoms: {symptoms}."
                ),
                "notes": "English evidence-retrieval query; expected logs and metrics are tracked separately.",
            },
            {
                "query_type": "technician_action",
                "question": (
                    f"What verification steps should a technician follow for {symptoms} "
                    f"affecting {service} ({category})?"
                ),
                "notes": "English technician query without incident-ID tokens that do not occur in evidence.",
            },
        ]
    else:
        templates = [
            {
                "query_type": "rca",
                "question": (
                    f"Service {service} co dau hieu: {symptoms}. "
                    "Hay phan tich RCA dua tren ticket, log, metric va runbook lien quan."
                ),
                "notes": "RCA query: danh gia kha nang truy xuat evidence va du doan root cause.",
            },
            {
                "query_type": "evidence_retrieval",
                "question": (
                    f"Trong time window {event_window}, can tim bang chung nao de xac minh su co "
                    f"tren service {service} voi trieu chung: {symptoms}?"
                ),
                "notes": "Retrieval query: danh gia recall cua ticket, runbook, log va metric evidence.",
            },
            {
                "query_type": "technician_action",
                "question": (
                    f"Technician nen kiem tra cac buoc nao cho trieu chung {symptoms} "
                    f"tren service {service} thuoc nhom {category}?"
                ),
                "notes": "Action query: danh gia truy xuat runbook va de xuat hanh dong co approval.",
            },
        ]

    rows: list[dict] = []
    for query_index, template in enumerate(templates, start=1):
        rows.append(
            {
                "eval_id": f"EV-{incident_index:04d}-{query_index}",
                "incident_id": incident["incident_id"],
                "query_type": template["query_type"],
                "question": template["question"],
                "service": service,
                "category": category,
                "split": split or incident["split"],
                "relevant_ticket_ids": incident["ticket_ids"],
                "runbook_ids": incident["runbook_ids"],
                "log_evidence_ids": compact_ids(incident["log_evidence_ids"], 5),
                "metric_evidence_ids": compact_ids(incident["metric_evidence_ids"], 5),
                "evidence_ids": evidence_ids,
                "expected_root_cause": incident["root_cause_label"],
                "source": "generated_from_synthetic_scenario_labels",
                "notes": template["notes"],
            }
        )
    return rows


def write_jsonl(rows: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(rows: list[dict], path: Path) -> None:
    fieldnames = [
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
        "source",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: "|".join(value) if isinstance(value, list) else value
                    for key, value in row.items()
                }
            )


def load_split_assignments(path: Path | None) -> dict[str, str] | None:
    if path is None:
        return None
    with path.open("r", encoding="utf-8", newline="") as handle:
        assignments = {row["incident_id"]: row["split"] for row in csv.DictReader(handle)}
    return assignments


def generate(*, language: str, split_file: Path | None, output_stem: str) -> int:
    incidents = load_incidents()
    assignments = load_split_assignments(split_file)
    if assignments is not None:
        incident_ids = {incident["incident_id"] for incident in incidents}
        if set(assignments) != incident_ids:
            raise ValueError("Split file incident IDs do not exactly match incidents.jsonl")

    rows: list[dict] = []
    for incident_index, incident in enumerate(incidents, start=1):
        split = assignments[incident["incident_id"]] if assignments is not None else None
        rows.extend(build_questions(incident, incident_index, language=language, split=split))

    jsonl_path = ROOT_DIR / "data" / "eval" / f"{output_stem}.jsonl"
    csv_path = ROOT_DIR / "data" / "eval" / f"{output_stem}.csv"
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(rows, jsonl_path)
    write_csv(rows, csv_path)
    print(f"Generated {len(rows)} queries -> {jsonl_path}")
    print(f"Generated CSV copy -> {csv_path}")
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate evaluation queries from incident labels.")
    parser.add_argument("--language", choices=["vi", "en"], default="vi")
    parser.add_argument("--split-file", type=Path)
    parser.add_argument("--output-stem", default="evaluation_queries")
    args = parser.parse_args()
    generate(language=args.language, split_file=args.split_file, output_stem=args.output_stem)
