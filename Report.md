# EEP 500D Take-home: Evaluation Harness

| Name | NetID |
|---|---|
| Karry Cheng | karryc |
| _TODO_ | _TODO_ |

## Submitted files

| Item | Location |
|---|---|
| 50 tasks | [`tasks.jsonl`](tasks.jsonl) |
| Evaluation script | [`nutrition_eval/`](nutrition_eval/), entry point `python -m nutrition_eval` |
| Results table with pass@3 and pass^3 | [Results](#results) below; the full run is in [`results/formal-50-english-2026-11-20-v5/`](results/formal-50-english-2026-11-20-v5/) |
| One paragraph explaining a failure | [Traced failure](#traced-failure-p08-agent-repeat-2) below |

## Tasks

- 50 tasks in the lecture-slide format (`id`, `type`, `question`, `rubric`): 33 `tool`, 15 `rubric`, 2 `unanswerable`.
- Edge cases (5): N09, N10, P08, M08, C10.
- Unanswerable (2): U01, U02.

## Evaluation script

One script runs the Agent (a tool-calling loop) and the non-agentic baseline (a fixed workflow that makes one structured model call) on all 50 tasks. The Agent runs 3 times per task and the baseline runs once:

```bash
docker compose --profile test up -d --wait db_test
docker compose --profile test run --build --rm --no-deps --volume "$PWD/results:/app/results" \
  --env "EVAL_PROGRAM_COMMIT=$(git rev-parse HEAD)" --entrypoint uv app \
  run --locked python -m nutrition_eval --tasks tasks.jsonl --config eval_config.json --output results/<new-dir>
```

## Results

Run `formal-50-english-2026-11-20-v5`: 200 scored attempts. The Agent ran 3 × 50 and the baseline ran 1 × 50.

| Metric | Agent | Baseline |
|---|---:|---:|
| Accuracy | **96.7%** (145/150) | **86.0%** (43/50) |
| Avg turns | 1.51 | 1.38 |
| Avg latency | 3,496.9 ms | 2,763.3 ms |
| p95 latency (nearest rank) | 5,876 ms | 5,332 ms |
| Avg tokens (input + output) | 9,158.8 | 4,504.1 |

| Agent, 3 runs × 50 tasks | Value |
|---|---:|
| **pass@3** (at least 1 of 3 runs passes) | **100%** (50/50) |
| **pass^3** (all 3 runs pass) | **94%** (47/50) |

**Tasks whose pass/fail outcome changes across runs:** A06, A07, P08.

## Traced failure: P08, Agent repeat 2

P08 is an edge case. It asks for a preview of cooking 500 g raw chicken and 250 g dry rice, "allocated exactly to 3 lunch boxes and 1 curry-only box". The user then rejects the preview. The state check passed. The order check failed because the preview → approval sequence never happened, and the reply rubric failed too. **The step that went wrong was the agent's first and only model call.** It chose `ask_user` with the topic `quantity` instead of calling `preview_preparation`. As a result, the application displayed its fixed question for that topic: "Provide the actual quantity, unit, and raw or cooked state." The user had already given that information. The scripted user had no answer to the question, so the episode ended without a preview. **Why:** the request does not say how to split the 500 g of chicken between the lunch boxes and the curry-only box. The agent was right that something was missing. However, the clarification topics are a fixed list with no allocation question, so the agent fell back to the generic quantity question. In the other two runs, the agent inferred a split instead (375 g chicken and 250 g rice for the lunch boxes, and 125 g chicken for the curry-only box), and the preview appeared. Either of two fixes would address this: add an allocation clarification topic, or have the preview propose a split for the user to approve or reject.
