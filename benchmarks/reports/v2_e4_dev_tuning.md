# E4 dev tuning

- Dev queries: 24
- E3 candidate_k: 20; output top_k: 10
- Model warmup excluded from latency

| Rerank K | Recall@5 | Precision@5 | MRR@10 | nDCG@5 | p50 ms | p95 ms |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 0.4306 | 0.2083 | 0.5224 | 0.3762 | 619.7 | 875.5 |
| 20 | 0.3681 | 0.1750 | 0.4806 | 0.3315 | 1112.8 | 1626.5 |

Selected rerank_k: 10 (highest nDCG@5; Recall@5 and smaller pool break ties).
