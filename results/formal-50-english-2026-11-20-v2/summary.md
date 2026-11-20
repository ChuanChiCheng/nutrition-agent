# Evaluation Summary

Run mode: `formal`

| Controller | Episodes | Accuracy | Mean turns | Mean model calls | Mean latency (ms) | p95 latency (ms, nearest rank) | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| agent | 150 | 38.0% (57/150) | 1.37 | 1.81 | 3606.7 | 6404 | 6739.0 |
| baseline | 50 | 50.0% (25/50) | 1.34 | 1.00 | 3061.3 | 6249 | 3889.6 |

## Agent repeat metrics

- Repeat 1 accuracy: 42.0%.
- Repeat 2 accuracy: 36.0%.
- Repeat 3 accuracy: 36.0%.
- pass@3: 48.0% across 50 tasks.
- pass^3: 28.0% across 50 tasks.
- Flipped task IDs: A02, A03, A04, A05, A06, A07, N05, P01, P03, Q04.
