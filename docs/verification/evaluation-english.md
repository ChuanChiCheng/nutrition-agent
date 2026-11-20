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
