# E2 BGE-M3 dense baseline

- Query count: 24
- Split: test
- Top K: 10
- Candidate K per branch: 50
- Recall@5: 0.2292
- Recall@10: 0.2569
- Precision@5: 0.1000
- MRR@10: 0.3258
- nDCG@5: 0.2160

## Notes

- Evaluation uses available evidence only: runbook documents and historical ticket documents.
- Log and metric evidence IDs are excluded until those sources are ingested as knowledge documents.
