from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INCIDENTS = ROOT_DIR / "data/eval/incidents.jsonl"
SPLITS = ROOT_DIR / "data/eval/benchmark_v2_splits.csv"
TICKETS = ROOT_DIR / "data/processed/tickets/normalized_tickets.csv"
METRICS = ROOT_DIR / "data/processed/metrics/incident_metrics.csv"
OUTPUT = ROOT_DIR / "benchmarks/reports/rca_baseline_v2_predictions.csv"

# These cause classes are declared operational rules, not looked up from the
# incident's hidden root_cause_label field.
RULES = {
    "packet_loss_percent": (10.0, "edge gateway saturation causing intermittent connectivity"),
    "share_mount_error_rate": (10.0, "network share permission or mount failure"),
    "dns_lookup_failure_rate": (10.0, "stale DNS resolver cache or failed upstream lookup"),
    "vpn_tunnel_failure_rate": (10.0, "VPN tunnel authentication or profile mismatch"),
    "proxy_5xx_rate": (8.0, "proxy rule or certificate inspection failure"),
    "device_error_count": (6.0, "endpoint device driver, firmware, or hardware malfunction"),
    "auth_failure_rate": (8.0, "identity provider policy mismatch or account lock"),
    "api_error_rate": (8.0, "application configuration regression causing request failures"),
    "notification_delivery_failure_rate": (8.0, "notification provider authentication or rate limit failure"),
    "payment_error_rate": (8.0, "payment API dependency failure"),
    "db_storage_error_rate": (5.0, "primary database storage or transaction failure"),
    "db_cpu_utilization": (90.0, "reporting database resource saturation"),
    "db_lookup_error_rate": (5.0, "customer database consistency or lookup failure"),
    "backup_job_failure_count": (5.0, "backup job failure or snapshot retention issue"),
}
TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {"the", "and", "for", "with", "from", "this", "that", "have", "has", "are", "was", "were", "into", "need", "help", "please", "issue", "problem"}


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def tokens(text: str) -> Counter:
    return Counter(token for token in TOKEN_RE.findall(text.lower()) if token not in STOPWORDS)


def cosine(left: Counter, right: Counter) -> float:
    if not left or not right:
        return 0.0
    common = left.keys() & right.keys()
    numerator = sum(left[key] * right[key] for key in common)
    denominator = math.sqrt(sum(value * value for value in left.values()) * sum(value * value for value in right.values()))
    return numerator / denominator if denominator else 0.0


def timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> None:
    incidents = {row["incident_id"]: row for row in read_jsonl(INCIDENTS)}
    with SPLITS.open(encoding="utf-8", newline="") as stream:
        splits = {row["incident_id"]: row["split"] for row in csv.DictReader(stream)}
    with TICKETS.open(encoding="utf-8", newline="") as stream:
        tickets = {row["ticket_id"]: row for row in csv.DictReader(stream)}
    with METRICS.open(encoding="utf-8", newline="") as stream:
        all_metrics = list(csv.DictReader(stream))

    train = [item for key, item in incidents.items() if splits.get(key) == "train"]
    test = [item for key, item in incidents.items() if splits.get(key) == "test"]
    output_rows = []
    for incident in test:
        ticket_id = incident["ticket_ids"][0]
        ticket = tickets[ticket_id]
        query_text = f"{ticket.get('title', '')} {ticket.get('description', '')} {incident['symptoms']}"

        rule_candidates = []
        start_text, end_text = incident["event_window"].split("/")
        start, end = timestamp(start_text), timestamp(end_text)
        for metric in all_metrics:
            metric_time = timestamp(metric["timestamp"])
            if metric["service"] != incident["service"] or not start <= metric_time <= end:
                continue
            rule = RULES.get(metric["metric_name"])
            if rule and float(metric["value"]) >= rule[0]:
                rule_candidates.append((float(metric["value"]) / rule[0], rule[1], metric["metric_id"]))
        rule_pred = max(rule_candidates, default=(0.0, "", ""))[1]
        rule_evidence = max(rule_candidates, default=(0.0, "", ""))[2]

        query_tokens = tokens(query_text)
        nearest = None
        nearest_score = 0.0
        for candidate in train:
            candidate_ticket_id = candidate["ticket_ids"][0]
            if candidate_ticket_id == ticket_id:
                continue
            candidate_ticket = tickets.get(candidate_ticket_id, {})
            candidate_text = f"{candidate_ticket.get('title', '')} {candidate_ticket.get('description', '')} {candidate['symptoms']}"
            score = cosine(query_tokens, tokens(candidate_text))
            if score > nearest_score:
                nearest, nearest_score = candidate, score

        output_rows.append({
            "incident_id": incident["incident_id"],
            "split": "test",
            "service": incident["service"],
            "ticket_id": ticket_id,
            "rule_prediction": rule_pred,
            "rule_evidence_id": rule_evidence,
            "nearest_ticket_id": nearest["ticket_ids"][0] if nearest and nearest_score > 0 else "",
            "nearest_similarity": round(nearest_score, 4),
            "nearest_prediction": nearest["root_cause_label"] if nearest and nearest_score > 0 else "",
            "synthetic_reference_label_for_offline_scoring": incident["root_cause_label"],
            "label_status": incident["label_status"],
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output_rows[0]) if output_rows else [])
        writer.writeheader()
        writer.writerows(output_rows)
    rule_scored = [row for row in output_rows if row["rule_prediction"]]
    nearest_scored = [row for row in output_rows if row["nearest_prediction"]]
    summary = {
        "test_rows": len(output_rows),
        "rule_answer_coverage": len(rule_scored),
        "rule_exact_match_to_synthetic_label": sum(row["rule_prediction"] == row["synthetic_reference_label_for_offline_scoring"] for row in rule_scored),
        "nearest_answer_coverage": len(nearest_scored),
        "nearest_exact_match_to_synthetic_label": sum(row["nearest_prediction"] == row["synthetic_reference_label_for_offline_scoring"] for row in nearest_scored),
        "prediction_file": str(OUTPUT),
        "caution": "Exploratory baseline comparison only; labels are synthetic assumptions and test rows are not sufficiency-reviewed yet.",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
