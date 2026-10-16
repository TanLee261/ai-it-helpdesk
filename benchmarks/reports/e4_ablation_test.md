# E4 retrieval ablation

- Test queries: 24 from 8 incidents
- candidate_k: 20; rerank_k: 20; output top_k: 10
- Model load and one warmup query per variant excluded from latency
- Sources: historical tickets and runbooks; log/metric evidence excluded
- Small synthetic test set; queries from one incident are related
- BM25 remains the API default because E4 lowers ranking quality and increases latency on this set

| Variant | Recall@5 | Precision@5 | MRR@10 | nDCG@5 | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|
| E1 BM25 | 0.5833 | 0.3083 | 0.7872 | 0.5879 | 23.6 | 92.1 |
| E3 Hybrid RRF | 0.4375 | 0.2250 | 0.6792 | 0.4484 | 108.8 | 191.4 |
| E4 Rerank | 0.1667 | 0.0750 | 0.2641 | 0.1705 | 1131.6 | 1526.6 |
| E4 Rewrite + Rerank | 0.1250 | 0.0500 | 0.2264 | 0.1405 | 1059.4 | 1694.8 |

## Delta versus E1 and E3

| Variant | Baseline | Recall@5 | nDCG@5 | p50 ms |
|---|---|---:|---:|---:|
| E4 Rerank | E1 BM25 | -0.4167 | -0.4174 | +1108.1 |
| E4 Rerank | E3 Hybrid RRF | -0.2708 | -0.2779 | +1022.9 |
| E4 Rewrite + Rerank | E1 BM25 | -0.4583 | -0.4473 | +1035.8 |
| E4 Rewrite + Rerank | E3 Hybrid RRF | -0.3125 | -0.3078 | +950.6 |
