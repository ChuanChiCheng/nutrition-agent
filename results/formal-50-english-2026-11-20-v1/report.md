# Formal 50-question evaluation report

Run: `formal-50-english-2026-11-20-v1`

**Execution completed: 50 questions, 200 unique attempts, all scored.** These are live model results, not a fake-client demonstration. The frozen controller was `gpt-6-luna` with medium reasoning; the configured response judge was `gpt-6.1-terra` with low reasoning. Program commit: `5c3bdcb47fffb4248a9a229c94a3aaeb01bd2b1e`.

## Results and interpretation

Raw overall accuracy was **0/150 (0%) for Agent** and **16/50 (32%) for baseline**. Do not interpret these numbers as a clean model-capability ranking: inspection found that the harness captures only the top-level `message`/`reply`, excluding structured results that the actual terminal renderer displays. In particular, approval/rejection responses can overwrite the captured reply with null. The same extraction rule affects both controllers, but their response structures differ.

These results document this exact implementation and grading path. They are useful diagnostic evidence; response-capture correctness must be repaired and verified before drawing a fair end-user comparison. No attempts have been replaced, rescored, or rerun to improve the result.

## Raw generated summary

### Metrics

Run mode: `formal`

| Controller | Episodes | Accuracy | Mean turns | Mean model calls | Mean latency (ms) | p95 latency (ms, nearest rank) | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| agent | 150 | 0.0% (0/150) | 1.35 | 1.97 | 4252.9 | 7839 | 7410.1 |
| baseline | 50 | 32.0% (16/50) | 1.18 | 1.02 | 3761.4 | 7618 | 3729.5 |

### Repeat metrics

- Repeat 1 accuracy: 0.0%.
- Repeat 2 accuracy: 0.0%.
- Repeat 3 accuracy: 0.0%.
- pass@3: 0.0% across 50 tasks.
- pass^3: 0.0% across 50 tasks.
- Flipped task IDs: none.


## Component checks

| Controller | Final state passed | Action order passed | Response passed | Null final replies | Controller failures |
|---|---:|---:|---:|---:|---:|
| agent | 143/150 | 122/150 | 0/150 | 50 | 0 |
| baseline | 42/50 | 28/50 | 16/50 | 8 | 5 |

A state pass alone can mean correctly leaving existing data unchanged; it does not prove that the requested explanation or workflow succeeded. All three checks are required for overall success.

## Evidence-backed failure analysis

- **Response capture:** Agent P01 repeat 1 successfully called `preview_preparation`, displayed the preview, and received the scripted rejection. The approval result had no top-level message; the final captured reply became null. C01 repeat 1 similarly previewed and confirmed a correction but ended with a null captured reply. In total, 50 Agent attempts and eight baseline attempts had null final replies. The relevant code is `nutrition_eval/episode.py::_reply` and its `record` function; the terminal instead uses `nutrition_demo/display.py::render`.
- **Generic displayed answer:** N01 Agent repeat 1 called `get_profile` and returned “Results from the shared application service follow.” The captured reply contained no actual values or target comparison, so the response rubric failed. The model-generated free text is deliberately not used by the application; rendering service data and satisfying the requested explanation require separate consideration.
- **Unnecessary clarification:** M01 Agent repeat 1 called `list_inventory` and asked the inventory question rather than recording the explicitly identified meal. No scripted inventory answer was available. U01 repeat 1 searched events, then asked which meal should be corrected rather than explaining that the requested nutrition was unavailable. These trace observations are genuine task/workflow issues beyond null-reply capture.
- **Baseline errors:** Four attempts returned invalid structured actions, and one failed the actual-consumption permission check. These five attempts remain failures in the denominator.

The automatically generated first-failure paragraph and trace are preserved in `failure_analysis.md` and `failure_trace.md`. The observations above expand that diagnosis without changing the frozen results.

## Per-question outcomes

| Question | Agent passes / 3 | Baseline passes / 1 |
|---|---:|---:|
| N01 | 0 | 0 |
| N02 | 0 | 1 |
| N03 | 0 | 1 |
| N04 | 0 | 0 |
| N05 | 0 | 1 |
| N06 | 0 | 1 |
| N07 | 0 | 1 |
| N08 | 0 | 1 |
| N09 | 0 | 1 |
| N10 | 0 | 0 |
| P01 | 0 | 0 |
| P02 | 0 | 0 |
| P03 | 0 | 0 |
| P04 | 0 | 0 |
| P05 | 0 | 0 |
| P06 | 0 | 0 |
| P07 | 0 | 0 |
| P08 | 0 | 0 |
| A01 | 0 | 0 |
| A02 | 0 | 0 |
| A03 | 0 | 0 |
| A04 | 0 | 0 |
| A05 | 0 | 0 |
| A06 | 0 | 0 |
| A07 | 0 | 0 |
| M01 | 0 | 1 |
| M02 | 0 | 1 |
| M03 | 0 | 1 |
| M04 | 0 | 1 |
| M05 | 0 | 1 |
| M06 | 0 | 0 |
| M07 | 0 | 1 |
| M08 | 0 | 0 |
| C01 | 0 | 0 |
| C02 | 0 | 0 |
| C03 | 0 | 0 |
| C04 | 0 | 0 |
| C05 | 0 | 0 |
| C06 | 0 | 0 |
| C07 | 0 | 0 |
| C08 | 0 | 0 |
| C09 | 0 | 0 |
| C10 | 0 | 0 |
| Q01 | 0 | 1 |
| Q02 | 0 | 0 |
| Q03 | 0 | 1 |
| Q04 | 0 | 0 |
| Q05 | 0 | 1 |
| U01 | 0 | 0 |
| U02 | 0 | 0 |

## Usage and reproducibility

Controller input + output tokens across all attempts: **1297993**. This is token usage, not a dollar-cost estimate. Judge usage is separate: 835360 input tokens and 6881 output tokens. Some attempts had no final reply and were deterministically failed without a judge call.

All 200 controller attempts and 200 scored records reconcile. Each question has three Agent attempts and one baseline attempt. Source/config hashes, the fixed clock, dataset hash, migration checksums, SDK/tool versions, resource limits, and judge prompt/schema are recorded in `status.json` and episode metadata. API keys and database credentials are excluded.

## Artifacts

- [Raw summary](summary.md)
- [All scored episodes and traces](episodes.jsonl)
- [Status and frozen metadata](status.json)
- [First failure trace](failure_trace.md)
- [Automatic failure analysis](failure_analysis.md)

## Recommended next step

Fix response capture to grade the complete user-visible rendered response and preserve relevant preview/confirmation content. Add tests proving the grader sees exactly what the user sees, then create a new versioned run. Keep this run intact as the original diagnostic result. A new controller comparison would require another paid run; no additional run was started.
