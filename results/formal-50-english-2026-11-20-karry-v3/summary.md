# Evaluation Summary

Run mode: `formal`

| Controller | Episodes | Accuracy | Mean turns | Mean model calls | Mean latency (ms) | p95 latency (ms, nearest rank) | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| agent | 150 | 38.0% (57/150) | 1.38 | 1.88 | 3170.4 | 6597 | 7021.5 |
| baseline | 50 | 60.0% (30/50) | 1.34 | 1.00 | 2753.2 | 5634 | 3883.0 |

## Agent repeat metrics

- Repeat 1 accuracy: 38.0%.
- Repeat 2 accuracy: 34.0%.
- Repeat 3 accuracy: 42.0%.
- pass@3: 52.0% across 50 tasks.
- pass^3: 28.0% across 50 tasks.
- Flipped task IDs: A01, A02, A03, A05, A07, N05, N07, P02, P05, P06, Q01, Q02.
