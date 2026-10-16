from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW = ROOT_DIR / "data/eval/benchmark_v2_review.csv"


def evaluate(path: Path) -> dict:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))

    reviewed = [
        row for row in rows
        if row.get("evidence_sufficiency") in {"sufficient", "insufficient"}
        and row.get("model_status", "").strip() in {"grounded", "answered", "insufficient_evidence"}
    ]
    matrix = {
        "sufficient": {"answered": 0, "abstained": 0},
        "insufficient": {"answered": 0, "abstained": 0},
    }
    answer_labels = []
    fact_total = 0
    unsupported_total = 0
    fact_rows = 0
    for row in reviewed:
        label = row["evidence_sufficiency"]
        action = "abstained" if row["model_status"].strip() == "insufficient_evidence" else "answered"
        matrix[label][action] += 1
        if label == "sufficient" and action == "answered" and row.get("rca_correct", "").lower() in {"yes", "no"}:
            answer_labels.append(row["rca_correct"].lower() == "yes")
        if row.get("fact_count", "").strip() and row.get("unsupported_fact_count", "").strip():
            fact_total += int(row["fact_count"])
            unsupported_total += int(row["unsupported_fact_count"])
            fact_rows += 1

    insufficient_total = sum(matrix["insufficient"].values())
    sufficient_total = sum(matrix["sufficient"].values())
    abstentions = matrix["insufficient"]["abstained"] + matrix["sufficient"]["abstained"]
    answered_sufficient = matrix["sufficient"]["answered"]
    strict_rca_successes = sum(answer_labels)
    return {
        "review_rows": len(rows),
        "reviewed_rows": len(reviewed),
        "decision_matrix": matrix,
        "correct_abstention_recall_on_insufficient": _ratio(matrix["insufficient"]["abstained"], insufficient_total),
        "abstention_precision": _ratio(matrix["insufficient"]["abstained"], abstentions),
        "false_abstention_rate_on_sufficient": _ratio(matrix["sufficient"]["abstained"], sufficient_total),
        "answer_coverage_on_sufficient": _ratio(answered_sufficient, sufficient_total),
        "rca_accuracy_among_answered_sufficient": _ratio(sum(answer_labels), len(answer_labels)),
        "rca_accuracy_denominator_answered_sufficient": len(answer_labels),
        "strict_rca_success_rate_on_all_sufficient": _ratio(strict_rca_successes, sufficient_total),
        "unsupported_fact_rate": _ratio(unsupported_total, fact_total),
        "unsupported_fact_counts": {"unsupported": unsupported_total, "total": fact_total, "reviewed_incidents": fact_rows},
        "unreviewed_rows": len(rows) - len(reviewed),
        "note": "Metrics describe only reviewed rows. Review sufficiency and RCA correctness independently of model output.",
    }


def _ratio(numerator: int, denominator: int) -> dict:
    return {"value": numerator / denominator if denominator else None, "numerator": numerator, "denominator": denominator}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score RCA answer/abstain decisions using a reviewed CSV.")
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(args.review)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
