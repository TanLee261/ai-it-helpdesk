# E3 RRF dev tuning

- Dev queries: 24
- RRF constant: 60
- Final output top_k: 10 (metrics at 5 and 10)

| Candidate K per branch | Recall@5 | Precision@5 | MRR@10 | nDCG@5 |
|---:|---:|---:|---:|---:|
| 20 | 0.4792 | 0.2333 | 0.8201 | 0.5287 |
| 50 | 0.4792 | 0.2333 | 0.8347 | 0.5334 |
| 100 | 0.4931 | 0.2417 | 0.8403 | 0.5441 |

- Selected candidate_k: 100 (highest nDCG@5; Recall@5 and smaller K break ties).
