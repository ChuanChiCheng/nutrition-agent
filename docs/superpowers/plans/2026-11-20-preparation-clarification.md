# Specific preparation clarification implementation plan

**Goal:** Ask one justified preparation question while retaining supplied actual usage, date and output details.

**Spec:** The preparation clarification proposal approved in this chat: collect structured supplied facts, derive missing fields/conflicts in Python, preview sufficiently specified requests, and preserve external approval, fixtures and historical results.

**Architecture:** A preparation draft is scoped to an accepted recipe and an explicit English preparation-preview request at cooking stage. The existing ReAct loop extracts partial details with `update_preparation_draft`; Python derives questions for `ask_user`. Existing preview/confirmation service operations remain authoritative. A model extraction is not proof of language understanding; all actual usage and allocations remain visible for external review.

## Constraints and decisions

- Use the current `fix-evaluation` checkout; no new worktree, paid model calls, evaluation, fixture/task/config edits or historical-result changes.
- Retain existing global tools/baseline and unrelated question paths. Expose draft tooling only in the preparation scope.
- Bind the draft to the accepted recipe/proposal. Preserve fields across direct clarification replies; abandon the pending question on unrelated requests and clear drafts on a new plan/recipe.
- Derive questions from partial actual ingredient fields, omitted accepted ingredients, date, output boxes, allocations and exact conservation. Do not fill actual fields from planned quantities or infer multi-batch allocations from box counts.
- An accepted ingredient missing from actual usage is unresolved until the external user answers its omission question. A model cannot certify omissions through tool arguments.
- Unit/state mismatches require verified matching input; no raw/cooked conversion assumptions. Existing service stock/nutrition validation remains in force.
- Changed actual quantities/box counts are allowed and recalculated; they do not automatically require accepting the planned quantities again.
- A generic quantity/details/date question is rejected until supplied facts have been captured. A complete draft rejects unnecessary clarification. Existing resource limits bound retries; unfinished preparation is reported incomplete.
- New previews require complete draft values matching the arguments; external `/confirm` or `/reject` is unchanged.

## Tasks

- [x] Add failing draft regressions and implement partial merge, derived issues, external omission answers and recipe binding.
- [x] Add failing real-service/fake-model tests and integrate scoped draft tools, specific questions, preview validation, continuation and reset behavior.
- [x] Cover confirm/reject, no writes before approval, conservation/unit/state errors, unrelated operations and unchanged prior contracts; run full offline suite and review.

## Verification

- `tests/test_preparation_clarification.py`: 34 passed.
- Full offline suite: 306 passed.
- `git diff --check`: passed.
- Protected evaluation records, fixtures, configuration, and unrelated service/tool files have no diff.
- No paid model calls or evaluation runs were made.

## Review focus

Stale draft reuse; repeated known fields; omitted accepted ingredients; complete single-output vs unspecified split allocation; model-certified omissions; preview arguments diverging from checked draft; approval bypass; unrelated follow-ups.
