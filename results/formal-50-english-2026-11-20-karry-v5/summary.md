# Evaluation Summary

Run mode: `formal`

| Controller | Episodes | Accuracy | Mean turns | Mean model calls | Mean latency (ms) | p95 latency (ms, nearest rank) | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| agent | 150 | 96.7% (145/150) | 1.51 | 2.04 | 3496.9 | 5876 | 9158.8 |
| baseline | 50 | 86.0% (43/50) | 1.38 | 1.02 | 2763.3 | 5332 | 4504.1 |

## Agent repeat metrics

- Repeat 1 accuracy: 96.0%.
- Repeat 2 accuracy: 96.0%.
- Repeat 3 accuracy: 98.0%.
- pass@3: 100.0% across 50 tasks.
- pass^3: 94.0% across 50 tasks.
- Flipped task IDs: A06, A07, P08.
