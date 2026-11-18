# EEP500 Evaluation Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可重現的 50 題 evaluation harness，使用同一套 Nutrition Agent 服務比較 Agent 與 fixed-workflow baseline，並產出課程要求的結果與 failure analysis。

**Architecture:** `nutrition_eval` 直接呼叫現有 `DemoAgent`、共用 `NutritionService` 和一個依固定步驟執行的 baseline。每個 episode 在測試資料庫的隔離 schema 中載入 `tasks.jsonl` fixture，執行 scripted 對話，檢查完整商業終態、操作順序與 rubric judge 結果，再清理 schema。

**Tech Stack:** Python 3.12、PostgreSQL 18、psycopg 3、OpenAI Responses API、`jsonschema`、`pytest`、JSONL。

**Spec:** `docs/superpowers/specs/2026-11-18-evaluation-harness-design.md`

## Global Constraints

- `tasks.jsonl` 必須剛好 50 題，至少 3 題標記 `edge`、至少 2 題標記 `unanswerable`；開發題放在獨立 `development_tasks.jsonl`。
- 六個一般題型配額為：料理／營養 10、烹調／分批 8、加餐／庫存 7、食用 8、更正 10、查詢 5；另有 2 題無法回答。Edge labels 與題型配額重疊。
- Agent 對每題跑 3 次；baseline 對每題跑 1 次。每次都從同一題 fixture 建立全新 schema。
- controller、judge 和 fixture 必須由獨立設定載入；不得將 answer key 或 rubric 傳入 controller context。
- 所有正式 episode 使用相同 America/Los_Angeles 固定 app clock、model identity、推理設定、工具版本和資源上限。
- 初始沿用 `nutrition_demo.agent.Settings` 的 12 model calls、24 tool calls、3 clarifications、4096 output tokens；Agent 與 baseline 使用相同上限，正式評估前凍結。
- 正式 run 的 OpenAI client 固定 `max_retries=0`、timeout 45 秒；controller episode 開始後的 API 失敗依 failure policy 記為該次失敗。
- 評估資料庫只能使用 `TEST_DATABASE_URL`，並驗證 host=`db_test`、dbname=`nutrition_test`；絕不回退到 `DATABASE_URL`。
- synthetic 與 source-backed 數值需標記來源／估算狀態。歷史 PDF 的估算值不可當精確答案。
- 一題通過須同時符合商業終態、required order 及文字 rubric。Judge 呼叫不計入 controller latency 或 tokens。
- episode 開始後的 controller exception、timeout 或資源上限耗盡算該次失敗且不得替換；controller 開始前的 harness／fixture 問題使整批 run 標為 incomplete，修正後用新 run ID 重跑全部題目。
- 同 request ID 寫入重試的可靠性檢查留在 development／service validation，不納入 50 題。

## Review Focus

- answer key 洩漏：controller 只能收到 fixture、request、實際 scripted answers 和核准結果；`expected_changes`、required order 與 rubric 由 grader 持有。Task 3 加入 adapter 測試。
- 無關資料遭改動：預期終態須保留所有未指定的 profile、庫存、烹調 run、批次、加餐與事件。Task 2 加入額外寫入必須判失敗的測試。
- 澄清順序錯誤：runner 只有在 controller 呼叫結構化 `ask_user` 後才送下一個 scripted answer；grader 另外核對問題是否切中該題歧義。Tasks 4–5 加入測試。
- 核准 ID 錯綁：只在 preview 顯示後，按 task script 對目前 preview ID 執行核准／拒絕。Tasks 4–5 加入核准先後與錯 ID 測試。
- 時間／執行互相污染：每次 run 使用新 schema、相同 fixture 和固定 clock；Task 4 驗證三次 run 的初始資料相同，且 latency 使用實際計時器。

## 檔案結構

- Create `nutrition_eval/__init__.py`、`contracts.py`、`tasks.py`：task／run 資料型別、JSONL 解析、題庫結構驗證。
- Create `nutrition_eval/fixtures.py`、`state.py`：測試 schema 生命週期、完整 fixture 載入、商業狀態 snapshot 和標準化。
- Create `nutrition_eval/controllers.py`、`baseline.py`：Agent adapter、controller protocol 與 fixed-workflow baseline。
- Create `nutrition_eval/episode.py`、`runner.py`：scripted user／approval 互動、單一 episode 與整批 orchestration、trace 和 metrics 蒐集。
- Create `nutrition_eval/grading.py`、`judge.py`：終態及操作順序的程式化判分、固定回覆 judge。
- Create `nutrition_eval/report.py`、`nutrition_eval/__main__.py`：CLI、指標彙整、結果及失敗 trace 輸出。
- Create root `development_tasks.jsonl`、`tasks.jsonl`、`eval_config.json`：開發案例、正式 50 題及凍結執行設定。
- Create `tests/test_eval_tasks.py`、`test_eval_fixtures.py`、`test_eval_controllers.py`、`test_eval_episode.py`、`test_eval_grading.py`、`test_eval_taskset.py`、`test_eval_report.py`：隔離、互動、判分及報表驗收。
- Modify `README.md`：安全啟動測試資料庫、開發題 dry run、正式評估命令、輸出目錄及限制。

所有需要資料庫的測試在 Docker Compose `db_test` 上執行，沿用 `tests/conftest.py` 的 TEST_DATABASE_URL guard、每測試獨立 schema 及 teardown 模式。單元測試使用 fake client／controller，不需 API key。

## Task 1: Task Schema and JSONL Loader

**Files:** `nutrition_eval/contracts.py`, `nutrition_eval/tasks.py`, `nutrition_eval/__init__.py`, `tests/test_eval_tasks.py`。

**Interfaces:**

- `ExpectedChange(op: Literal['insert', 'update', 'delete'], entity: str, match: dict, values: dict)` represents a semantic business-state change. New events omit generated IDs; an insert `match` must uniquely identify the expected record by semantic fields.
- `EvalTask(id: str, category: str, labels: set[str], fixture: dict, request: str, scripted_answers: list[str], approval: Literal['approve', 'reject'] | None, expected_changes: list[ExpectedChange], required_order: list[dict], reply_rubric: list[str])`。
- `load_tasks(path: Path, *, expected_count: int | None = None) -> list[EvalTask]` parses UTF-8 JSONL, rejects duplicate IDs, invalid required fields, malformed JSON, unsupported labels and non-finite numeric values.
- `validate_taskset(tasks: list[EvalTask], *, expected_count: int = 50) -> None` checks exact task count and minimum edge/unanswerable quotas.
- `EvalConfig(now: datetime, model_id: str, reasoning_effort: str | None, max_model_calls: int, max_tool_calls: int, max_clarifications: int, max_output_tokens: int, timeout_seconds: int, judge_model_id: str, judge_parameters: dict, task_version: str)`; API credentials come from environment and never from JSON config.
- `EpisodeResult(task_id: str, controller: str, repeat: int, status: str, reply: str | None, trace: list[dict], interactions: list[dict], final_state: dict, turns: int, model_calls: int, tool_calls: int, input_tokens: int, output_tokens: int, latency_ms: int, error: str | None)`.
- `GradePart(passed: bool, reasons: list[str])`, `EpisodeGrade(passed: bool, state: GradePart, order: GradePart, reply: GradePart)`, and `ScoredEpisode(task: EvalTask, episode: EpisodeResult, grade: EpisodeGrade)`.
- `SuiteResult(status: str, episodes: list[EpisodeResult], error: str | None)`; `status` is `complete` or `incomplete`.

- [ ] Write `test_load_tasks_rejects_invalid_json_duplicate_ids_and_missing_fields`; assert each input raises a task/line-specific `ValueError`.
- [ ] Write `test_formal_taskset_requires_50_three_edges_two_unanswerables`; assert 49 rows, duplicate IDs, only two edge labels, or one unanswerable label each fail.
- [ ] Run `docker compose --profile test run --rm --no-deps --entrypoint uv app run --locked python -m pytest tests/test_eval_tasks.py -q`; confirm the new tests fail because the module is absent.
- [ ] Implement dataclasses, strict JSONL parsing, validation and controller input projection using existing `jsonschema` dependency.
- [ ] Rerun the targeted command and confirm all schema tests pass without an OpenAI key.
- [ ] Commit `feat: define evaluation task contract`.

## Task 2: Isolated Fixture Loading and State Snapshot

**Files:** `nutrition_eval/fixtures.py`, `nutrition_eval/state.py`, `tests/test_eval_fixtures.py`.

**Interfaces:**

- `episode_store(dsn: str, schema_prefix: str) -> ContextManager[Store]` validates TEST_DATABASE_URL points to `db_test/nutrition_test`, creates a random schema, applies current `Store.migrate()`, yields the Store, then drops the schema in `finally`.
- `seed_fixture(store: Store, fixture: dict) -> None` inserts profile, inventory, cooking runs/ingredients, batches/allocations, addon plans, events, movements and workflow session data in one transaction; reject nonempty schema and invalid references.
- `read_business_state(store: Store) -> dict` returns the complete semantic business state, including all inventory movements; excludes only generated IDs/timestamps and agent-run telemetry from comparisons.
- `normalize_state(state: dict) -> dict` sorts collections and normalizes generated IDs for comparison while preserving quantities, dates, nutrient snapshots and operation multiplicity.

- [ ] Write `test_fixture_round_trips_all_business_tables`; seed a synthetic profile, inventory item, two batches, addon plan, event and workflow state, then assert the normalized snapshot matches.
- [ ] Write `test_extra_event_or_movement_changes_snapshot`; assert one additional meal event or inventory movement produces a state difference.
- [ ] Write `test_episode_schema_is_removed_after_success_and_exception`; assert the schema is absent after both context exits.
- [ ] Write `test_fixture_loader_rejects_personal_database_and_nonempty_schema`; assert production host/db and an already seeded schema are refused before task execution.
- [ ] Ensure `docker compose --profile test up -d --wait db_test` has completed before running the database-backed fixture tests.
- [ ] Run `docker compose --profile test run --rm --no-deps --entrypoint uv app run --locked python -m pytest tests/test_eval_fixtures.py -q`; confirm failures before implementation.
- [ ] Implement the schema context manager and transactionally seed/read/normalize fixture state using `Store.transaction()` and parameterized SQL.
- [ ] Rerun `tests/test_eval_fixtures.py -q`; confirm state preservation, exception cleanup and DB safety guard pass.
- [ ] Commit `feat: isolate evaluation fixture state`.

## Task 3: Controller Interface and Fixed-Workflow Baseline

**Files:** `nutrition_eval/controllers.py`, `nutrition_eval/baseline.py`, `tests/test_eval_controllers.py`.

**Interfaces:**

- `Controller.handle(message: str) -> Result` and `Controller.approve(preview_id: str, outcome: str) -> Result`, where outcome is `approve` or `reject`.
- `AgentController(agent: DemoAgent, workflow: Workflow)` delegates message handling to `DemoAgent.handle()` and binds approvals to the current workflow preview via `/confirm <id>` or `/reject <id>`.
- `FixedWorkflowBaseline(service: NutritionService, workflow: Workflow, client, settings)` uses one constrained structured-action extraction per user message; the structured result contains an action, arguments and user-facing reply, while Python applies a fixed routing table and calls the same service operations. Clarification is a structured action and subsequent answers re-enter the same fixed route. It does not expose a model-selected tool loop or select a new operation after observing tool results. It uses the same model identity/settings, context, resource limits, fixtures and approvals as Agent.

`agent_factory(store, task, config) -> Controller` and `baseline_factory(store, task, config) -> Controller` construct each controller against the current episode's service and workflow.

- [ ] Write `test_agent_adapter_passes_message_and_preview_id_to_application_confirmation`; use a fake DemoAgent/workflow and assert the exact current preview ID is used.
- [ ] Write `test_agent_adapter_never_passes_task_answer_key`; assert the adapter sends only the current user message to `DemoAgent.handle()` and never serializes `EvalTask.expected_changes`, `required_order` or `reply_rubric`.
- [ ] Write `test_fixed_baseline_uses_closed_action_schema_and_one_route_per_response`; fake the model response and assert the baseline follows the fixed Python route without a second model-driven operation choice.
- [ ] Write `test_baseline_uses_same_service_for_inventory_meal_and_correction`; inject a spy service and assert only the shared public service methods perform writes.
- [ ] Run `docker compose --profile test run --rm --no-deps --entrypoint uv app run --locked python -m pytest tests/test_eval_controllers.py -q`; confirm failure before implementation.
- [ ] Implement the protocol/adapters and closed action schema; use task/fixture input only, never expected changes or rubrics.
- [ ] Rerun controller tests and the existing `tests/test_demo_agent.py -q` to verify the adapter does not change V1 behavior.
- [ ] Commit `feat: add fixed workflow evaluation baseline`.

## Task 4: Scripted Episode Runner and Metrics Capture

**Files:** `nutrition_eval/episode.py`, `nutrition_eval/runner.py`, `tests/test_eval_episode.py`.

**Interfaces:**

- `run_episode(task: EvalTask, controller: Controller, store: Store, *, repeat: int, now: datetime, limits: dict) -> EpisodeResult` runs a full conversation and returns trace, state, response and metrics.
- `run_suite(tasks: list[EvalTask], agent_factory, baseline_factory, config: EvalConfig) -> SuiteResult` runs Agent 3 times and baseline once for each task, always using a new schema and the same task fixture. Infrastructure errors before controller start return `incomplete` and stop the suite.
- One assistant reply counts as one turn. Model calls are counted separately. Tokens sum all controller call input/output usage. Latency spans initial request through final reply and includes controller model/service work; it excludes scripted waits and judge calls.
- After an explicit `ask_user` result, runner sends the next scripted answer if available. If the controller skips the question, it receives no answer. A scripted approval/rejection is sent only after the current preview appears and uses that live preview ID.

- [ ] Write `test_episode_replays_answer_only_after_ask_user`; assert no answer is supplied if controller skips the clarification and the next scripted answer is supplied after the structured ask.
- [ ] Write `test_approval_waits_for_preview_and_binds_current_id`; assert approval before preview is impossible and mismatched IDs fail the episode process check.
- [ ] Write `test_each_repeat_reloads_same_fixture_and_clock`; run a fake mutating controller three times and assert each starts from the original inventory/batch counts and same app clock.
- [ ] Write `test_suite_runs_agent_three_times_and_baseline_once`; assert each formal task creates three isolated Agent episodes and one isolated baseline episode.
- [ ] Write `test_turns_model_calls_latency_and_tokens_aggregate_across_messages`; use fake usage/clock values and assert exact totals.
- [ ] Write `test_controller_failure_is_failed_episode_but_setup_error_incompletes_suite`; assert controller exception/budget exhaustion returns a failed EpisodeResult, while fixture failure stops the suite as incomplete.
- [ ] Run `docker compose --profile test run --rm --no-deps --entrypoint uv app run --locked python -m pytest tests/test_eval_episode.py -q`; confirm expected failures before implementation.
- [ ] Implement the episode loop, trace aggregation, monotonic latency, timeout/resource policy and suite orchestration; preserve partial controller trace on failure.
- [ ] Rerun `tests/test_eval_episode.py -q` and existing `tests/test_demo_scenario.py -q`.
- [ ] Commit `feat: run isolated scripted evaluation episodes`.

## Task 5: Independent Grader and Rubric Judge

**Files:** `nutrition_eval/grading.py`, `nutrition_eval/judge.py`, `tests/test_eval_grading.py`.

**Interfaces:**

- `grade_state(task: EvalTask, actual: dict) -> GradePart` applies expected changes to fixture state and compares all normalized business fields.
- `grade_order(task: EvalTask, episode: EpisodeResult) -> GradePart` evaluates required order for clarification, preview, approval and writes from the recorded trace/interactions.
- `grade_reply(task: EvalTask, episode: EpisodeResult, *, judge_client, judge_config) -> GradePart` submits the response, scripted conversation, fixture and actual final state plus rubric to one frozen judge, requiring structured criterion-level JSON.
- `grade_episode(task, episode, judge_client, judge_config) -> EpisodeGrade` passes only when state, order and reply all pass. Judge usage is recorded separately and excluded from controller metrics.
- `grade_suite(tasks: list[EvalTask], suite: SuiteResult, *, judge_client, judge_config) -> list[ScoredEpisode]` grades every episode from a complete suite. A judge outage makes the overall run incomplete; partial grades must not be reported as final accuracy.

- [ ] Write `test_state_grader_rejects_wrong_values_and_unrelated_writes`; assert incorrect stock, extra event/movement and changed unrelated batch each fail.
- [ ] Write `test_order_grader_rejects_write_before_clarification_or_approval`; assert the valid ask → answer → preview → approval → write order passes.
- [ ] Write `test_unanswerable_reply_requires_no_invention_and_no_state_change`; assert any invented nutrition claim or new event fails.
- [ ] Write `test_reply_judge_parses_each_rubric_criterion_and_excludes_usage`; fake judge JSON and verify each criterion contributes to pass and judge tokens remain separate.
- [ ] Write `test_judge_outage_marks_suite_incomplete_without_final_metrics`; assert partial judge results are not reported as a complete evaluation.
- [ ] Run `docker compose --profile test run --rm --no-deps --entrypoint uv app run --locked python -m pytest tests/test_eval_grading.py -q`; confirm failures before implementation.
- [ ] Implement deterministic state/trace grading and the versioned judge adapter; select judge model and exact parameters at implementation time, then freeze them before formal evaluation.
- [ ] Rerun `tests/test_eval_grading.py -q`; validate the grader against correct and deliberately incorrect fixtures.
- [ ] Commit `feat: grade evaluation state process and responses`.

## Task 6: Development Cases and Formal 50-Task Dataset

**Files:** `development_tasks.jsonl`, `tasks.jsonl`, `eval_config.json`, `tests/test_eval_taskset.py`.

**Interfaces:** `load_tasks()` and `validate_taskset()` from Task 1; fixture seeding and grader behavior from Tasks 2 and 5.

- [ ] Write `test_development_cases_are_separate_and_formal_dataset_exactly_50`; assert development records are not counted and final file has 50 unique IDs.
- [ ] Write `test_formal_taskset_matches_approved_category_counts`; assert counts are 10/8/7/8/10/5/2 for nutrition, preparation, addons, meal logging, corrections, queries and unanswerable.
- [ ] Author 3–5 development cases: one ordinary successful write, one clarification/approval sequence, one unanswerable response and at least one nutrition or allocation edge; include correct and intentionally incorrect grading samples.
- [ ] Run the dev cases against fake controllers and judge to verify state, order, answer, and report failures are detected as intended; adjust rubric/schema before formal authoring.
- [ ] Author exactly 50 formal cases using the approved category quotas; tag at least five approved edge scenarios and two unanswerables. Keep all fixture values and provenance explicit.
- [ ] Write `eval_config.json` with one frozen Los Angeles clock, model ID/effort, call/time/token limits, judge version, tool version and dataset version; exclude credentials.
- [ ] Run `docker compose --profile test run --rm --no-deps --entrypoint uv app run --locked python -m pytest tests/test_eval_taskset.py -q`; assert 50 tasks, 3+ edges, 2+ unanswerables, valid provenance and answer-key projection.
- [ ] Commit `test: add development and 50 task evaluation sets`.

## Task 7: CLI, Summary Report and Run Documentation

**Files:** `nutrition_eval/report.py`, `nutrition_eval/__main__.py`, `tests/test_eval_report.py`, `README.md`.

**Interfaces:**

- `summarize_runs(results: list[ScoredEpisode]) -> dict` computes accuracy, turns, model calls, mean/p95 latency, mean input+output tokens, pass@3, pass^3 and flipped task IDs. Compute p95 with nearest-rank over episode samples.
- `write_run_artifacts(output_dir: Path, suite: SuiteResult, results: list[ScoredEpisode], summary: dict | None) -> None` writes raw `episodes.jsonl`, run status/metadata, a side-by-side `summary.md` for complete runs and a failure-trace file under `results/<run_id>/`. Incomplete runs preserve partial episodes and their reason without presenting partial metrics as final. After a complete formal run, write `failure_analysis.md` from one actual failed episode; if there were none, state that no controller failure was observed.
- CLI `python -m nutrition_eval --tasks tasks.jsonl --config eval_config.json --output results/<run_id>` validates the taskset before any controller starts and refuses the personal `DATABASE_URL`.

- [ ] Write `test_report_computes_pass_at_3_pass_power_3_flips_and_percentile`; use fixed synthetic run data to assert exact accuracy, metrics, and nearest-rank p95.
- [ ] Write `test_report_saves_episode_samples_and_metadata`; assert raw rows retain controller, task, repeat, model/tool/fixture versions and failures.
- [ ] Write `test_cli_aborts_before_execution_on_invalid_taskset_or_unsafe_database`; assert no controller call occurs.
- [ ] Run `docker compose --profile test run --rm --no-deps --entrypoint uv app run --locked python -m pytest tests/test_eval_report.py -q`; confirm they fail before implementation.
- [ ] Implement the CLI orchestration: run controllers, grade every episode, mark judge interruption incomplete, aggregate only complete scored runs, and preserve raw partial episodes plus status metadata; document that Agent has 150 episode samples and baseline 50.
- [ ] Update README with test DB startup, no-key dry run, formal-run command, output files, frozen settings and the separate 200-task/safety-suite scope.
- [ ] Run `docker compose --profile test up -d --wait db_test` and `docker compose --profile test run --rm --no-deps --entrypoint uv app run --locked python -m pytest tests/test_eval_tasks.py tests/test_eval_fixtures.py tests/test_eval_controllers.py tests/test_eval_episode.py tests/test_eval_grading.py tests/test_eval_taskset.py tests/test_eval_report.py -q`; confirm all evaluation tests pass.
- [ ] Run the complete existing suite with `docker compose --profile test run --rm --no-deps --entrypoint uv app run --locked python -m pytest tests/ -q`; confirm V1 tests remain green.
- [ ] Run the fake-client development dry run and inspect generated JSONL/Markdown output; do not label it as a live-model comparison.
- [ ] Commit `feat: report agent baseline evaluation results`.

## Formal Run Handoff

After implementation and review, freeze exact model/SDK/settings, task and fixture versions, tool contract and judge. Run the 50-task comparison using the test database and generate the requested results. Select one observed failed episode and write the one-paragraph failure analysis from its preserved trace. If no live controller failure occurs, report that fact rather than inventing one. The 11/17 take-home deadline has passed; confirm later course expectations before describing a late submission as accepted.
