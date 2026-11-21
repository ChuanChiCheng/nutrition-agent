# Formal 50-question evaluation report (v5, final for the take-home)

Run ID: `formal-50-english-2026-11-20-v5`

**Completed: all 50 questions, 200 unique attempts, and 200 scored records.** The Agent ran each task three times and the baseline ran each task once. No attempt was replaced or selectively rerun. The run took about 17.5 minutes (19:41–19:59 Pacific).

## Outcome

- Agent: **145/150 successful attempts (96.7%)**.
- Baseline: **43/50 successful attempts (86.0%)**.
- Agent pass@3: **50/50 (100%)**. Agent pass^3: **47/50 (94%)**.
- Flipped tasks: A06, A07, P08.
- No failed controller episodes and no empty replies for either controller.

## Frozen revisions

- Program commit: `2f14d8a450b2bd4dd1a197b803c0d7552bceedeb` (branch `karry_test`). Tool version: `v1.2`.
- Task format: lecture-slide fields (`id`, `type`, `question`, `rubric`). Taskset SHA-256: `1632bf3a5bfe52e415bde7b783626f8f82a8fb493922166ae33ebf4f7d496fa2`. Tasks, rubrics, and fixtures are the same as in v3.
- Dataset: `nutrition-eval-50-v2`. Baseline: `fixed-workflow-v2`. Judge adapter: `nutrition-reply-judge-v2`.
- Controller: `gpt-6-luna` with medium reasoning. Judge: `gpt-6.1-terra` with low reasoning.
- Fixed clock: November 18, 2026, 07:30 America/Los_Angeles.

## Aggregate metrics

| Controller | Episodes | Accuracy | Mean turns | Mean model calls | Mean latency (ms) | p95 latency (ms, nearest rank) | Mean tokens (input + output) |
|---|---:|---:|---:|---:|---:|---:|---:|
| agent | 150 | 96.7% (145/150) | 1.51 | 2.04 | 3496.9 | 5876 | 9158.8 |
| baseline | 50 | 86.0% (43/50) | 1.38 | 1.02 | 2763.3 | 5332 | 4504.1 |

Agent accuracy by repeat: 96%, 96%, and 98%.

## Component checks

| Controller | State | Order | Reply rubric | Failed controller episodes |
|---|---:|---:|---:|---:|
| agent | 150/150 | 149/150 | 145/150 | 0 |
| baseline | 50/50 | 43/50 | 43/50 | 0 |

## Results by task type and category

| Task type | Agent | Baseline |
|---|---:|---:|
| `tool` (33 tasks) | 94/99 | 26/33 |
| `rubric` (15 tasks) | 45/45 | 15/15 |
| `unanswerable` (2 tasks) | 6/6 | 2/2 |

| Category | Agent | Baseline |
|---|---:|---:|
| nutrition | 30/30 | 10/10 |
| preparation | 22/24 | 1/8 |
| addons | 18/21 | 7/7 |
| meal_logging | 24/24 | 8/8 |
| corrections | 30/30 | 10/10 |
| queries | 15/15 | 5/5 |
| unanswerable | 6/6 | 2/2 |

All seven baseline failures are preparation tasks (P01, P02, P04–P08). Instead of producing the preview, the baseline asked for missing details, so the required preview → approval order never happened.

## Traced failure: P08, Agent repeat 2

**The task.** P08 is an edge case. The user asks for a preview of cooking 500 g raw chicken and 250 g dry rice, "allocated exactly to 3 lunch boxes and 1 curry-only box", and then rejects that preview.

**What failed.** The state check passed. The order check failed because preview → approval never happened, and the reply rubric failed.

**The step that went wrong.** The agent's first and only model call chose `ask_user` with the topic `quantity` instead of calling `preview_preparation`. The application rendered its fixed question for that topic: "Provide the actual quantity, unit, and raw or cooked state." The user had already given that information. The scripted user has no answer to the question, so the episode ended without a preview.

**Why.** The request does not say how the 500 g of chicken is split between the lunch boxes and the curry-only box. The agent was right that something was missing. However, clarification topics come from a fixed list with no allocation question, so the agent fell back to the generic quantity question.

**How the other two runs went.** In repeats 1 and 3, the agent inferred a split instead: 375 g chicken and 250 g rice for the lunch boxes, and 125 g chicken for the curry-only box. In both runs, the service rejected the first `preview_preparation` call as invalid. The agent corrected it on the next call, and the preview was shown.

**Possible fixes.**
- Add an allocation clarification topic.
- Show a proposed split in the preview for the user to approve or reject.

## Judge inconsistency in the other four Agent failures

The other four Agent failures (A06 repeats 1–2, A07 repeat 3, and P08 repeat 1) are rejection tasks.

**Same behavior, different grades.** In each of these runs, the agent showed the correct preview, the user rejected it, and the final reply was "Preview rejected. Inventory and meal records remain unchanged." That reply does not repeat the rejected quantities, which only appear in the preview. Passing repeats of the same tasks did exactly the same thing.

**The clearest case.** The A07 repeat 3 transcript is identical to the passing repeat 2 transcript, apart from the repeat number. The judge passed one and failed the other. These failures therefore reflect judge variance on whether the preview counts, not different agent behavior.

**A product fix.** The rejection message could restate what was rejected.

## How v3 became v5

| Run | Commit | Agent accuracy | Agent pass@3 / pass^3 | Baseline accuracy |
|---|---|---:|---:|---:|
| v3 | `db6790e` | 38.0% (57/150) | 52% / 28% | 60.0% (30/50) |
| v4 | `0ad1e32` | 100.0% (150/150) | 100% / 100% | 66.0% (33/50) |
| v5 | `2f14d8a` | 96.7% (145/150) | 100% / 94% | 86.0% (43/50) |

**v3.** In 93 failed Agent attempts, the final state was correct every time; what failed was the reply rubric. By design, the agent never shows unchecked model prose. Its replies are built only from tool results under fixed templates, and those templates often left out the facts the user asked for.

**v3 → v4 (`0ad1e32`).** These changes keep that safety design and apply to both controllers:
- Application-computed meal-target checks.
- A `check_meal_targets` tool for hypothetical values.
- Meal confirmations that state the batch, date, meal, and remaining boxes.
- Addon confirmations that list the saved items.
- Explicit "no record" messages.

Two further changes apply only to the Agent:
- A one-time reminder to answer through tools when its first response calls none.
- Guidance to use stated cooking usage as given.

**v4 → v5 (`2f14d8a`).** In v4, the baseline called the new tools with a `batch_id`, which the schemas rejected. Its nutrition score fell from 8/10 to 2/10 (see the [v4 report](../formal-50-english-2026-11-20-v4/report.md)). Both tools now accept a `batch_id`.

**Caveats.** These fixes were designed by reading v3 failures on these same 50 tasks, so v5 overstates how well the changes would generalize to new tasks. The guidance about stated cooking usage was added only to the Agent's instructions, and the baseline's 1/8 preparation score reflects that missing guidance.

## Per-question outcomes

| Question | Agent passes / 3 | Baseline passes / 1 |
|---|---:|---:|
| N01–N10 | 3 each | 1 each |
| P01, P02 | 3 | 0 |
| P03 | 3 | 1 |
| P04–P07 | 3 | 0 |
| P08 | 1 | 0 |
| A01–A05 | 3 | 1 |
| A06 | 1 | 1 |
| A07 | 2 | 1 |
| M01–M08 | 3 | 1 |
| C01–C10 | 3 | 1 |
| Q01–Q05 | 3 | 1 |
| U01, U02 | 3 | 1 |

## Usage

Controller tokens (input + output) totalled **1,599,027**: 1,373,821 for the Agent and 225,206 for the baseline. Judge usage is counted separately: **1,342,274 input tokens** and **11,233 output tokens**. These are token counts, not dollar costs.

## Files

- [Generated metrics summary](summary.md)
- [All 200 attempts with traces, scores, and metrics](episodes.jsonl)
- [Run status and frozen metadata](status.json)
- [v3 report](../formal-50-english-2026-11-20-v3/report.md) and [v4 report](../formal-50-english-2026-11-20-v4/report.md)

## Limitations

- **Synthetic data.** All tasks use synthetic data, and several are quantity or date variants of each other.
- **No held-out set.** The fixes were tuned on these 50 tasks, so a separate test set is needed to measure how well they generalize.
- **Uneven sampling.** The baseline was run once per question.
- **Judge variance.** The model judge can grade identical transcripts differently, as A07 shows.
