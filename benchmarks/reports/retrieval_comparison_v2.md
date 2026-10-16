# Retrieval Benchmark V2

## Test results

The results below use the same 21 English test queries from 7 stratified incidents. Evaluation sources are historical tickets and runbooks; log and metric evidence are not yet indexed into the retrieval corpus.

| Experiment | Recall@5 | Precision@5 | MRR@10 | nDCG@5 | p50 latency | p95 latency |
|---|---:|---:|---:|---:|---:|---:|
| E1 BM25 | 0.4286 | 0.2000 | 0.7579 | 0.4876 | 93.9 ms | 293.9 ms |
| E2 BGE-M3 dense | 0.3492 | 0.1524 | 0.5847 | 0.3639 | Not recorded | Not recorded |
| E3 BM25 + BGE-M3 RRF, candidate_k=100 | 0.5079 | 0.2381 | 0.9048 | 0.5805 | 181.1 ms | 400.5 ms |
| E4 RRF + reranker, rerank_k=10 | 0.3730 | 0.1619 | 0.5639 | 0.3608 | 753.2 ms | 924.4 ms |
| E4 query rewrite + reranker | 0.4048 | 0.1810 | 0.5696 | 0.3779 | 755.5 ms | 919.9 ms |

## Interpretation

- E3 is the strongest measured configuration on this test set. Relative to E1, Recall@5 improves by 0.0793 and nDCG@5 by 0.0929.
- E4 did not improve ranking quality and increased median latency by about 572 ms relative to E3. Keep E3 as the default retrieval path; do not enable reranking by default based on these results.
- E2 dense-only is weaker than BM25 here. Retain dense retrieval as a complementary signal in RRF rather than using it alone.
- The test set is small (7 incidents), synthetic, and queries from one incident are correlated. Treat these metrics as an MVP diagnostic, not a broad generalization claim.
- The gold evidence currently contains ticket/runbook IDs only. Logs and metrics are excluded until they are ingested and their relevance labels are independently reviewed.
- Do not modify or tune against this test split. Use the dev split for subsequent parameter changes and create a new held-out test set for final claims.

Detailed per-query and per-category data: `v2_e1_bm25.json`, `v2_e2_dense.json`, `v2_e3_rrf.json`, and `v2_e4_final_test.json`.
