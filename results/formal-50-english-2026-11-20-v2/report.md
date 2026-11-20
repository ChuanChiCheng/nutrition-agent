# Updated formal 50-question evaluation report

Run ID: `formal-50-english-2026-11-20-v2`

**Completed: all 50 questions, 200 unique attempts, and 200 scored records.** Agent ran each task three times; baseline ran each once. No failed attempt was replaced or selectively rerun.

## Outcome

- Agent: **57/150 successful attempts (38%)**.
- Baseline: **25/50 successful attempts (50%)**.
- Agent pass@3: **24/50 questions (48%)** passed at least once.
- Agent pass^3: **14/50 questions (28%)** passed all three times.
- All final responses were captured: **zero null replies for either controller**.

The baseline had a higher observed episode accuracy in this run. These are descriptive results on this fixed synthetic dataset, not proof of general superiority. The Agent sample includes three attempts per question while baseline has one; judge-based response scoring can vary.

## Frozen revisions

- Program commit: `b57744d38d642646e8df3b4d0f401ef5d8de2de8`.
- Dataset/task: `nutrition-eval-50-v2`; fixture state: `inventory-confirmed-v2`.
- Baseline: `fixed-workflow-v2`; response capture: `terminal-render-v1`.
- Judge adapter: `nutrition-reply-judge-v2`.
- Configured controller: `gpt-6-luna`, medium reasoning; configured judge: `gpt-6.1-terra`, low reasoning.
- Fixed application clock: November 18, 2026, 07:30 America/Los_Angeles.

## Aggregate metrics

### Generated summary

Run mode: `formal`

| Controller | Episodes | Accuracy | Mean turns | Mean model calls | Mean latency (ms) | p95 latency (ms, nearest rank) | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| agent | 150 | 38.0% (57/150) | 1.37 | 1.81 | 3606.7 | 6404 | 6739.0 |
| baseline | 50 | 50.0% (25/50) | 1.34 | 1.00 | 3061.3 | 6249 | 3889.6 |

### Agent repeat metrics

- Repeat 1 accuracy: 42.0%.
- Repeat 2 accuracy: 36.0%.
- Repeat 3 accuracy: 36.0%.
- pass@3: 48.0% across 50 tasks.
- pass^3: 28.0% across 50 tasks.
- Flipped task IDs: A02, A03, A04, A05, A06, A07, N05, P01, P03, Q04.


## Component checks

A run succeeds only if all three components pass. A correct unchanged state does not establish that a query was answered correctly.

| Controller | State | Order | Response | Failed controller episodes | Null replies |
|---|---:|---:|---:|---:|---:|
| agent | 149/150 | 128/150 | 57/150 | 0 | 0 |
| baseline | 49/50 | 35/50 | 25/50 | 7 | 0 |

## Results by category

| Category | Agent successes / attempts | Baseline successes / attempts |
|---|---:|---:|
| nutrition | 5/30 | 4/10 |
| preparation | 3/24 | 0/8 |
| addons | 11/21 | 1/7 |
| meal_logging | 0/24 | 6/8 |
| corrections | 30/30 | 10/10 |
| queries | 8/15 | 4/5 |
| unanswerable | 0/6 | 0/2 |

## Verification of the fixes

- **Full response capture:** zero null final responses versus 50 Agent and eight baseline null replies in v1. The judge now receives rendered service output and approval/rejection responses.
- **Correction continuation:** all ten baseline correction tasks executed `find_events` followed by `preview_correction`, and all ten passed. Agent passed all 30 correction attempts.
- **Clarification context:** deterministic pre-run tests validated baseline M08 with a batch question and answer. In this live run the baseline instead called `log_meal` directly with an ambiguous batch selection; the application rejected it. This is a remaining action-selection failure, not the previously fixed loss of context after a clarification.
- **Fixture alignment:** all v2 fixtures explicitly provide confirmed inventory, with preparation at cooking stage and other tasks ready. This is a dataset change and is recorded in the v2 hash.

## Observed failure analysis

**N01, Agent repeat 1:** the task asked for four nutrient values, targets, and overall target status. The trace contains a successful `find_batches` call. The rendered reply displays only the batch candidate and remaining boxes, not the requested nutrients or target comparison. State and order passed, but the response rubric failed. The failure is now visible in the actual rendered response, rather than an empty capture. A useful improvement would be to retrieve and present the required batch nutrition and targets before ending the answer.

Other remaining patterns:

- Preparation: Agent passed 3/24 and baseline 0/8. Several attempts asked for quantity or details rather than producing the required preview. Some preparation requests leave allocation details open; low success can reflect the interaction between model clarification and the finite scripted dialogue. Requests and rubrics were not changed to make the rerun easier.
- Meal logging: Agent passed 0/24, even though many writes completed. For example M08 repeat 1 displays meal nutrients and an event ID but does not explicitly confirm all requested batch/date/meal details in the rendered reply. Baseline passed 6/8. This exposes response completeness limitations in the product presentation.
- Addons: Agent passed 11/21 and baseline 1/7. Some confirmations say a plan was saved without repeating exact addon quantities. The judge can consider the preview, but criterion-level outcomes still vary; inspect individual reasons rather than treating all addon failures as failed writes.
- Missing information: neither controller passed these questions. U01 Agent repeat 1 displayed a zero-event daily summary without clearly stating that the requested meal nutrition was unknown. The baseline said it would look up the meal but did not complete the explanation.
- Baseline controller failures: six invalid structured actions and one rejected ambiguous meal write. All seven remain in the denominator.

## Comparison with the preserved first run

| Metric | Original v1 | Corrected v2 |
|---|---:|---:|
| Agent accuracy | 0/150 (0%) | 57/150 (38%) |
| Baseline accuracy | 16/50 (32%) | 25/50 (50%) |
| Agent null replies | 50 | 0 |
| Baseline null replies | 8 | 0 |

This is not a controlled model-improvement comparison: response capture, judge conversation, baseline behavior, fixture starting states, and random model outputs changed. The v1 scores were compromised by capture errors. Keep v1 as diagnostic history; use v2 to describe this corrected configuration.

## Per-question outcomes

| Question | Agent passes / 3 | Baseline passes / 1 |
|---|---:|---:|
| N01 | 0 | 0 |
| N02 | 0 | 1 |
| N03 | 0 | 1 |
| N04 | 0 | 0 |
| N05 | 2 | 1 |
| N06 | 0 | 0 |
| N07 | 3 | 0 |
| N08 | 0 | 0 |
| N09 | 0 | 1 |
| N10 | 0 | 0 |
| P01 | 1 | 0 |
| P02 | 0 | 0 |
| P03 | 2 | 0 |
| P04 | 0 | 0 |
| P05 | 0 | 0 |
| P06 | 0 | 0 |
| P07 | 0 | 0 |
| P08 | 0 | 0 |
| A01 | 3 | 0 |
| A02 | 2 | 0 |
| A03 | 1 | 0 |
| A04 | 2 | 0 |
| A05 | 1 | 0 |
| A06 | 1 | 1 |
| A07 | 1 | 0 |
| M01 | 0 | 1 |
| M02 | 0 | 1 |
| M03 | 0 | 1 |
| M04 | 0 | 1 |
| M05 | 0 | 1 |
| M06 | 0 | 0 |
| M07 | 0 | 1 |
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
| Q01 | 0 | 1 |
| Q02 | 0 | 0 |
| Q03 | 3 | 1 |
| Q04 | 2 | 1 |
| Q05 | 3 | 1 |
| U01 | 0 | 0 |
| U02 | 0 | 0 |

## Usage and artifact integrity

Total controller tokens (input + output): **1205337**. Judge usage is separate: **1284006 input tokens** and **11746 output tokens**. These are usage counts, not dollar-cost estimates.

All 200 attempts have grades and distinct task/controller/repeat keys. The stored dataset hash matches the executed formal taskset. Frozen configuration, source hash, program commit, model/tool/SDK versions, migration checksums, judge prompt/schema, and limits are preserved in metadata. Credentials are not included.

## Files

- [Generated metrics summary](summary.md)
- [All 200 attempts, traces, scores, and metrics](episodes.jsonl)
- [Run status and frozen metadata](status.json)
- [First failure trace](failure_trace.md)
- [Automatic first-failure analysis](failure_analysis.md)
- [Original v1 report](../formal-50-english-2026-11-20-v1/report.md)

## Limitations

The 50 synthetic tasks include repeated quantity/date variants and do not establish broad safety or real-world coverage. Baseline has only one attempt per question. Response grades use a model judge and may vary. Predefined dialogues cannot answer arbitrary additional clarification questions. Product rendering can omit facts even when state changes are correct; those remaining failures must not be confused with the fixed capture bug.
