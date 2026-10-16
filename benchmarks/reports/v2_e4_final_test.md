# E4 retrieval ablation

- Test queries: 21 from 7 incidents
- Category query counts: {'database': 9, 'network': 6, 'server_api': 6}
- candidate_k: 100; rerank_k: 10; output top_k: 10
- Model load and one warmup query per variant excluded from latency
- Sources: historical tickets and runbooks; log/metric evidence excluded
- Queries from the same incident are related; interpret the small test set cautiously

| Variant | Recall@5 | Precision@5 | MRR@10 | nDCG@5 | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|
| E1 BM25 | 0.4286 | 0.2000 | 0.7579 | 0.4876 | 93.9 | 293.9 |
| E3 Hybrid RRF | 0.5079 | 0.2381 | 0.9048 | 0.5805 | 181.1 | 400.5 |
| E4 Rerank | 0.3730 | 0.1619 | 0.5639 | 0.3608 | 753.2 | 924.4 |
| E4 Rewrite + Rerank | 0.4048 | 0.1810 | 0.5696 | 0.3779 | 755.5 | 919.9 |

## Delta versus E1 and E3

| Variant | Baseline | Recall@5 | nDCG@5 | p50 ms |
|---|---|---:|---:|---:|
| E4 Rerank | E1 BM25 | -0.0556 | -0.1268 | +659.3 |
| E4 Rerank | E3 Hybrid RRF | -0.1349 | -0.2197 | +572.1 |
| E4 Rewrite + Rerank | E1 BM25 | -0.0238 | -0.1097 | +661.6 |
| E4 Rewrite + Rerank | E3 Hybrid RRF | -0.1032 | -0.2026 | +574.4 |

## Metrics by category

### E1 BM25

| Category | Queries | Recall@5 | nDCG@5 | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|
| database | 9 | 0.5000 | 0.5246 | 22.5 | 93.9 |
| network | 6 | 0.4167 | 0.5110 | 90.9 | 179.3 |
| server_api | 6 | 0.3333 | 0.4088 | 170.7 | 300.1 |

### E3 Hybrid RRF

| Category | Queries | Recall@5 | nDCG@5 | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|
| database | 9 | 0.5741 | 0.6051 | 104.9 | 185.7 |
| network | 6 | 0.5000 | 0.6131 | 186.7 | 297.6 |
| server_api | 6 | 0.4167 | 0.5110 | 261.4 | 423.6 |

### E4 Rerank

| Category | Queries | Recall@5 | nDCG@5 | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|
| database | 9 | 0.3148 | 0.3343 | 753.5 | 847.1 |
| network | 6 | 0.5000 | 0.4035 | 688.4 | 906.6 |
| server_api | 6 | 0.3333 | 0.3577 | 751.7 | 911.3 |

### E4 Rewrite + Rerank

| Category | Queries | Recall@5 | nDCG@5 | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|
| database | 9 | 0.3889 | 0.3910 | 767.4 | 914.1 |
| network | 6 | 0.5000 | 0.3786 | 660.8 | 873.5 |
| server_api | 6 | 0.3333 | 0.3577 | 786.0 | 911.2 |

