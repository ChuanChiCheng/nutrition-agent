# Missing meal data implementation plan

**Goal:** Separate absence of a saved meal from ambiguity, database failure, and zero recorded daily totals.

**Architecture:** `find_events` supplies explicit match status, normalized search criteria and recorded-prepared-meal coverage. A shared renderer presents negative lookups and saved event snapshots. A scoped read-only meal-history question handler binds explicit English date/meal criteria and ends the existing ReAct loop after a verified matching search; unrelated requests and correction routing retain their existing paths.

**Spec:** The missing-data semantics proposal approved in this chat: no_match/unique/multiple/error distinction, unknown meal nutrition separate from empty aggregate totals, and a grounded negative lookup as a valid answer.

## Constraints

- Work on the existing `fix-evaluation` checkout; no worktree, paid calls, evaluation runs or historical-result/task/config edits.
- Do not modify `nutrition_demo/completion.py` or the batch-target comparison contract.
- Retain `candidates` and a compatibility ambiguity flag for existing consumers; only multiple matches are ambiguous. Read-only enumeration does not require selecting one record.
- Preserve correction search/preview/confirmation/rejection and external approval requirements.
- Daily numeric sums stay unchanged. An empty log means zero recorded intake, not knowledge of actual intake.
- Scope terminal history handling to explicit single-date meal/dish lookups. Reject mismatched or over-filtered model searches; errors never become absence. English ISO/month-name/today/yesterday dates are normalized using the application date. No additional model interpretation call is added.

## Tasks

- [x] Add failing service/display regressions for no matches, unique and multiple snapshots, daily empty totals, and database errors; implement shared search semantics and rendering.
- [x] Add failing real-service/fake-model regressions for missing lunch with another meal present, no-match terminal handling, matching query validation, and read-only enforcement; implement scoped history handling.
- [x] Verify correction no-match/ambiguity/approval paths and run the full offline suite, review changes, and leave implementation uncommitted.

## Review focus

Incorrect date/meal scope; search failures; stale or current-state nutrition replacing saved snapshots; unwanted selection prompts; mixed read/write requests; existing approval state; unchanged batch-target behavior.

## Observed verification

- Added 54 offline regression cases. Full Docker/PostgreSQL suite: **272 passed in 22.76 seconds**.
- Both Agent and baseline correction no-match, ambiguity, selection, preview, unauthorized confirmation, external confirmation and rejection are covered with real service operations and fake model I/O.
- Review findings were reproduced before fixes: unsupported date qualifiers/ranges and mixed/planning actions stay outside terminal history handling; meal comparisons ignore case/whitespace without modifying saved snapshots.
- Terminal activation matches a complete supported English history-question form after date canonicalization. Unknown wording, extra qualifiers and mixed actions retain the existing workflow; this is not a general natural-language classifier. An omitted year uses the application date's year.
- Batch-target contract and tests, historical results, tasks, evaluation configuration, evaluator/baseline code, and READMEs have no diff. No paid model calls or evaluation runs were made. Changes remain uncommitted.
