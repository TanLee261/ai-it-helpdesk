# E2 BGE-M3 dense baseline

- Query count: 21
- Split: test
- Top K: 10
- Candidate K per branch: 100
- Recall@5: 0.3492
- Recall@10: 0.4048
- Precision@5: 0.1524
- MRR@10: 0.5847
- nDCG@5: 0.3639

## Notes

- Evaluation uses available evidence only: runbook documents and historical ticket documents.
- Log and metric evidence IDs are excluded until those sources are ingested as knowledge documents.

## Metrics by category

| Category | Queries | Recall@5 | Precision@5 | MRR@10 | nDCG@5 |
|---|---:|---:|---:|---:|---:|
| database | 9 | 0.3148 | 0.1556 | 0.4929 | 0.3028 |
| network | 6 | 0.4167 | 0.1667 | 0.7238 | 0.4483 |
| server_api | 6 | 0.3333 | 0.1333 | 0.5833 | 0.3710 |
