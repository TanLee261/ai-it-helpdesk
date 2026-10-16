# E3 BM25 + BGE-M3 RRF

- Query count: 21
- Split: test
- Top K: 10
- Candidate K per branch: 100
- Recall@5: 0.5079
- Recall@10: 0.5317
- Precision@5: 0.2381
- MRR@10: 0.9048
- nDCG@5: 0.5805

## Notes

- Evaluation uses available evidence only: runbook documents and historical ticket documents.
- Log and metric evidence IDs are excluded until those sources are ingested as knowledge documents.

## Metrics by category

| Category | Queries | Recall@5 | Precision@5 | MRR@10 | nDCG@5 |
|---|---:|---:|---:|---:|---:|
| database | 9 | 0.5741 | 0.3111 | 0.8889 | 0.6051 |
| network | 6 | 0.5000 | 0.2000 | 1.0000 | 0.6131 |
| server_api | 6 | 0.4167 | 0.1667 | 0.8333 | 0.5110 |
