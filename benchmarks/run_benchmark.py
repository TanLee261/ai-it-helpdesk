from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from app.schemas.retrieval import RetrievalRequest  # noqa: E402
from app.services.retrieval_service import retrieve_evidence  # noqa: E402


@dataclass(frozen=True)
class QueryMetric:
    eval_id: str
    incident_id: str
    category: str
    expected_available_ids: list[str]
    retrieved_ids: list[str]
    recall_at_5: float
    recall_at_10: float
    precision_at_5: float
    mrr_at_10: float
    ndcg_at_5: float


def load_eval_queries(path: Path, split: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            row = json.loads(line)
            if split and row.get("split") != split:
                continue
            rows.append(row)
            if limit and len(rows) >= limit:
                break
    return rows


def expected_available_ids(row: dict[str, Any]) -> list[str]:
    ticket_ids = [f"KT-{ticket_id}" for ticket_id in row.get("relevant_ticket_ids", [])]
    runbook_ids = row.get("runbook_ids", [])
    return sorted(set(ticket_ids + runbook_ids))


def normalize_retrieved_ids(results: list[Any]) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for result in results:
        document_id = result.document_id
        if document_id not in seen:
            ids.append(document_id)
            seen.add(document_id)
    return ids


def recall_at_k(retrieved_ids: list[str], expected_ids: list[str], k: int) -> float:
    if not expected_ids:
        return 0.0
    top_ids = set(retrieved_ids[:k])
    return len(top_ids.intersection(expected_ids)) / len(expected_ids)


def mrr_at_k(retrieved_ids: list[str], expected_ids: list[str], k: int) -> float:
    expected = set(expected_ids)
    for index, document_id in enumerate(retrieved_ids[:k], start=1):
        if document_id in expected:
            return 1 / index
    return 0.0


def precision_at_k(retrieved_ids: list[str], expected_ids: list[str], k: int) -> float:
    return len(set(retrieved_ids[:k]).intersection(expected_ids)) / k


def ndcg_at_k(retrieved_ids: list[str], expected_ids: list[str], k: int) -> float:
    expected = set(expected_ids)
    if not expected:
        return 0.0
    dcg = sum(1.0 / math.log2(rank + 1) for rank, document_id in enumerate(retrieved_ids[:k], 1) if document_id in expected)
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, min(k, len(expected)) + 1))
    return dcg / ideal


def run_retrieval_benchmark(
    eval_path: Path,
    split: str | None,
    limit: int | None,
    top_k: int,
    method: str,
    candidate_k: int = 50,
) -> dict[str, Any]:
    rows = load_eval_queries(eval_path, split=split, limit=limit)
    query_metrics: list[QueryMetric] = []

    with SessionLocal() as db:
        for row in rows:
            expected_ids = expected_available_ids(row)
            if not expected_ids:
                continue
            response = retrieve_evidence(
                db,
                RetrievalRequest(
                    query=row["question"],
                    method=method,
                    service=row.get("service"),
                    category=row.get("category"),
                    source_types=["runbook", "historical_ticket"],
                    access_scope="it_internal",
                    top_k=top_k,
                    candidate_k=candidate_k,
                ),
            )
            retrieved_ids = normalize_retrieved_ids(response.results)[:top_k]
            query_metrics.append(
                QueryMetric(
                    eval_id=row["eval_id"],
                    incident_id=row["incident_id"],
                    category=row.get("category", "unknown"),
                    expected_available_ids=expected_ids,
                    retrieved_ids=retrieved_ids[:top_k],
                    recall_at_5=recall_at_k(retrieved_ids, expected_ids, 5),
                    recall_at_10=recall_at_k(retrieved_ids, expected_ids, 10),
                    precision_at_5=precision_at_k(retrieved_ids, expected_ids, 5),
                    mrr_at_10=mrr_at_k(retrieved_ids, expected_ids, 10),
                    ndcg_at_5=ndcg_at_k(retrieved_ids, expected_ids, 5),
                )
            )

    per_category = {}
    for category in sorted({item.category for item in query_metrics}):
        items = [item for item in query_metrics if item.category == category]
        per_category[category] = {
            "query_count": len(items),
            "recall_at_5": mean([item.recall_at_5 for item in items]),
            "precision_at_5": mean([item.precision_at_5 for item in items]),
            "mrr_at_10": mean([item.mrr_at_10 for item in items]),
            "ndcg_at_5": mean([item.ndcg_at_5 for item in items]),
        }

    return {
        "benchmark": {"bm25": "E1 BM25 keyword baseline", "dense": "E2 BGE-M3 dense baseline", "hybrid": "E3 BM25 + BGE-M3 RRF"}[method],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "eval_path": str(eval_path),
        "split": split,
        "top_k": top_k,
        "candidate_k": candidate_k,
        "query_count": len(query_metrics),
        "metrics": {
            "recall_at_5": mean([item.recall_at_5 for item in query_metrics]) if query_metrics else 0.0,
            "recall_at_10": mean([item.recall_at_10 for item in query_metrics]) if query_metrics else 0.0,
            "precision_at_5": mean([item.precision_at_5 for item in query_metrics]) if query_metrics else 0.0,
            "mrr_at_10": mean([item.mrr_at_10 for item in query_metrics]) if query_metrics else 0.0,
            "ndcg_at_5": mean([item.ndcg_at_5 for item in query_metrics]) if query_metrics else 0.0,
        },
        "per_category": per_category,
        "notes": [
            "Evaluation uses available evidence only: runbook documents and historical ticket documents.",
            "Log and metric evidence IDs are excluded until those sources are ingested as knowledge documents.",
        ],
        "per_query": [asdict(item) for item in query_metrics],
    }


def write_markdown_report(report: dict[str, Any], path: Path) -> None:
    metrics = report["metrics"]
    lines = [
        f"# {report['benchmark']}",
        "",
        f"- Query count: {report['query_count']}",
        f"- Split: {report['split'] or 'all'}",
        f"- Top K: {report['top_k']}",
        f"- Candidate K per branch: {report['candidate_k']}",
        f"- Recall@5: {metrics['recall_at_5']:.4f}",
        f"- Recall@10: {metrics['recall_at_10']:.4f}",
        f"- Precision@5: {metrics['precision_at_5']:.4f}",
        f"- MRR@10: {metrics['mrr_at_10']:.4f}",
        f"- nDCG@5: {metrics['ndcg_at_5']:.4f}",
        "",
        "## Notes",
        "",
    ]
    lines.extend([f"- {note}" for note in report["notes"]])
    if report.get("per_category"):
        lines.extend([
            "",
            "## Metrics by category",
            "",
            "| Category | Queries | Recall@5 | Precision@5 | MRR@10 | nDCG@5 |",
            "|---|---:|---:|---:|---:|---:|",
        ])
        for category, values in report["per_category"].items():
            lines.append(
                f"| {category} | {values['query_count']} | {values['recall_at_5']:.4f} | "
                f"{values['precision_at_5']:.4f} | {values['mrr_at_10']:.4f} | {values['ndcg_at_5']:.4f} |"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run retrieval benchmark experiments.")
    parser.add_argument("--config", default="e1_bm25", choices=["e1_bm25", "e2_dense", "e3_hybrid_rrf"])
    parser.add_argument("--split", default="test")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--candidate-k", type=int, default=50)
    parser.add_argument("--tune", action="store_true", help="Evaluate E3 candidate depths on the dev split only.")
    parser.add_argument("--report-stem", default=None, help="Override report filename without replacing a prior run.")
    parser.add_argument("--compare-with", default=None, help="BM25 report JSON to compare against E2.")
    parser.add_argument("--compare-dense", default=None, help="Dense report JSON to compare against E3.")
    parser.add_argument("--eval-file", type=Path, default=None, help="Evaluation JSONL path; relative paths are resolved from project root.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reports_dir = PROJECT_ROOT / "benchmarks" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    eval_path = args.eval_file or (PROJECT_ROOT / "data" / "eval" / "evaluation_queries.jsonl")
    if not eval_path.is_absolute():
        eval_path = PROJECT_ROOT / eval_path
    if args.tune:
        if args.config != "e3_hybrid_rrf" or args.split != "dev":
            raise ValueError("Tuning requires --config e3_hybrid_rrf --split dev")
        trials = []
        for candidate_k in (20, 50, 100):
            trial = run_retrieval_benchmark(eval_path, "dev", args.limit or None, 10, "hybrid", candidate_k)
            trials.append(trial)
            print(f"candidate_k={candidate_k} nDCG@5={trial['metrics']['ndcg_at_5']:.4f} Recall@5={trial['metrics']['recall_at_5']:.4f}")
        best = max(trials, key=lambda trial: (trial["metrics"]["ndcg_at_5"], trial["metrics"]["recall_at_5"], -trial["candidate_k"]))
        lines = ["# E3 RRF dev tuning", "", f"- Dev queries: {best['query_count']}", "- RRF constant: 60", "- Final output top_k: 10 (metrics at 5 and 10)", "", "| Candidate K per branch | Recall@5 | Precision@5 | MRR@10 | nDCG@5 |", "|---:|---:|---:|---:|---:|"]
        for trial in trials:
            metrics = trial["metrics"]
            lines.append(f"| {trial['candidate_k']} | {metrics['recall_at_5']:.4f} | {metrics['precision_at_5']:.4f} | {metrics['mrr_at_10']:.4f} | {metrics['ndcg_at_5']:.4f} |")
        lines.extend(["", f"- Selected candidate_k: {best['candidate_k']} (highest nDCG@5; Recall@5 and smaller K break ties).", ""])
        path = reports_dir / f"{args.report_stem or 'e3_hybrid_rrf'}_dev_tuning.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        print(f"Selected candidate_k={best['candidate_k']}; wrote {path}")
        return

    method = {"e1_bm25": "bm25", "e2_dense": "dense", "e3_hybrid_rrf": "hybrid"}[args.config]
    report = run_retrieval_benchmark(
        eval_path=eval_path,
        split=args.split or None,
        limit=args.limit or None,
        top_k=args.top_k,
        method=method,
        candidate_k=args.candidate_k,
    )
    report_stem = args.report_stem or {"bm25": "e1_bm25_baseline", "dense": "e2_dense_bge_m3_baseline", "hybrid": "e3_hybrid_rrf"}[method]
    json_path = reports_dir / f"{report_stem}.json"
    md_path = reports_dir / f"{report_stem}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(report, md_path)
    print(
        f"{report['benchmark']}: "
        f"queries={report['query_count']} "
        f"recall@5={report['metrics']['recall_at_5']:.4f} "
        f"recall@10={report['metrics']['recall_at_10']:.4f} "
        f"precision@5={report['metrics']['precision_at_5']:.4f} "
        f"mrr@10={report['metrics']['mrr_at_10']:.4f} "
        f"ndcg@5={report['metrics']['ndcg_at_5']:.4f}"
    )
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")

    if method == "dense" and args.compare_with:
        comparison_path = reports_dir / "retrieval_comparison_e1_e2.md"
        bm25_path = Path(args.compare_with) if args.compare_with else reports_dir / "e1_bm25_baseline.json"
        if bm25_path.exists():
            bm25_report = json.loads(bm25_path.read_text(encoding="utf-8"))
            if (
                bm25_report.get("query_count") != report.get("query_count")
                or bm25_report.get("split") != report.get("split")
                or bm25_report.get("top_k") != report.get("top_k")
                or bm25_report.get("candidate_k") != report.get("candidate_k")
                or [item["eval_id"] for item in bm25_report.get("per_query", [])]
                != [item["eval_id"] for item in report.get("per_query", [])]
            ):
                raise ValueError("BM25 and dense reports must use the same evaluation queries, split, and top_k")
            lines = [
                "# Retrieval Comparison E1 vs E2",
                "",
                f"- Evaluation queries: {report['query_count']} ({report['split'] or 'all'} split)",
                f"- Top K: {report['top_k']}",
                f"- BM25 report: {bm25_path.name}",
                f"- Dense report: {json_path.name}",
                "- Both methods use the same PostgreSQL knowledge chunks and filters.",
                "- Scores cover ticket and runbook evidence only; log and metric evidence are not indexed here.",
                "",
                "| Method | Recall@5 | Recall@10 | MRR@10 |",
                "|---|---:|---:|---:|",
                (
                    f"| E1 BM25 | {bm25_report['metrics']['recall_at_5']:.4f} | "
                    f"{bm25_report['metrics']['recall_at_10']:.4f} | "
                    f"{bm25_report['metrics']['mrr_at_10']:.4f} |"
                ),
                (
                    f"| E2 BGE-M3 Dense | {report['metrics']['recall_at_5']:.4f} | "
                    f"{report['metrics']['recall_at_10']:.4f} | "
                    f"{report['metrics']['mrr_at_10']:.4f} |"
                ),
                "",
            ]
            comparison_path.write_text("\n".join(lines), encoding="utf-8")
            print(f"Wrote {comparison_path}")

    if method == "hybrid" and args.compare_with and args.compare_dense:
        baseline_reports = [json.loads(Path(path).read_text(encoding="utf-8")) for path in (args.compare_with, args.compare_dense)]
        for baseline in baseline_reports:
            if (baseline.get("split"), baseline.get("top_k"), baseline.get("candidate_k")) != (report["split"], report["top_k"], report["candidate_k"]):
                raise ValueError("E1-E3 must have identical split, top_k, and candidate_k")
            if [item["eval_id"] for item in baseline.get("per_query", [])] != [item["eval_id"] for item in report["per_query"]]:
                raise ValueError("E1-E3 must use identical evaluation queries")
        incident_count = len({item["incident_id"] for item in report["per_query"]})
        lines = ["# Retrieval comparison E1-E3", "", f"- Split: {report['split']}; queries: {report['query_count']} from {incident_count} incidents; output top_k: {report['top_k']}", f"- Candidate K per branch: {report['candidate_k']}; RRF constant: 60", "- All methods use the same ticket and runbook corpus and filters.", "- Log/metric evidence is outside this retrieval evaluation.", "- Queries from one incident are related, so this small synthetic test set is not a general performance estimate.", "", "| Method | Recall@5 | Recall@10 | Precision@5 | MRR@10 | nDCG@5 |", "|---|---:|---:|---:|---:|---:|"]
        for item in (*baseline_reports, report):
            metrics = item["metrics"]
            lines.append(f"| {item['benchmark']} | {metrics['recall_at_5']:.4f} | {metrics['recall_at_10']:.4f} | {metrics['precision_at_5']:.4f} | {metrics['mrr_at_10']:.4f} | {metrics['ndcg_at_5']:.4f} |")
        comparison_path = reports_dir / "retrieval_comparison_e1_e2_e3.md"
        lines.extend(["", "BM25 remains the API default because it outperforms E3 on this test set."])
        comparison_path.write_text("\n".join([*lines, ""]), encoding="utf-8")
        print(f"Wrote {comparison_path}")


if __name__ == "__main__":
    main()
