# English evaluation verification

Date: 2026-11-20

- All 50 formal tasks and four development tasks translated, including fixture values, provenance, scripted answers, and response rubrics.
- Evaluation uses English controller instructions, application clarification questions, preview summaries, workflow messages, and deterministic replies.
- Shared meal permission checks match English batch names case-insensitively. Hypothetical consumption remains blocked.
- Formal taskset SHA-256 refreshed; configuration records `evaluation_language=en` and `language_revision=english-v1`.
- Full suite: 158 passed in 12.50 seconds, including both evaluation factories and real PostgreSQL service operations.
- Fake-client dry run: 16 passing episodes from four development tasks. Generated JSONL and Markdown contain no Mandarin text. Output inspected at `/tmp/nutrition-eval-english-verification/dev-english-v1`.
- Formal paid model comparison remains unexecuted; no live accuracy is claimed.

Historical planning documents retain their original language. The current evaluation report and README evaluation instructions are English.

## Shared agent English default

The English evaluation subclasses have been removed. Both controller factories now use the shared DemoAgent, Workflow, NutritionService, and Catalog. The shared prompt, application-owned questions, workflow messages, preview summaries, recipe calculation instructions, help text, recovery messages, terminal labels, and CLI errors default to English.

Original recipe evidence and existing/user-supplied data retain their original language. Bilingual intent/date recognition is retained as input support, not generated response text. Historical planning documents are unchanged.

Regression checks cover help, explicit and implicit meal recovery after an API error, unknown commands, missing previews, mismatched confirmations, all clarification topics, resource-limit messages, target pass/fail displays, malformed tool calls, rejection rendering, and sanitized CLI failures. Existing service, display, and cooking-evidence tests continue to run.

Latest full suite: 165 passed in 12.73 seconds. No live model calls were made.
