# Retrieval Comparison E1 vs E2

- Evaluation queries: 24 (test split)
- Top K: 10
- BM25 report: e1_bm25_full_corpus.json
- Dense report: e2_dense_bge_m3_full_corpus.json
- Both methods use the same PostgreSQL knowledge chunks and filters.
- Scores cover ticket and runbook evidence only; log and metric evidence are not indexed here.

| Method | Recall@5 | Recall@10 | MRR@10 |
|---|---:|---:|---:|
| E1 BM25 | 0.6250 | 0.6667 | 0.9028 |
| E2 BGE-M3 Dense | 0.2292 | 0.2708 | 0.3567 |
