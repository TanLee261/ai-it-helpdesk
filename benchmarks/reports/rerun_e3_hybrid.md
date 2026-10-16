# E3 BM25 + BGE-M3 RRF

- Query count: 24
- Split: test
- Top K: 10
- Candidate K per branch: 50
- Recall@5: 0.3958
- Recall@10: 0.5208
- Precision@5: 0.2000
- MRR@10: 0.5615
- nDCG@5: 0.3831

## Notes

- Evaluation uses available evidence only: runbook documents and historical ticket documents.
- Log and metric evidence IDs are excluded until those sources are ingested as knowledge documents.
