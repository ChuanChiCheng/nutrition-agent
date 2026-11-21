# Addon receipts and deterministic grading

## Intent

Make addon approval and rejection replies self-contained, and make the fixed addon response criterion score consistently. Reports must separate operation-state/order outcomes from response outcomes so response-only failures are not described as failed writes.

## Goals and constraints

- Render batch, addon name, exact quantity and unit, and planned-default versus actual-consumption status after approval; identify the rejected proposal and say the prior plan remains unchanged after rejection.
- Derive receipt facts from the stored preview payload. Keep user approval as the only commit path; rejection must remain non-mutating.
- Replace model judging only for the fixed addon rubric with deterministic checks against the terminal reply and observed successful preview action. Keep other rubric judging unchanged.
- Report state, order, response, and overall pass counts by controller and category.
- Keep `results/formal-50-english-2026-11-20-v2/`, task fixtures, and frozen evaluation configuration unchanged. Do not make paid model calls or run a live evaluation.

## Approaches

1. Change only judge instructions. This leaves repeat-to-repeat model variability and the generic user-facing receipt.
2. Add a self-contained app-owned receipt and deterministic addon rubric check. This makes user-visible evidence complete and scores the objective criterion without a judge call. **Chosen.**
3. Exclude the reply component from addon success. This would conceal a real response-quality gap and weaken the existing all-components pass rule.

## Design

The service will attach an `addon_receipt` made from the immutable preview payload to successful addon confirmation and rejection results. The display layer will use it to produce an explicit receipt. Confirmation reports the saved default and that stock is consumed only when eaten; rejection reports that the previous default remains unchanged. Neither receipt claims intake was recorded.

The addon response grader will inspect the successful `preview_batch_addons` action, fixture names, approval outcome, and rendered terminal reply. It will require every proposed item and exact amount/unit plus the corresponding saved/rejected and default-versus-consumption wording. Missing preview evidence or mismatched wording fails deterministically. It will not call the model judge. Other categories retain the existing judge.

Run metadata will name the deterministic reply-grader version and count only episodes that actually need a model-judge call. Generated summaries will include component counts by controller and category, while overall success continues to require state, order, and response to pass.

## Non-goals

- Regrading, rewriting, or deleting historical v2 results.
- Changing tasks, fixtures, expected business state, approval behavior, or the overall pass definition.
- Changing response grading for non-addon categories or altering the LLM judge prompt/schema.
