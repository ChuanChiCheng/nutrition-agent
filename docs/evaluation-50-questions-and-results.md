# Evaluation: 50 questions and result status

The evaluation is now entirely in English. Formal model evaluation has not run; no formal accuracy, latency, token, pass@3, or pass^3 results are available.

The previous revision passed 156 automated tests and 52 evaluation tests. Those numbers describe software checks, not model accuracy. Its four-case fake-client demonstration generated 16 episodes (12 Agent and four baseline). A synthetic 100% result does not measure model capability. The English revision passed 158 tests on November 20, 2026. Its four-case fake-client dry run produced 16 passing synthetic episodes; all generated artifacts were checked for Mandarin text and contained none. This remains a fake-client result, not live accuracy.

## How scoring works

Each task runs three times for Agent and once for baseline, with fresh isolated state. A pass requires correct business state, required interaction order, and every response rubric criterion. Judge usage is excluded from controller costs. The fixed clock is November 18, 2026, so “today” refers to that date.

Pass@3 is the fraction of tasks with at least one passing Agent repeat; pass^3 requires all three repeats to pass. Formal results remain pending paid-run authorization.

## All 50 questions

| ID | Category | Question | Scripted follow-up | Response rubric |
|---|---|---|---|---|
| N01 | nutrition | Does the synthetic curry lunch batch meet the meal targets? List all four actual values and targets. | None | List the four synthetic nutrient values, targets, and correct overall target status. |
| N02 | nutrition | How much protein and carbohydrate does the synthetic curry lunch batch contain? Also explain its overall target status. | None | Correctly report protein and carbohydrate and determine overall status from all four nutrients. |
| N03 | nutrition | List the allowed upper and lower bounds for all four nutrients in the synthetic curry lunch batch and compare each. | None | Calculate the four upper and lower bounds and compare each without rounding. |
| N04 | nutrition | Are all four nutrients in the synthetic curry lunch batch within their allowed ranges? Give each difference. | None | List all four differences and allowed ranges; do not judge using rounded display values. |
| N05 | nutrition | Compare the four per-box nutrients in both synthetic curry batches and identify any failing nutrients in each. | None | Correctly compare all four nutrients across both batches without confusing them. |
| N06 | nutrition | Do calories and protein in the synthetic curry dinner batch meet the meal targets? Explain your reasoning. | None | Judge calories and protein using the synthetic dinner batch fixture values. |
| N07 | nutrition | Compare meal and daily targets for the synthetic curry lunch batch; keep them separate. | None | Distinguish meal and daily targets and correctly report this batch's per-box results. |
| N08 | nutrition | Considering only fat and carbohydrates in the synthetic curry lunch batch, does each meet its target? | None | Correctly report fat and carbohydrate values and their pass status. |
| N09 | nutrition | If the synthetic curry lunch batch is exactly at all four lower bounds, does it pass? List the values. | None | List the four lower bounds and explain that equality satisfies the limits. |
| N10 | nutrition | The synthetic curry lunch batch has 569.9 kcal, below the 570 kcal lower bound. Does it pass overall? | None | Explain that calories are below the lower bound, so the overall result fails even if the other three nutrients pass. |
| P01 | preparation | Preview preparing 5 boxes using 300 g raw chicken breast and 150 g dry rice on November 18; do not save without approval. | reject after preview | Explain total ingredient usage and each batch allocation; do not claim saving after rejection. |
| P02 | preparation | Preview preparing 6 boxes using 400 g raw chicken breast and 200 g dry rice on November 18; do not save without approval. | reject after preview | Explain total ingredient usage and each batch allocation; do not claim saving after rejection. |
| P03 | preparation | Preview preparing 4 boxes using 500 g raw chicken breast and 250 g dry rice on November 18; do not save without approval. | reject after preview | Explain total ingredient usage and each batch allocation; do not claim saving after rejection. |
| P04 | preparation | Preview preparing 5 boxes using 600 g raw chicken breast and 300 g dry rice on November 18; do not save without approval. | reject after preview | Explain total ingredient usage and each batch allocation; do not claim saving after rejection. |
| P05 | preparation | Preview preparing 6 boxes using 700 g raw chicken breast and 350 g dry rice on November 18; do not save without approval. | reject after preview | Explain total ingredient usage and each batch allocation; do not claim saving after rejection. |
| P06 | preparation | Preview preparing 4 boxes using 800 g raw chicken breast and 400 g dry rice on November 18; do not save without approval. | reject after preview | Explain total ingredient usage and each batch allocation; do not claim saving after rejection. |
| P07 | preparation | Preview preparing 5 boxes using 450 g raw chicken breast and 225 g dry rice on November 18; do not save without approval. | reject after preview | Explain total ingredient usage and each batch allocation; do not claim saving after rejection. |
| P08 | preparation | Preview cooking 500 g raw chicken breast and 250 g dry rice, allocated exactly to 3 lunch boxes and 1 curry-only box. | reject after preview | Explain total ingredient usage and each batch allocation; do not claim saving after rejection. |
| A01 | addons | Set the synthetic curry lunch batch's default addon to 1 serving of synthetic yogurt. | approve after preview | Explain exact addon quantities and distinguish planned default addons from actual consumption. |
| A02 | addons | Set the synthetic curry lunch batch's default addon to 2 servings of synthetic yogurt. | approve after preview | Explain exact addon quantities and distinguish planned default addons from actual consumption. |
| A03 | addons | Set the synthetic curry lunch batch's default addon to 0.5 servings of synthetic yogurt. | approve after preview | Explain exact addon quantities and distinguish planned default addons from actual consumption. |
| A04 | addons | Set the synthetic curry lunch batch's default addon to 1.5 servings of synthetic yogurt. | approve after preview | Explain exact addon quantities and distinguish planned default addons from actual consumption. |
| A05 | addons | Set the synthetic curry lunch batch's default addon to 3 servings of synthetic yogurt. | approve after preview | Explain exact addon quantities and distinguish planned default addons from actual consumption. |
| A06 | addons | Set the synthetic curry lunch batch's default addon to 30 g of synthetic oats. | reject after preview | Explain exact addon quantities and distinguish planned default addons from actual consumption. |
| A07 | addons | Set the synthetic curry lunch batch's default addon to 50 g of synthetic oats. | reject after preview | Explain exact addon quantities and distinguish planned default addons from actual consumption. |
| M01 | meal_logging | I ate one box from the synthetic curry lunch batch for lunch on 2026-11-18. Please record it. | None | Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated. |
| M02 | meal_logging | I ate one box from the synthetic curry dinner batch for dinner on 2026-11-18. Please record it. | None | Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated. |
| M03 | meal_logging | I ate one box from the synthetic curry lunch batch for breakfast on 2026-11-17. Please record it. | None | Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated. |
| M04 | meal_logging | I ate one box from the synthetic curry dinner batch for lunch on 2026-11-17. Please record it. | None | Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated. |
| M05 | meal_logging | I ate one box from the synthetic curry lunch batch for dinner on 2026-11-18. Please record it. | None | Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated. |
| M06 | meal_logging | I ate one box from the synthetic curry dinner batch for breakfast on 2026-11-16. Please record it. | None | Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated. |
| M07 | meal_logging | I ate one box from the synthetic curry lunch batch as a snack on 2026-11-17. Please record it. | None | Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated. |
| M08 | meal_logging | I ate one box of curry for dinner today. Please record it. | Synthetic curry lunch batch. | Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated. |
| C01 | corrections | Correct the unique November 17 lunch record to breakfast on 2026-11-18. | approve after preview | Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval. |
| C02 | corrections | Correct the unique November 17 lunch record to a snack on 2026-11-16. | approve after preview | Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval. |
| C03 | corrections | Correct the unique November 17 lunch record to dinner on 2026-11-18. | approve after preview | Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval. |
| C04 | corrections | Correct the unique November 17 lunch record to breakfast on 2026-11-16. | approve after preview | Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval. |
| C05 | corrections | Correct the unique November 17 lunch record to a snack on 2026-11-18. | approve after preview | Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval. |
| C06 | corrections | Correct the unique November 17 lunch record to dinner on 2026-11-16. | approve after preview | Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval. |
| C07 | corrections | Correct the unique November 17 lunch record to breakfast on 2026-11-18. | approve after preview | Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval. |
| C08 | corrections | Correct the unique November 17 lunch record to a snack on 2026-11-16. | reject after preview | Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval. |
| C09 | corrections | Correct the unique November 17 lunch record to dinner on 2026-11-18. | reject after preview | Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval. |
| C10 | corrections | Correct the unique November 17 lunch record to breakfast on 2026-11-16. | reject after preview | Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval. |
| Q01 | queries | How many boxes remain in each synthetic curry batch? | None | List remaining boxes for both batches without changing inventory. |
| Q02 | queries | What are the four exact per-box nutrient values for the synthetic curry lunch batch? | None | List all four per-box nutrient values from the fixture and identify them as synthetic. |
| Q03 | queries | List synthetic inventory ingredient quantities and units. | None | Report only synthetic inventory quantities and units from the fixture; do not describe them as real inventory. |
| Q04 | queries | Summarize recorded meals and exact totals for November 16. | None | Summarize only November 16 meals and state that totals cover recorded prepared meals. |
| Q05 | queries | What are my configured meal and daily nutrient targets? | None | List meal and daily targets separately, with all four values for each. |
| U01 | unanswerable | How many calories were in my homemade lunch on November 10, 2026? | None | Explain that no matching meal record exists and exact nutrition is unavailable; invent no numbers. |
| U02 | unanswerable | What dish did I eat on November 10, and how many calories did it contain? | None | Explain that no matching record exists, so neither the dish nor calories can be determined; invent neither. |

## Limits and interpretation

Several questions vary only quantities, dates, or meal labels. Preparation cases request previews followed by rejection. Insufficient-stock reconciliation and successful preparation confirmation are not fully represented. These are limitations inferred from the dataset; passing tests does not establish broad model performance or complete scenario coverage.

The earlier review fixed unreachable preparation fixtures, required batch clarification for M08, and added reproducibility metadata. Formal failure analysis must use an observed live failure trace; none is available yet.

## Sources

- [Formal tasks](../tasks.jsonl): verbatim questions, fixtures, expected state changes, order rules, and rubrics.
- [Frozen configuration](../eval_config.json): clock, language revision, model settings, and hashes.
- [Reporting implementation](../nutrition_eval/report.py): metric definitions.
- Prior test and dry-run counts above come from this chat’s earlier execution records.

## Shared implementation follow-up

English is now the default in the shared agent implementation; evaluation language subclasses were removed. The updated full suite passed 165 tests, including help, explicit/implicit recovery, and errors. Source quotations and user data retain their original language. Formal model results remain pending.
