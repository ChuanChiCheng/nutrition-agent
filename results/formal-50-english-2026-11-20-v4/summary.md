# Evaluation Summary

Run mode: `formal`

| Controller | Episodes | Accuracy | Mean turns | Mean model calls | Mean latency (ms) | p95 latency (ms, nearest rank) | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| agent | 150 | 74.0% (111/150) | 1.36 | 2.05 | 3326.5 | 6069 | 7254.9 |
| baseline | 50 | 62.0% (31/50) | 1.34 | 1.00 | 3031.9 | 5505 | 3895.7 |

## Component outcomes

Counts are passed episodes / attempts. Component counts can overlap; overall success requires state, order, and response to pass.

| Controller | Category | Overall | State | Order | Response |
|---|---|---:|---:|---:|---:|
| agent | addons | 21/21 | 21/21 | 21/21 | 21/21 |
| agent | corrections | 29/30 | 30/30 | 30/30 | 29/30 |
| agent | meal_logging | 24/24 | 24/24 | 24/24 | 24/24 |
| agent | nutrition | 21/30 | 30/30 | 30/30 | 21/30 |
| agent | preparation | 0/24 | 24/24 | 0/24 | 7/24 |
| agent | queries | 10/15 | 15/15 | 15/15 | 10/15 |
| agent | unanswerable | 6/6 | 6/6 | 6/6 | 6/6 |
| baseline | addons | 7/7 | 7/7 | 7/7 | 7/7 |
| baseline | corrections | 10/10 | 10/10 | 10/10 | 10/10 |
| baseline | meal_logging | 6/8 | 6/8 | 6/8 | 6/8 |
| baseline | nutrition | 2/10 | 10/10 | 3/10 | 2/10 |
| baseline | preparation | 0/8 | 8/8 | 0/8 | 0/8 |
| baseline | queries | 4/5 | 5/5 | 4/5 | 4/5 |
| baseline | unanswerable | 2/2 | 2/2 | 2/2 | 2/2 |

## Agent repeat metrics

- Repeat 1 accuracy: 72.0%.
- Repeat 2 accuracy: 74.0%.
- Repeat 3 accuracy: 76.0%.
- pass@3: 78.0% across 50 tasks.
- pass^3: 70.0% across 50 tasks.
- Flipped task IDs: C03, Q01, Q02, Q04.
