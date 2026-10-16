# E4 dev tuning

- Dev queries: 21
- E3 candidate_k: 20; output top_k: 10
- Model warmup excluded from latency

| Rerank K | Recall@5 | Precision@5 | MRR@10 | nDCG@5 | p50 ms | p95 ms |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 0.2460 | 0.1238 | 0.2911 | 0.1870 | 599.4 | 899.0 |
| 20 | 0.2143 | 0.1048 | 0.2180 | 0.1624 | 1075.8 | 1381.8 |

Selected rerank_k: 10 (highest nDCG@5; Recall@5 and smaller pool break ties).
