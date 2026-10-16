# Retrieval comparison E1-E3

- Split: test; queries: 24 from 8 incidents; output top_k: 10
- Candidate K per branch: 20; RRF constant: 60
- All methods use the same ticket and runbook corpus and filters.
- Log/metric evidence is outside this retrieval evaluation.
- Queries from one incident are related, so this small synthetic test set is not a general performance estimate.

| Method | Recall@5 | Recall@10 | Precision@5 | MRR@10 | nDCG@5 |
|---|---:|---:|---:|---:|---:|
| E1 BM25 keyword baseline | 0.6250 | 0.6667 | 0.3333 | 0.9028 | 0.6555 |
| E2 BGE-M3 dense baseline | 0.2292 | 0.2708 | 0.1000 | 0.3567 | 0.2218 |
| E3 BM25 + BGE-M3 RRF | 0.5486 | 0.6319 | 0.2917 | 0.8069 | 0.5453 |

BM25 remains the API default because it outperforms E3 on this test set.
