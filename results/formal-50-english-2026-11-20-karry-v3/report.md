# Formal 50-question evaluation report (v3, lecture-slide task format)

Run ID: `formal-50-english-2026-11-20-v3` on branch `karry_test` (stored as `formal-50-english-2026-11-20-karry-v3` so it does not clash with the team's runs of the same name)

**Completed: all 50 questions, 200 unique attempts, and 200 scored records.** The Agent ran each task three times and the baseline ran each task once. No failed attempt was replaced or selectively rerun. The run took about 17.5 minutes (18:54–19:12 Pacific).

## Outcome

- Agent: **57/150 successful attempts (38%)**.
- Baseline: **30/50 successful attempts (60%)**.
- Agent pass@3: **26/50 questions (52%)** passed at least once.
- Agent pass^3: **14/50 questions (28%)** passed all three times.
- Both controllers returned a final reply on every attempt.

The baseline had the higher observed accuracy in this run. These are descriptive results on a fixed synthetic dataset, not proof that one controller is generally better. The Agent was run three times per question and the baseline once, and reply scoring uses a model judge that can vary.

## Frozen revisions

- Program commit: `db6790e4c0ef9fb92019f1c468c9ba1256186b9e` (branch `karry_test`).
- Task format: lecture-slide fields (`id`, `type`, `question`, `rubric`).
- Taskset SHA-256: `1632bf3a5bfe52e415bde7b783626f8f82a8fb493922166ae33ebf4f7d496fa2`.
- Dataset and tasks: `nutrition-eval-50-v2`. Fixture state: `inventory-confirmed-v2`.
- Baseline: `fixed-workflow-v2`. Response capture: `terminal-render-v1`. Judge adapter: `nutrition-reply-judge-v2`.
- Controller: `gpt-6-luna` with medium reasoning. Judge: `gpt-6.1-terra` with low reasoning.
- Fixed application clock: November 18, 2026, 07:30 America/Los_Angeles.

## Aggregate metrics

| Controller | Episodes | Accuracy | Mean turns | Mean model calls | Mean latency (ms) | p95 latency (ms, nearest rank) | Mean tokens (input + output) |
|---|---:|---:|---:|---:|---:|---:|---:|
| agent | 150 | 38.0% (57/150) | 1.38 | 1.88 | 3170.4 | 6597 | 7021.5 |
| baseline | 50 | 60.0% (30/50) | 1.34 | 1.00 | 2753.2 | 5634 | 3883.0 |

### Agent repeat metrics

- Accuracy by repeat: 38% (repeat 1), 34% (repeat 2), 42% (repeat 3).
- pass@3: 52% (26/50). pass^3: 28% (14/50).
- 12 flipped tasks: A01, A02, A03, A05, A07, N05, N07, P02, P05, P06, Q01, Q02.

## Component checks

An attempt succeeds only if all three components pass.

| Controller | State | Order | Reply rubric | Failed controller episodes |
|---|---:|---:|---:|---:|
| agent | 150/150 | 129/150 | 57/150 | 0 |
| baseline | 47/50 | 37/50 | 30/50 | 5 |

The five failed baseline episodes are four invalid structured actions (N06, M04, M05, Q01) and one ambiguous meal write that the application rejected (M08). All five stay in the denominator.

## Results by task type and category

| Task type | Agent | Baseline |
|---|---:|---:|
| `tool` (33 tasks) | 42/99 | 18/33 |
| `rubric` (15 tasks) | 15/45 | 12/15 |
| `unanswerable` (2 tasks) | 0/6 | 0/2 |

| Category | Agent | Baseline |
|---|---:|---:|
| nutrition | 3/30 | 8/10 |
| preparation | 3/24 | 0/8 |
| addons | 9/21 | 4/7 |
| meal_logging | 0/24 | 4/8 |
| corrections | 30/30 | 10/10 |
| queries | 12/15 | 4/5 |
| unanswerable | 0/6 | 0/2 |

## Traced failure: N01, Agent repeat 1

N01 asks whether the synthetic curry lunch batch meets the meal targets, and asks for all four nutrient values and their targets. **The step that went wrong was the agent's first and only model call.** It produced 135 output tokens, 53 of them reasoning, and no tool call. In the agent loop, a model response without a tool call ends the turn (`nutrition_demo/agent.py`, line 218). No tool had run and no workflow state was pending, so `_display` returned its fallback text: "Provide more details; query /inventory, /batches, or /daily." (line 168). **Why:** every request already sends the profile targets and the batch summary to the model as application context (lines 201–203). The model could therefore answer from that context in its own words. By design, however, the agent never displays unchecked model prose; it shows only tool results under fixed templates. Whatever the model wrote was dropped, and the judge saw no values, targets, or verdict.

The other two Agent attempts failed the same way at different points:
- **Repeat 2** called only `get_profile`, so the reply showed the targets but not the batch's nutrients.
- **Repeat 3** called only `find_batches`, so the reply showed the batch candidate and nothing else.

The baseline passed N01 with a single structured call. It chose `batch_summary`, and its structured `reply` field said that the batch meets all four targets (600/600 kcal, 40/40 g protein, 65/65 g carbohydrates, 20/20 g fat). That reply was displayed. The Agent loses this task because its prose is never shown, not because it lacks the data. Two changes could fix this:
- Add a tool that compares a batch with the meal targets and returns the verdict, and require target questions to use it.
- Display a final answer once it has been checked against the tool results.

## Comparison with v2

| Metric | v2 (pre-rename file) | v3 (slide format) |
|---|---:|---:|
| Agent accuracy | 57/150 (38%) | 57/150 (38%) |
| Baseline accuracy | 25/50 (50%) | 30/50 (60%) |
| Agent pass@3 | 48% | 52% |
| Agent pass^3 | 28% | 28% |
| Agent mean latency | 3606.7 ms | 3170.4 ms |
| Agent mean tokens | 6739.0 | 7021.5 |

Between v2 and v3, only the task file's field names changed, along with the loader that reads them. Questions, rubrics, fixtures, controllers, and the judge input are the same. The differences between the two runs are therefore run-to-run variation from the model and the judge:
- Agent accuracy stayed at 38%.
- The baseline moved by five tasks.
- A different set of tasks flipped.

## Per-question outcomes

| Question | Agent passes / 3 | Baseline passes / 1 |
|---|---:|---:|
| N01 | 0 | 1 |
| N02 | 0 | 1 |
| N03 | 0 | 1 |
| N04 | 0 | 0 |
| N05 | 1 | 1 |
| N06 | 0 | 0 |
| N07 | 2 | 1 |
| N08 | 0 | 1 |
| N09 | 0 | 1 |
| N10 | 0 | 1 |
| P01 | 0 | 0 |
| P02 | 1 | 0 |
| P03 | 0 | 0 |
| P04 | 0 | 0 |
| P05 | 1 | 0 |
| P06 | 1 | 0 |
| P07 | 0 | 0 |
| P08 | 0 | 0 |
| A01 | 1 | 0 |
| A02 | 1 | 1 |
| A03 | 1 | 1 |
| A04 | 0 | 1 |
| A05 | 1 | 0 |
| A06 | 3 | 0 |
| A07 | 2 | 1 |
| M01 | 0 | 1 |
| M02 | 0 | 1 |
| M03 | 0 | 1 |
| M04 | 0 | 0 |
| M05 | 0 | 0 |
| M06 | 0 | 1 |
| M07 | 0 | 0 |
| M08 | 0 | 0 |
| C01 | 3 | 1 |
| C02 | 3 | 1 |
| C03 | 3 | 1 |
| C04 | 3 | 1 |
| C05 | 3 | 1 |
| C06 | 3 | 1 |
| C07 | 3 | 1 |
| C08 | 3 | 1 |
| C09 | 3 | 1 |
| C10 | 3 | 1 |
| Q01 | 2 | 0 |
| Q02 | 1 | 1 |
| Q03 | 3 | 1 |
| Q04 | 3 | 1 |
| Q05 | 3 | 1 |
| U01 | 0 | 0 |
| U02 | 0 | 0 |

## Usage

Controller tokens (input + output) totalled **1,247,370**: 1,053,220 for the Agent and 194,150 for the baseline. Judge usage is counted separately: **1,285,899 input tokens** and **12,066 output tokens**. These are token counts, not dollar costs.

## Files

- [Generated metrics summary](summary.md)
- [All 200 attempts with traces, scores, and metrics](episodes.jsonl)
- [Run status and frozen metadata](status.json)
- [Automatic first-failure trace](failure_trace.md) and [analysis](failure_analysis.md)
- [v2 report](../formal-50-english-2026-11-20-v2/report.md)

## Limitations

- All tasks use synthetic data, and several are quantity or date variants of each other.
- The baseline has one attempt per question, so its accuracy is noisier than the Agent's.
- Replies are graded by a model judge, which can vary.
- Scripted dialogues cannot answer arbitrary extra clarifying questions.
- The product's fixed templates can leave out facts even when the state is correct, so the reply checks measure what the user actually sees.
