# E1 BM25 keyword baseline

- Query count: 24
- Split: test
- Top K: 10
- Candidate K per branch: 50
- Recall@5: 0.5833
- Recall@10: 0.6944
- Precision@5: 0.3083
- MRR@10: 0.7872
- nDCG@5: 0.5879

## Notes

- Evaluation uses available evidence only: runbook documents and historical ticket documents.
- Log and metric evidence IDs are excluded until those sources are ingested as knowledge documents.
