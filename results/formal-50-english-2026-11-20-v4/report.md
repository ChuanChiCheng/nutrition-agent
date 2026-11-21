# Formal 50-question evaluation report (v4, after the reply-completeness fixes)

Run ID: `formal-50-english-2026-11-20-v4`. Program commit: `0ad1e3297e6dc7648f3c81994850b655d3f98c25` (branch `karry_test`). Tool version: `v1.1`.

**Superseded by [v5](../formal-50-english-2026-11-20-v5/report.md).** This run is kept because it revealed a tool-schema problem that unfairly lowered the baseline.

## Outcome

| Controller | Episodes | Accuracy | Mean turns | Mean model calls | Mean latency (ms) | p95 latency (ms) | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| agent | 150 | 100.0% (150/150) | 1.52 | 2.07 | 3088.9 | 5475 | 9285.0 |
| baseline | 50 | 66.0% (33/50) | 1.38 | 1.02 | 2724.1 | 5777 | 4483.7 |

- Agent pass@3: 100%. Agent pass^3: 100%. No tasks flipped.
- Component checks for the baseline: state 50/50, order 34/50, reply 33/50.

## What changed since v3

Commit `0ad1e32` made the application-rendered replies state the facts users ask for:

| Change | Applies to |
|---|---|
| `batch_summary` adds an exact per-box check against the saved meal targets | Both controllers |
| New `check_meal_targets` tool for hypothetical values | Both controllers |
| Meal confirmations state the batch, date, meal, and remaining boxes | Both controllers |
| Addon confirmations list the saved items | Both controllers |
| Empty lookups say that nothing is known | Both controllers |
| A one-time reminder to answer through tools when the first response calls none, plus guidance to use stated cooking usage as given | Agent only |

Tasks, rubrics, fixtures, and the judge did not change.

## Baseline regression

The baseline fell from 8/10 nutrition tasks in v3 to 2/10 here. Eight nutrition tasks (N01–N04, N06–N08, N10) and Q02 failed with "Baseline returned an invalid structured action".

A diagnostic call on N01 and N02 showed the cause. The baseline chose `check_meal_targets` or `batch_summary` with `{"batch_id": "batch-1"}`. Both schemas rejected that argument, so the action was invalid even though the baseline's reply text was correct. The baseline makes a single attempt, so it cannot recover from an invalid action.

v5 lets both tools accept a `batch_id`. In v5, the same two calls are valid.
