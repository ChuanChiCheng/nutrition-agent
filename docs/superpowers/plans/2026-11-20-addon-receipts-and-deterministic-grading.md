# Addon Receipts and Deterministic Grading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make addon receipts specific, grade the fixed addon response rubric deterministically, and report component outcomes separately.

**Architecture:** Addon confirm/reject service results carry preview-derived receipt facts. The existing terminal renderer formats those facts. The evaluation grader uses a deterministic addon-specific checker and retains the LLM judge for other categories; generated summaries expose component counts by controller and category.

**Tech Stack:** Python, PostgreSQL test service, pytest, JSONL evaluation tasks.

**Spec:** `docs/superpowers/specs/2026-11-20-addon-receipts-and-deterministic-grading-design.md`

## Global Constraints

- Do not alter historical v2 results, task fixtures, `tasks.jsonl`, or `eval_config.json`.
- Preserve external `/confirm` and `/reject` behavior and the all-components pass definition.
- Do not make paid model calls or run a formal/live evaluation.

## Review Focus

- Confirm and reject receipts use the actual stored preview and do not imply intake or stock consumption.
- Missing/failed preview actions fail deterministic addon response grading.
- Decimal quantities and multiple addon items retain exact values and units.
- Non-addon tasks still use the configured model judge.
- Component counts overlap correctly and category denominators include every scored episode.

---

### Task 1: Self-contained addon receipts

**Files:**
- Modify: `nutrition_demo/service.py`
- Modify: `nutrition_demo/display.py`
- Test: `tests/test_demo_display.py`
- Test: `tests/test_demo_preparation.py`

**Interface:** Service confirm/reject results for addon previews expose an `addon_receipt` containing outcome, batch ID/name, and preview items.

- [x] Add failing renderer tests for confirmed and rejected receipts, including exact item, quantity, unit, batch, and no-intake/default wording.
- [x] Add failing service tests proving preview facts are returned and rejection leaves addon plan, inventory, and meal events unchanged.
- [x] Run the targeted tests and confirm they fail on missing receipt data.
- [x] Implement preview-derived receipt data and terminal rendering without changing approval authority.
- [x] Run the targeted tests and confirm they pass.

### Task 2: Deterministic addon response grading

**Files:**
- Modify: `nutrition_eval/judge.py`
- Modify: `nutrition_eval/__main__.py`
- Test: `tests/test_eval_grading.py`
- Test: `tests/test_eval_report.py`

**Interface:** `grade_reply` returns a deterministic result for `category == "addons"`; other categories keep using `grade_reply`'s existing model-judge request. Run metadata includes `reply_grader_version` and accurate planned model-judge calls.

- [x] Add failing approval/rejection grading tests with exact rendered receipt details and a judge client that must not be called for addon tasks.
- [x] Add a failing repeatability test: equivalent addon episodes receive the same component grade.
- [x] Reuse the existing passing control test proving non-addon tasks still invoke the model judge.
- [x] Run the targeted tests and confirm expected failures.
- [x] Implement the deterministic addon checker and grader metadata/call-count changes.
- [x] Run the targeted tests and confirm they pass.

### Task 3: Component reporting

**Files:**
- Modify: `nutrition_eval/report.py`
- Test: `tests/test_eval_report.py`

- [x] Add failing summary tests for per-controller and per-category state/order/response counts, including 21 addon attempts with state/order 21/21 and response 11/21.
- [x] Run the targeted tests and confirm the component summary is absent.
- [x] Add component counts to summary data and Markdown while retaining existing overall accuracy.
- [x] Run report tests and confirm the old aggregate metrics remain unchanged.
- [x] Run the full offline test suite; verify protected result/config/task files remain untouched and no live evaluation ran.

## Verification

- Receipt tests: 24 passed; the initial red run had 4 expected failures.
- Evaluation grader/report tests: 22 passed; initial grader red run had 5 expected failures, and the component-report test failed before implementation as expected.
- Full offline suite: 315 passed.
- `git diff --check`: passed.
- Historical result files, task fixtures, `tasks.jsonl`, and `eval_config.json` have no diff.
- No paid judge calls or live evaluation runs were made.
