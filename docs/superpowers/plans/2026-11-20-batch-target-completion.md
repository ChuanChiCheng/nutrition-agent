# Batch-target completion implementation plan

**Goal:** Require evidence-backed completion for existing-batch meal-target comparisons while retaining the ReAct loop.

**Spec:** The completion-contract design approved in this chat: fixed requirements, request-bound evidence, explicit finish, bounded corrective observations, clarification and approval pauses, and offline regressions.

**Architecture:** A scoped completion object owns immutable request requirements and ephemeral evidence. The existing model/tool loop selects actions; Python validates assessment and completion. A conservative English request gate activates only explicit single-batch per-box meal-target comparisons, using current batch names/IDs to bind identity. It is request interpretation, not an execution plan, and cannot establish arbitrary natural-language understanding.

## Constraints

- Use the existing `fix-evaluation` checkout; no worktree, paid calls, evaluation runs, dataset/config changes, or historical-result edits.
- Existing tool schemas and baseline remain unchanged; expose additional tools only within the scoped contract.
- All four nutrients use current configured meal targets and the existing exact Decimal validator; retain saved batch nutrient snapshots.
- No model-supplied nutrient values, completion flags, cross-request evidence, or guessed ambiguous batch selections.
- Two corrective observations maximum, still subject to existing model/tool caps. Exhaustion is incomplete, never answered.
- Clarification is an explicit awaiting-user outcome, with the original comparison retained for batch selection. Existing approval behavior stays unchanged.

## Review focus

Wrong/stale evidence; missing nutrient fields; depleted batches; profile targets missing; unrelated follow-up after clarification; mixed write requests; no-tool exits; resource exhaustion; decimal boundaries.

## Tasks

- [x] Add failing tests for request scope, assessment computation, request-bound completion, invalid/incomplete evidence, ambiguous selection, and boundary values. Implement `nutrition_demo/completion.py` plus `NutritionService.assess_batch_targets(batch_id)`.
- [x] Add failing fake-model/real-service tests for premature stop, lookup-only completion, wrong batch, valid finish, bounded recovery, clarification continuation, and write rejection. Integrate scoped tools and completion state with `DemoAgent.handle`.
- [x] Add failing rendered-answer checks for all actuals/targets/ranges/differences and synthetic provenance. Implement the trusted answer display; run focused and full offline suites and review the diff.

## Verification

Run focused tests red before each implementation slice. Run the repository's Docker/PostgreSQL pytest suite after integration. Check whitespace and changed paths. Leave implementation uncommitted for review.

**Observed verification:** 41 new scoped regressions passed; full offline suite passed 218 tests in 20.83 seconds. No paid model calls or evaluation runs were made. Protected dataset/config/result/evaluator/baseline paths have no diff.

**Review resolutions:** Added red-to-green regressions for fractional/multiple-box scope, contradictory name/ID references, overlapping names, an explicit ID disambiguating duplicate names, and clearing pending comparison state on `/new-plan`. The contract uses conservative English request recognition, not an extra model classifier; unsupported wording remains outside its completion guarantee. Runtime runs record `batch-target-completion-v1` separately from the unchanged legacy tool registry.
