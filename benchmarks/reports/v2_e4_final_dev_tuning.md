# E4 dev tuning

- Dev queries: 24
- E3 candidate_k: 100; output top_k: 10
- Model warmup excluded from latency

| Rerank K | Recall@5 | Precision@5 | MRR@10 | nDCG@5 | p50 ms | p95 ms |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 0.3889 | 0.1833 | 0.5063 | 0.3474 | 629.8 | 977.9 |
| 20 | 0.3681 | 0.1750 | 0.4919 | 0.3413 | 1142.4 | 1679.7 |

Selected rerank_k: 10 (highest nDCG@5; Recall@5 and smaller pool break ties).
