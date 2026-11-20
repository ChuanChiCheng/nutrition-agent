# Baseline and fixture corrections before the next evaluation

The original formal results remain preserved. No paid model calls were made for these corrections.

## Changes

- Both controllers call the shared application bookkeeping before interpreting a natural-language message. A declared consumption event and candidate batch IDs survive a clarification answer; existing meal permission checks still decide whether a write is allowed.
- Baseline has an explicit correct_meal extraction action containing an original-record query and requested changes. Python performs a fixed search-to-preview route for a unique candidate, asks for an event selection for multiple candidates, or reports no match. It performs no additional model decision after reading the search result. Pending changes and allowed candidate IDs survive selection. Search, clarification, and preview operations are individually traced and counted against the tool budget. Confirmation remains external.
- Baseline exposes operation results through the shared tool_results presentation contract, so actual preview changes reach both the UI and the evaluator.
- All formal and development fixtures explicitly start with confirmed inventory. Existing preparation fixtures remain at the cooking stage with a confirmed recipe; other fixtures start ready. These tasks exercise operations on an already-configured synthetic account, not onboarding. Real application onboarding remains unchanged.

Dataset/task revision: nutrition-eval-50-v2. Baseline revision: fixed-workflow-v2. The task hash was refreshed. Model settings, resource caps, judge parameters, category counts, requests, rubrics, and expected business changes were not changed by this patch. Raw config and baseline revision are saved in future run metadata.

## Verification

Regression tests initially reproduced all four issues. Real PostgreSQL tests run M08 plus all ten formal correction cases with fake model extractions, checking business state, process order, full preview display, approval binding, and model/tool counts. Additional tests cover ambiguous selection, no matches, pending correction changes, and tool limits.

These tests verify deterministic execution for valid model extractions; they do not guarantee that a live model will select the correct action or arguments.

Full suite: 175 passed in 16.20 seconds.
