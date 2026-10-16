from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from time import perf_counter
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.schemas.retrieval import RetrievalRequest  # noqa: E402
from app.services.retrieval_service import get_dense_retriever, get_reranker, retrieve_evidence  # noqa: E402
from run_benchmark import (  # noqa: E402
    expected_available_ids,
    load_eval_queries,
    mrr_at_k,
    ndcg_at_k,
    normalize_retrieved_ids,
    precision_at_k,
    recall_at_k,
)


def percentile(values: list[float], percentage: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * percentage
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def request_for(
    row: dict[str, Any], method: str, *, rewrite: bool, candidate_k: int, rerank_k: int,
) -> RetrievalRequest:
    return RetrievalRequest(
        query=row["question"], method=method, rewrite=rewrite,
        service=row.get("service"), category=row.get("category"),
        source_types=["runbook", "historical_ticket"], access_scope="it_internal",
        top_k=10, candidate_k=candidate_k, rerank_k=rerank_k,
    )


def evaluate(
    rows: list[dict[str, Any]], method: str, *, rewrite: bool = False,
    candidate_k: int = 100, rerank_k: int = 20,
) -> dict[str, Any]:
    per_query: list[dict[str, Any]] = []
    with SessionLocal() as db:
        if rows:
            retrieve_evidence(
                db, request_for(rows[0], method, rewrite=rewrite, candidate_k=candidate_k, rerank_k=rerank_k),
            )
        for row in rows:
            expected = expected_available_ids(row)
            if not expected:
                continue
            start = perf_counter()
            response = retrieve_evidence(
                db, request_for(row, method, rewrite=rewrite, candidate_k=candidate_k, rerank_k=rerank_k),
            )
            latency_ms = (perf_counter() - start) * 1000
            ids = normalize_retrieved_ids(response.results)
            per_query.append({
                "eval_id": row["eval_id"], "incident_id": row["incident_id"],
                "category": row.get("category", "unknown"),
                "retrieved_ids": ids, "expected_ids": expected,
                "recall_at_5": recall_at_k(ids, expected, 5),
                "precision_at_5": precision_at_k(ids, expected, 5),
                "mrr_at_10": mrr_at_k(ids, expected, 10),
                "ndcg_at_5": ndcg_at_k(ids, expected, 5),
                "latency_ms": round(latency_ms, 3),
            })
    latencies = [item["latency_ms"] for item in per_query]
    metrics = {key: mean([item[key] for item in per_query]) if per_query else 0.0 for key in (
        "recall_at_5", "precision_at_5", "mrr_at_10", "ndcg_at_5",
    )}
    metrics["latency_p50_ms"] = median(latencies) if latencies else 0.0
    metrics["latency_p95_ms"] = percentile(latencies, 0.95)
    per_category = {}
    for category in sorted({item["category"] for item in per_query}):
        items = [item for item in per_query if item["category"] == category]
        per_category[category] = {
            "query_count": len(items),
            "recall_at_5": mean([item["recall_at_5"] for item in items]),
            "precision_at_5": mean([item["precision_at_5"] for item in items]),
            "mrr_at_10": mean([item["mrr_at_10"] for item in items]),
            "ndcg_at_5": mean([item["ndcg_at_5"] for item in items]),
            "latency_p50_ms": median([item["latency_ms"] for item in items]),
            "latency_p95_ms": percentile([item["latency_ms"] for item in items], 0.95),
        }
    return {
        "method": method, "rewrite": rewrite, "candidate_k": candidate_k,
        "rerank_k": rerank_k, "query_count": len(per_query), "metrics": metrics,
        "per_category": per_category, "per_query": per_query,
    }


def warm_models() -> None:
    get_dense_retriever().embedding_model.embed_text("warmup payment api")
    get_reranker().score_pairs("warmup payment api", ["warmup passage"])


def tune(rows: list[dict[str, Any]], reports_dir: Path, report_stem: str, candidate_k: int) -> None:
    trials = [evaluate(rows, "hybrid_rerank", candidate_k=candidate_k, rerank_k=k) for k in (10, 20)]
    best = max(trials, key=lambda trial: (trial["metrics"]["ndcg_at_5"], trial["metrics"]["recall_at_5"], -trial["rerank_k"]))
    lines = ["# E4 dev tuning", "", f"- Dev queries: {len(rows)}", f"- E3 candidate_k: {candidate_k}; output top_k: 10", "- Model warmup excluded from latency", "", "| Rerank K | Recall@5 | Precision@5 | MRR@10 | nDCG@5 | p50 ms | p95 ms |", "|---:|---:|---:|---:|---:|---:|---:|"]
    for trial in trials:
        m = trial["metrics"]
        lines.append(f"| {trial['rerank_k']} | {m['recall_at_5']:.4f} | {m['precision_at_5']:.4f} | {m['mrr_at_10']:.4f} | {m['ndcg_at_5']:.4f} | {m['latency_p50_ms']:.1f} | {m['latency_p95_ms']:.1f} |")
    lines.extend(["", f"Selected rerank_k: {best['rerank_k']} (highest nDCG@5; Recall@5 and smaller pool break ties).", ""])
    path = reports_dir / f"{report_stem}_dev_tuning.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Selected rerank_k={best['rerank_k']}; wrote {path}")


def ablation(
    rows: list[dict[str, Any]], reports_dir: Path, candidate_k: int, rerank_k: int, report_stem: str,
) -> None:
    variants = [
        ("E1 BM25", "bm25", False),
        ("E3 Hybrid RRF", "hybrid", False),
        ("E4 Rerank", "hybrid_rerank", False),
        ("E4 Rewrite + Rerank", "hybrid_rerank", True),
    ]
    results = {
        label: evaluate(rows, method, rewrite=rewrite, candidate_k=candidate_k, rerank_k=rerank_k)
        for label, method, rewrite in variants
    }
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "split": "test", "incident_count": len({row["incident_id"] for row in rows}),
        "query_count": len(rows), "candidate_k": candidate_k, "rerank_k": rerank_k,
        "category_counts": {
            category: sum(1 for row in rows if row.get("category") == category)
            for category in sorted({row.get("category", "unknown") for row in rows})
        },
        "results": results,
    }
    json_path = reports_dir / f"{report_stem}.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# E4 retrieval ablation", "", f"- Test queries: {len(rows)} from {report['incident_count']} incidents", f"- Category query counts: {report['category_counts']}", f"- candidate_k: {candidate_k}; rerank_k: {rerank_k}; output top_k: 10", "- Model load and one warmup query per variant excluded from latency", "- Sources: historical tickets and runbooks; log/metric evidence excluded", "- Queries from the same incident are related; interpret the small test set cautiously", "", "| Variant | Recall@5 | Precision@5 | MRR@10 | nDCG@5 | p50 ms | p95 ms |", "|---|---:|---:|---:|---:|---:|---:|"]
    for label, result in results.items():
        m = result["metrics"]
        lines.append(f"| {label} | {m['recall_at_5']:.4f} | {m['precision_at_5']:.4f} | {m['mrr_at_10']:.4f} | {m['ndcg_at_5']:.4f} | {m['latency_p50_ms']:.1f} | {m['latency_p95_ms']:.1f} |")
    lines.extend(["", "## Delta versus E1 and E3", "", "| Variant | Baseline | Recall@5 | nDCG@5 | p50 ms |", "|---|---|---:|---:|---:|"])
    for label in ("E4 Rerank", "E4 Rewrite + Rerank"):
        current = results[label]["metrics"]
        for baseline_name in ("E1 BM25", "E3 Hybrid RRF"):
            baseline = results[baseline_name]["metrics"]
            lines.append(f"| {label} | {baseline_name} | {current['recall_at_5'] - baseline['recall_at_5']:+.4f} | {current['ndcg_at_5'] - baseline['ndcg_at_5']:+.4f} | {current['latency_p50_ms'] - baseline['latency_p50_ms']:+.1f} |")
    lines.extend(["", "## Metrics by category", ""])
    for label, result in results.items():
        lines.extend([f"### {label}", "", "| Category | Queries | Recall@5 | nDCG@5 | p50 ms | p95 ms |", "|---|---:|---:|---:|---:|---:|"])
        for category, values in result["per_category"].items():
            lines.append(f"| {category} | {values['query_count']} | {values['recall_at_5']:.4f} | {values['ndcg_at_5']:.4f} | {values['latency_p50_ms']:.1f} | {values['latency_p95_ms']:.1f} |")
        lines.append("")
    md_path = reports_dir / f"{report_stem}.md"
    md_path.write_text("\n".join([*lines, ""]), encoding="utf-8")
    print(f"Wrote {json_path} and {md_path}")
    for label, result in results.items():
        m = result["metrics"]
        print(f"{label}: Recall@5={m['recall_at_5']:.4f} nDCG@5={m['ndcg_at_5']:.4f} p50={m['latency_p50_ms']:.1f}ms p95={m['latency_p95_ms']:.1f}ms")


def main() -> None:
    parser = argparse.ArgumentParser(description="Tune and evaluate E4 cross-encoder reranking.")
    parser.add_argument("--split", choices=["dev", "test"], required=True)
    parser.add_argument("--rerank-k", type=int, choices=[10, 20], default=20)
    parser.add_argument("--candidate-k", type=int, default=100)
    parser.add_argument("--eval-file", type=Path, default=PROJECT_ROOT / "data" / "eval" / "evaluation_queries.jsonl")
    parser.add_argument("--report-stem", default=None, help="Output filename stem; use distinct names to preserve earlier runs.")
    args = parser.parse_args()
    reports_dir = PROJECT_ROOT / "benchmarks" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    eval_path = args.eval_file if args.eval_file.is_absolute() else PROJECT_ROOT / args.eval_file
    rows = load_eval_queries(eval_path, split=args.split)
    report_stem = args.report_stem or "e4_ablation_test"
    warm_models()
    if args.split == "dev":
        tune(rows, reports_dir, report_stem, args.candidate_k)
    else:
        ablation(rows, reports_dir, args.candidate_k, args.rerank_k, report_stem)


if __name__ == "__main__":
    main()
