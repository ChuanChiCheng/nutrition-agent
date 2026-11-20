# Evaluation task questions and passing standards

This is a readable reference generated from the current [tasks.jsonl](../tasks.jsonl). It states the existing standards; it does not add requirements or change scoring. All 50 formal tasks are listed below. Four development tasks are separate and are not included.

- Dataset/task version: `nutrition-eval-50-v2`.
- Dataset SHA-256: `18150dbd01141402c6532e503214c50a927e771548530e886951018bbc79f772`.
- Fixed application time: `2026-11-18T07:30:00-08:00` (`America/Los_Angeles`). “Today” means November 18, 2026.
- All fixture values are synthetic; they are not verified personal dietary data.

## What counts as success?

Every attempt must pass all three checks:

1. **Final business state:** apply only the listed changes to the starting data. All unrelated records, inventory, nutrition snapshots, and history must remain unchanged. No listed change means no business-data change is permitted.
2. **Required process:** follow the listed clarification, preview, approval/rejection, and write requirements. Approvals bind to the actual displayed preview ID. Only release scripted answers after an explicit successful question; M08 also requires the batch topic.
3. **Response rubric:** satisfy every listed criterion using the complete rendered conversation, including preview and approval/rejection responses. The criteria are not a single required wording or a model answer.

A controller error, timeout, or exhausted resource budget fails the attempt. A judge outage instead makes the batch incomplete. Process records such as previews and workflow sessions are retained for diagnosis but are not compared as final business state.

The data tables below provide context for interpreting the question and rubric. The source JSONL contains the full fixture, including catalog, events, allocations, and provenance. Expand the exact state-change specification to inspect the complete stored answer key. It is not passed to controllers.

## Index

- **Nutrition (10):** [N01](#n01), [N02](#n02), [N03](#n03), [N04](#n04), [N05](#n05), [N06](#n06), [N07](#n07), [N08](#n08), [N09](#n09), [N10](#n10)
- **Preparation (8):** [P01](#p01), [P02](#p02), [P03](#p03), [P04](#p04), [P05](#p05), [P06](#p06), [P07](#p07), [P08](#p08)
- **Addons (7):** [A01](#a01), [A02](#a02), [A03](#a03), [A04](#a04), [A05](#a05), [A06](#a06), [A07](#a07)
- **Meal logging (8):** [M01](#m01), [M02](#m02), [M03](#m03), [M04](#m04), [M05](#m05), [M06](#m06), [M07](#m07), [M08](#m08)
- **Corrections (10):** [C01](#c01), [C02](#c02), [C03](#c03), [C04](#c04), [C05](#c05), [C06](#c06), [C07](#c07), [C08](#c08), [C09](#c09), [C10](#c10)
- **Queries (5):** [Q01](#q01), [Q02](#q02), [Q03](#q03), [Q04](#q04), [Q05](#q05)
- **Missing information (2):** [U01](#u01), [U02](#u02)

<a id="n01"></a>

## N01 — Nutrition

**Question**

> Does the synthetic curry lunch batch meet the meal targets? List all four actual values and targets.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Stored target checks (boundaries are inclusive; do not use rounded display values):

| Batch | Nutrient | Actual | Target | Lower | Upper | Pass |
|---|---|---:|---:|---:|---:|---|
| Synthetic curry lunch batch | kcal | 600 | 600 | 570 | 630 | True |
| Synthetic curry lunch batch | protein_g | 40 | 40 | 40 | 44 | True |
| Synthetic curry lunch batch | carbs_g | 65 | 65 | 58.5 | 71.5 | True |
| Synthetic curry lunch batch | fat_g | 20 | 20 | 18 | 22 | True |
| Synthetic curry dinner batch | kcal | 550 | 600 | 570 | 630 | False |
| Synthetic curry dinner batch | protein_g | 38 | 40 | 40 | 44 | False |
| Synthetic curry dinner batch | carbs_g | 60 | 65 | 58.5 | 71.5 | True |
| Synthetic curry dinner batch | fat_g | 18 | 20 | 18 | 22 | True |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. List the four synthetic nutrient values, targets, and correct overall target status.

<a id="n02"></a>

## N02 — Nutrition

**Question**

> How much protein and carbohydrate does the synthetic curry lunch batch contain? Also explain its overall target status.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Stored target checks (boundaries are inclusive; do not use rounded display values):

| Batch | Nutrient | Actual | Target | Lower | Upper | Pass |
|---|---|---:|---:|---:|---:|---|
| Synthetic curry lunch batch | kcal | 600 | 600 | 570 | 630 | True |
| Synthetic curry lunch batch | protein_g | 40 | 40 | 40 | 44 | True |
| Synthetic curry lunch batch | carbs_g | 65 | 65 | 58.5 | 71.5 | True |
| Synthetic curry lunch batch | fat_g | 20 | 20 | 18 | 22 | True |
| Synthetic curry dinner batch | kcal | 550 | 600 | 570 | 630 | False |
| Synthetic curry dinner batch | protein_g | 38 | 40 | 40 | 44 | False |
| Synthetic curry dinner batch | carbs_g | 60 | 65 | 58.5 | 71.5 | True |
| Synthetic curry dinner batch | fat_g | 18 | 20 | 18 | 22 | True |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Correctly report protein and carbohydrate and determine overall status from all four nutrients.

<a id="n03"></a>

## N03 — Nutrition

**Question**

> List the allowed upper and lower bounds for all four nutrients in the synthetic curry lunch batch and compare each.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Stored target checks (boundaries are inclusive; do not use rounded display values):

| Batch | Nutrient | Actual | Target | Lower | Upper | Pass |
|---|---|---:|---:|---:|---:|---|
| Synthetic curry lunch batch | kcal | 600 | 600 | 570 | 630 | True |
| Synthetic curry lunch batch | protein_g | 40 | 40 | 40 | 44 | True |
| Synthetic curry lunch batch | carbs_g | 65 | 65 | 58.5 | 71.5 | True |
| Synthetic curry lunch batch | fat_g | 20 | 20 | 18 | 22 | True |
| Synthetic curry dinner batch | kcal | 550 | 600 | 570 | 630 | False |
| Synthetic curry dinner batch | protein_g | 38 | 40 | 40 | 44 | False |
| Synthetic curry dinner batch | carbs_g | 60 | 65 | 58.5 | 71.5 | True |
| Synthetic curry dinner batch | fat_g | 18 | 20 | 18 | 22 | True |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Calculate the four upper and lower bounds and compare each without rounding.

<a id="n04"></a>

## N04 — Nutrition

**Question**

> Are all four nutrients in the synthetic curry lunch batch within their allowed ranges? Give each difference.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Stored target checks (boundaries are inclusive; do not use rounded display values):

| Batch | Nutrient | Actual | Target | Lower | Upper | Pass |
|---|---|---:|---:|---:|---:|---|
| Synthetic curry lunch batch | kcal | 600 | 600 | 570 | 630 | True |
| Synthetic curry lunch batch | protein_g | 40 | 40 | 40 | 44 | True |
| Synthetic curry lunch batch | carbs_g | 65 | 65 | 58.5 | 71.5 | True |
| Synthetic curry lunch batch | fat_g | 20 | 20 | 18 | 22 | True |
| Synthetic curry dinner batch | kcal | 550 | 600 | 570 | 630 | False |
| Synthetic curry dinner batch | protein_g | 38 | 40 | 40 | 44 | False |
| Synthetic curry dinner batch | carbs_g | 60 | 65 | 58.5 | 71.5 | True |
| Synthetic curry dinner batch | fat_g | 18 | 20 | 18 | 22 | True |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. List all four differences and allowed ranges; do not judge using rounded display values.

<a id="n05"></a>

## N05 — Nutrition

**Question**

> Compare the four per-box nutrients in both synthetic curry batches and identify any failing nutrients in each.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Stored target checks (boundaries are inclusive; do not use rounded display values):

| Batch | Nutrient | Actual | Target | Lower | Upper | Pass |
|---|---|---:|---:|---:|---:|---|
| Synthetic curry lunch batch | kcal | 600 | 600 | 570 | 630 | True |
| Synthetic curry lunch batch | protein_g | 40 | 40 | 40 | 44 | True |
| Synthetic curry lunch batch | carbs_g | 65 | 65 | 58.5 | 71.5 | True |
| Synthetic curry lunch batch | fat_g | 20 | 20 | 18 | 22 | True |
| Synthetic curry dinner batch | kcal | 550 | 600 | 570 | 630 | False |
| Synthetic curry dinner batch | protein_g | 38 | 40 | 40 | 44 | False |
| Synthetic curry dinner batch | carbs_g | 60 | 65 | 58.5 | 71.5 | True |
| Synthetic curry dinner batch | fat_g | 18 | 20 | 18 | 22 | True |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Correctly compare all four nutrients across both batches without confusing them.

<a id="n06"></a>

## N06 — Nutrition

**Question**

> Do calories and protein in the synthetic curry dinner batch meet the meal targets? Explain your reasoning.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Stored target checks (boundaries are inclusive; do not use rounded display values):

| Batch | Nutrient | Actual | Target | Lower | Upper | Pass |
|---|---|---:|---:|---:|---:|---|
| Synthetic curry lunch batch | kcal | 600 | 600 | 570 | 630 | True |
| Synthetic curry lunch batch | protein_g | 40 | 40 | 40 | 44 | True |
| Synthetic curry lunch batch | carbs_g | 65 | 65 | 58.5 | 71.5 | True |
| Synthetic curry lunch batch | fat_g | 20 | 20 | 18 | 22 | True |
| Synthetic curry dinner batch | kcal | 550 | 600 | 570 | 630 | False |
| Synthetic curry dinner batch | protein_g | 38 | 40 | 40 | 44 | False |
| Synthetic curry dinner batch | carbs_g | 60 | 65 | 58.5 | 71.5 | True |
| Synthetic curry dinner batch | fat_g | 18 | 20 | 18 | 22 | True |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Judge calories and protein using the synthetic dinner batch fixture values.

<a id="n07"></a>

## N07 — Nutrition

**Question**

> Compare meal and daily targets for the synthetic curry lunch batch; keep them separate.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Stored target checks (boundaries are inclusive; do not use rounded display values):

| Batch | Nutrient | Actual | Target | Lower | Upper | Pass |
|---|---|---:|---:|---:|---:|---|
| Synthetic curry lunch batch | kcal | 600 | 600 | 570 | 630 | True |
| Synthetic curry lunch batch | protein_g | 40 | 40 | 40 | 44 | True |
| Synthetic curry lunch batch | carbs_g | 65 | 65 | 58.5 | 71.5 | True |
| Synthetic curry lunch batch | fat_g | 20 | 20 | 18 | 22 | True |
| Synthetic curry dinner batch | kcal | 550 | 600 | 570 | 630 | False |
| Synthetic curry dinner batch | protein_g | 38 | 40 | 40 | 44 | False |
| Synthetic curry dinner batch | carbs_g | 60 | 65 | 58.5 | 71.5 | True |
| Synthetic curry dinner batch | fat_g | 18 | 20 | 18 | 22 | True |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Distinguish meal and daily targets and correctly report this batch's per-box results.

<a id="n08"></a>

## N08 — Nutrition

**Question**

> Considering only fat and carbohydrates in the synthetic curry lunch batch, does each meet its target?

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Stored target checks (boundaries are inclusive; do not use rounded display values):

| Batch | Nutrient | Actual | Target | Lower | Upper | Pass |
|---|---|---:|---:|---:|---:|---|
| Synthetic curry lunch batch | kcal | 600 | 600 | 570 | 630 | True |
| Synthetic curry lunch batch | protein_g | 40 | 40 | 40 | 44 | True |
| Synthetic curry lunch batch | carbs_g | 65 | 65 | 58.5 | 71.5 | True |
| Synthetic curry lunch batch | fat_g | 20 | 20 | 18 | 22 | True |
| Synthetic curry dinner batch | kcal | 550 | 600 | 570 | 630 | False |
| Synthetic curry dinner batch | protein_g | 38 | 40 | 40 | 44 | False |
| Synthetic curry dinner batch | carbs_g | 60 | 65 | 58.5 | 71.5 | True |
| Synthetic curry dinner batch | fat_g | 18 | 20 | 18 | 22 | True |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Correctly report fat and carbohydrate values and their pass status.

<a id="n09"></a>

## N09 — Nutrition

**Question**

> If the synthetic curry lunch batch is exactly at all four lower bounds, does it pass? List the values.

**Starting context**

- Labels: `edge`.
- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 570 / 40 / 58.5 / 18 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Stored target checks (boundaries are inclusive; do not use rounded display values):

| Batch | Nutrient | Actual | Target | Lower | Upper | Pass |
|---|---|---:|---:|---:|---:|---|
| Synthetic curry lunch batch | kcal | 570 | 600 | 570 | 630 | True |
| Synthetic curry lunch batch | protein_g | 40 | 40 | 40 | 44 | True |
| Synthetic curry lunch batch | carbs_g | 58.5 | 65 | 58.5 | 71.5 | True |
| Synthetic curry lunch batch | fat_g | 18 | 20 | 18 | 22 | True |
| Synthetic curry dinner batch | kcal | 550 | 600 | 570 | 630 | False |
| Synthetic curry dinner batch | protein_g | 38 | 40 | 40 | 44 | False |
| Synthetic curry dinner batch | carbs_g | 60 | 65 | 58.5 | 71.5 | True |
| Synthetic curry dinner batch | fat_g | 18 | 20 | 18 | 22 | True |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. List the four lower bounds and explain that equality satisfies the limits.

<a id="n10"></a>

## N10 — Nutrition

**Question**

> The synthetic curry lunch batch has 569.9 kcal, below the 570 kcal lower bound. Does it pass overall?

**Starting context**

- Labels: `edge`.
- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 569.9 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Stored target checks (boundaries are inclusive; do not use rounded display values):

| Batch | Nutrient | Actual | Target | Lower | Upper | Pass |
|---|---|---:|---:|---:|---:|---|
| Synthetic curry lunch batch | kcal | 569.9 | 600 | 570 | 630 | False |
| Synthetic curry lunch batch | protein_g | 40 | 40 | 40 | 44 | True |
| Synthetic curry lunch batch | carbs_g | 65 | 65 | 58.5 | 71.5 | True |
| Synthetic curry lunch batch | fat_g | 20 | 20 | 18 | 22 | True |
| Synthetic curry dinner batch | kcal | 550 | 600 | 570 | 630 | False |
| Synthetic curry dinner batch | protein_g | 38 | 40 | 40 | 44 | False |
| Synthetic curry dinner batch | carbs_g | 60 | 65 | 58.5 | 71.5 | True |
| Synthetic curry dinner batch | fat_g | 18 | 20 | 18 | 22 | True |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Explain that calories are below the lower bound, so the overall result fails even if the other three nutrients pass.

<a id="p01"></a>

## P01 — Preparation

**Question**

> Preview preparing 5 boxes using 300 g raw chicken breast and 150 g dry rice on November 18; do not save without approval.

**Starting context**

- Inventory is confirmed. Workflow stage: `cooking`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **reject** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Explain total ingredient usage and each batch allocation; do not claim saving after rejection.

<a id="p02"></a>

## P02 — Preparation

**Question**

> Preview preparing 6 boxes using 400 g raw chicken breast and 200 g dry rice on November 18; do not save without approval.

**Starting context**

- Inventory is confirmed. Workflow stage: `cooking`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **reject** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Explain total ingredient usage and each batch allocation; do not claim saving after rejection.

<a id="p03"></a>

## P03 — Preparation

**Question**

> Preview preparing 4 boxes using 500 g raw chicken breast and 250 g dry rice on November 18; do not save without approval.

**Starting context**

- Inventory is confirmed. Workflow stage: `cooking`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **reject** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Explain total ingredient usage and each batch allocation; do not claim saving after rejection.

<a id="p04"></a>

## P04 — Preparation

**Question**

> Preview preparing 5 boxes using 600 g raw chicken breast and 300 g dry rice on November 18; do not save without approval.

**Starting context**

- Inventory is confirmed. Workflow stage: `cooking`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **reject** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Explain total ingredient usage and each batch allocation; do not claim saving after rejection.

<a id="p05"></a>

## P05 — Preparation

**Question**

> Preview preparing 6 boxes using 700 g raw chicken breast and 350 g dry rice on November 18; do not save without approval.

**Starting context**

- Inventory is confirmed. Workflow stage: `cooking`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **reject** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Explain total ingredient usage and each batch allocation; do not claim saving after rejection.

<a id="p06"></a>

## P06 — Preparation

**Question**

> Preview preparing 4 boxes using 800 g raw chicken breast and 400 g dry rice on November 18; do not save without approval.

**Starting context**

- Inventory is confirmed. Workflow stage: `cooking`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **reject** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Explain total ingredient usage and each batch allocation; do not claim saving after rejection.

<a id="p07"></a>

## P07 — Preparation

**Question**

> Preview preparing 5 boxes using 450 g raw chicken breast and 225 g dry rice on November 18; do not save without approval.

**Starting context**

- Inventory is confirmed. Workflow stage: `cooking`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **reject** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Explain total ingredient usage and each batch allocation; do not claim saving after rejection.

<a id="p08"></a>

## P08 — Preparation

**Question**

> Preview cooking 500 g raw chicken breast and 250 g dry rice, allocated exactly to 3 lunch boxes and 1 curry-only box.

**Starting context**

- Labels: `edge`.
- Inventory is confirmed. Workflow stage: `cooking`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **reject** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Explain total ingredient usage and each batch allocation; do not claim saving after rejection.

<a id="a01"></a>

## A01 — Addons

**Question**

> Set the synthetic curry lunch batch's default addon to 1 serving of synthetic yogurt.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **approve** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval → write.

**Expected final business state**

- Save addon version **1** for batch `batch-1`: 1 serving Synthetic yogurt. Do not record intake or consume stock at plan-setting time.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "insert",
    "entity": "batch_addons",
    "match": {
      "batch_id": "batch-1",
      "version": 1
    },
    "values": {
      "items": [
        {
          "ingredient_id": "yogurt",
          "quantity": "1",
          "unit": "serving",
          "state": "packaged",
          "nutrients": {
            "kcal": "100",
            "protein_g": "10",
            "carbs_g": "12",
            "fat_g": "0"
          },
          "cost": null,
          "source": {
            "status": "synthetic",
            "source_id": "evaluation-fixture:yogurt"
          },
          "price_source": null,
          "name": "Synthetic yogurt"
        }
      ]
    }
  }
]
```

</details>

**Response passing standard**

1. Explain exact addon quantities and distinguish planned default addons from actual consumption.

<a id="a02"></a>

## A02 — Addons

**Question**

> Set the synthetic curry lunch batch's default addon to 2 servings of synthetic yogurt.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **approve** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval → write.

**Expected final business state**

- Save addon version **1** for batch `batch-1`: 2 serving Synthetic yogurt. Do not record intake or consume stock at plan-setting time.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "insert",
    "entity": "batch_addons",
    "match": {
      "batch_id": "batch-1",
      "version": 1
    },
    "values": {
      "items": [
        {
          "ingredient_id": "yogurt",
          "quantity": "2",
          "unit": "serving",
          "state": "packaged",
          "nutrients": {
            "kcal": "200",
            "protein_g": "20",
            "carbs_g": "24",
            "fat_g": "0"
          },
          "cost": null,
          "source": {
            "status": "synthetic",
            "source_id": "evaluation-fixture:yogurt"
          },
          "price_source": null,
          "name": "Synthetic yogurt"
        }
      ]
    }
  }
]
```

</details>

**Response passing standard**

1. Explain exact addon quantities and distinguish planned default addons from actual consumption.

<a id="a03"></a>

## A03 — Addons

**Question**

> Set the synthetic curry lunch batch's default addon to 0.5 servings of synthetic yogurt.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **approve** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval → write.

**Expected final business state**

- Save addon version **1** for batch `batch-1`: 0.5 serving Synthetic yogurt. Do not record intake or consume stock at plan-setting time.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "insert",
    "entity": "batch_addons",
    "match": {
      "batch_id": "batch-1",
      "version": 1
    },
    "values": {
      "items": [
        {
          "ingredient_id": "yogurt",
          "quantity": "0.5",
          "unit": "serving",
          "state": "packaged",
          "nutrients": {
            "kcal": "50",
            "protein_g": "5",
            "carbs_g": "6",
            "fat_g": "0"
          },
          "cost": null,
          "source": {
            "status": "synthetic",
            "source_id": "evaluation-fixture:yogurt"
          },
          "price_source": null,
          "name": "Synthetic yogurt"
        }
      ]
    }
  }
]
```

</details>

**Response passing standard**

1. Explain exact addon quantities and distinguish planned default addons from actual consumption.

<a id="a04"></a>

## A04 — Addons

**Question**

> Set the synthetic curry lunch batch's default addon to 1.5 servings of synthetic yogurt.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **approve** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval → write.

**Expected final business state**

- Save addon version **1** for batch `batch-1`: 1.5 serving Synthetic yogurt. Do not record intake or consume stock at plan-setting time.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "insert",
    "entity": "batch_addons",
    "match": {
      "batch_id": "batch-1",
      "version": 1
    },
    "values": {
      "items": [
        {
          "ingredient_id": "yogurt",
          "quantity": "1.5",
          "unit": "serving",
          "state": "packaged",
          "nutrients": {
            "kcal": "150",
            "protein_g": "15",
            "carbs_g": "18",
            "fat_g": "0"
          },
          "cost": null,
          "source": {
            "status": "synthetic",
            "source_id": "evaluation-fixture:yogurt"
          },
          "price_source": null,
          "name": "Synthetic yogurt"
        }
      ]
    }
  }
]
```

</details>

**Response passing standard**

1. Explain exact addon quantities and distinguish planned default addons from actual consumption.

<a id="a05"></a>

## A05 — Addons

**Question**

> Set the synthetic curry lunch batch's default addon to 3 servings of synthetic yogurt.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **approve** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval → write.

**Expected final business state**

- Save addon version **1** for batch `batch-1`: 3 serving Synthetic yogurt. Do not record intake or consume stock at plan-setting time.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "insert",
    "entity": "batch_addons",
    "match": {
      "batch_id": "batch-1",
      "version": 1
    },
    "values": {
      "items": [
        {
          "ingredient_id": "yogurt",
          "quantity": "3",
          "unit": "serving",
          "state": "packaged",
          "nutrients": {
            "kcal": "300",
            "protein_g": "30",
            "carbs_g": "36",
            "fat_g": "0"
          },
          "cost": null,
          "source": {
            "status": "synthetic",
            "source_id": "evaluation-fixture:yogurt"
          },
          "price_source": null,
          "name": "Synthetic yogurt"
        }
      ]
    }
  }
]
```

</details>

**Response passing standard**

1. Explain exact addon quantities and distinguish planned default addons from actual consumption.

<a id="a06"></a>

## A06 — Addons

**Question**

> Set the synthetic curry lunch batch's default addon to 30 g of synthetic oats.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **reject** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Explain exact addon quantities and distinguish planned default addons from actual consumption.

<a id="a07"></a>

## A07 — Addons

**Question**

> Set the synthetic curry lunch batch's default addon to 50 g of synthetic oats.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **reject** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Explain exact addon quantities and distinguish planned default addons from actual consumption.

<a id="m01"></a>

## M01 — Meal logging

**Question**

> I ate one box from the synthetic curry lunch batch for lunch on 2026-11-18. Please record it.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

- Required event: `write`.

**Expected final business state**

- Set remaining boxes to **3** for {"cooking_run_id": "run-seed", "name": "Synthetic curry lunch batch"}.
- Add one meal record: batch `batch-1`, date **2026-11-18**, meal **lunch**, 1 box(es). Use the specified stored nutrient/addon/source snapshot.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "batches",
    "match": {
      "cooking_run_id": "run-seed",
      "name": "Synthetic curry lunch batch"
    },
    "values": {
      "remaining_boxes": 3
    }
  },
  {
    "op": "insert",
    "entity": "events",
    "match": {
      "batch_id": "batch-1",
      "eaten_on": "2026-11-18",
      "meal": "lunch",
      "boxes": 1
    },
    "values": {
      "data": {
        "batch_id": "batch-1",
        "batch_name": "Synthetic curry lunch batch",
        "eaten_on": "2026-11-18",
        "meal": "lunch",
        "box_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated.

<a id="m02"></a>

## M02 — Meal logging

**Question**

> I ate one box from the synthetic curry dinner batch for dinner on 2026-11-18. Please record it.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

- Required event: `write`.

**Expected final business state**

- Set remaining boxes to **2** for {"cooking_run_id": "run-seed", "name": "Synthetic curry dinner batch"}.
- Add one meal record: batch `batch-2`, date **2026-11-18**, meal **dinner**, 1 box(es). Use the specified stored nutrient/addon/source snapshot.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "batches",
    "match": {
      "cooking_run_id": "run-seed",
      "name": "Synthetic curry dinner batch"
    },
    "values": {
      "remaining_boxes": 2
    }
  },
  {
    "op": "insert",
    "entity": "events",
    "match": {
      "batch_id": "batch-2",
      "eaten_on": "2026-11-18",
      "meal": "dinner",
      "boxes": 1
    },
    "values": {
      "data": {
        "batch_id": "batch-2",
        "batch_name": "Synthetic curry dinner batch",
        "eaten_on": "2026-11-18",
        "meal": "dinner",
        "box_nutrients": {
          "kcal": "550",
          "protein_g": "38",
          "carbs_g": "60",
          "fat_g": "18"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "550",
          "protein_g": "38",
          "carbs_g": "60",
          "fat_g": "18"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated.

<a id="m03"></a>

## M03 — Meal logging

**Question**

> I ate one box from the synthetic curry lunch batch for breakfast on 2026-11-17. Please record it.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

- Required event: `write`.

**Expected final business state**

- Set remaining boxes to **3** for {"cooking_run_id": "run-seed", "name": "Synthetic curry lunch batch"}.
- Add one meal record: batch `batch-1`, date **2026-11-17**, meal **breakfast**, 1 box(es). Use the specified stored nutrient/addon/source snapshot.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "batches",
    "match": {
      "cooking_run_id": "run-seed",
      "name": "Synthetic curry lunch batch"
    },
    "values": {
      "remaining_boxes": 3
    }
  },
  {
    "op": "insert",
    "entity": "events",
    "match": {
      "batch_id": "batch-1",
      "eaten_on": "2026-11-17",
      "meal": "breakfast",
      "boxes": 1
    },
    "values": {
      "data": {
        "batch_id": "batch-1",
        "batch_name": "Synthetic curry lunch batch",
        "eaten_on": "2026-11-17",
        "meal": "breakfast",
        "box_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated.

<a id="m04"></a>

## M04 — Meal logging

**Question**

> I ate one box from the synthetic curry dinner batch for lunch on 2026-11-17. Please record it.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

- Required event: `write`.

**Expected final business state**

- Set remaining boxes to **2** for {"cooking_run_id": "run-seed", "name": "Synthetic curry dinner batch"}.
- Add one meal record: batch `batch-2`, date **2026-11-17**, meal **lunch**, 1 box(es). Use the specified stored nutrient/addon/source snapshot.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "batches",
    "match": {
      "cooking_run_id": "run-seed",
      "name": "Synthetic curry dinner batch"
    },
    "values": {
      "remaining_boxes": 2
    }
  },
  {
    "op": "insert",
    "entity": "events",
    "match": {
      "batch_id": "batch-2",
      "eaten_on": "2026-11-17",
      "meal": "lunch",
      "boxes": 1
    },
    "values": {
      "data": {
        "batch_id": "batch-2",
        "batch_name": "Synthetic curry dinner batch",
        "eaten_on": "2026-11-17",
        "meal": "lunch",
        "box_nutrients": {
          "kcal": "550",
          "protein_g": "38",
          "carbs_g": "60",
          "fat_g": "18"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "550",
          "protein_g": "38",
          "carbs_g": "60",
          "fat_g": "18"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated.

<a id="m05"></a>

## M05 — Meal logging

**Question**

> I ate one box from the synthetic curry lunch batch for dinner on 2026-11-18. Please record it.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

- Required event: `write`.

**Expected final business state**

- Set remaining boxes to **3** for {"cooking_run_id": "run-seed", "name": "Synthetic curry lunch batch"}.
- Add one meal record: batch `batch-1`, date **2026-11-18**, meal **dinner**, 1 box(es). Use the specified stored nutrient/addon/source snapshot.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "batches",
    "match": {
      "cooking_run_id": "run-seed",
      "name": "Synthetic curry lunch batch"
    },
    "values": {
      "remaining_boxes": 3
    }
  },
  {
    "op": "insert",
    "entity": "events",
    "match": {
      "batch_id": "batch-1",
      "eaten_on": "2026-11-18",
      "meal": "dinner",
      "boxes": 1
    },
    "values": {
      "data": {
        "batch_id": "batch-1",
        "batch_name": "Synthetic curry lunch batch",
        "eaten_on": "2026-11-18",
        "meal": "dinner",
        "box_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated.

<a id="m06"></a>

## M06 — Meal logging

**Question**

> I ate one box from the synthetic curry dinner batch for breakfast on 2026-11-16. Please record it.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

- Required event: `write`.

**Expected final business state**

- Set remaining boxes to **2** for {"cooking_run_id": "run-seed", "name": "Synthetic curry dinner batch"}.
- Add one meal record: batch `batch-2`, date **2026-11-16**, meal **breakfast**, 1 box(es). Use the specified stored nutrient/addon/source snapshot.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "batches",
    "match": {
      "cooking_run_id": "run-seed",
      "name": "Synthetic curry dinner batch"
    },
    "values": {
      "remaining_boxes": 2
    }
  },
  {
    "op": "insert",
    "entity": "events",
    "match": {
      "batch_id": "batch-2",
      "eaten_on": "2026-11-16",
      "meal": "breakfast",
      "boxes": 1
    },
    "values": {
      "data": {
        "batch_id": "batch-2",
        "batch_name": "Synthetic curry dinner batch",
        "eaten_on": "2026-11-16",
        "meal": "breakfast",
        "box_nutrients": {
          "kcal": "550",
          "protein_g": "38",
          "carbs_g": "60",
          "fat_g": "18"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "550",
          "protein_g": "38",
          "carbs_g": "60",
          "fat_g": "18"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated.

<a id="m07"></a>

## M07 — Meal logging

**Question**

> I ate one box from the synthetic curry lunch batch as a snack on 2026-11-17. Please record it.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

- Required event: `write`.

**Expected final business state**

- Set remaining boxes to **3** for {"cooking_run_id": "run-seed", "name": "Synthetic curry lunch batch"}.
- Add one meal record: batch `batch-1`, date **2026-11-17**, meal **snack**, 1 box(es). Use the specified stored nutrient/addon/source snapshot.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "batches",
    "match": {
      "cooking_run_id": "run-seed",
      "name": "Synthetic curry lunch batch"
    },
    "values": {
      "remaining_boxes": 3
    }
  },
  {
    "op": "insert",
    "entity": "events",
    "match": {
      "batch_id": "batch-1",
      "eaten_on": "2026-11-17",
      "meal": "snack",
      "boxes": 1
    },
    "values": {
      "data": {
        "batch_id": "batch-1",
        "batch_name": "Synthetic curry lunch batch",
        "eaten_on": "2026-11-17",
        "meal": "snack",
        "box_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated.

<a id="m08"></a>

## M08 — Meal logging

**Question**

> I ate one box of curry for dinner today. Please record it.

**Starting context**

- Labels: `edge`.
- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

**Scripted user interaction**

Answers supplied in order after a successful clarification question:
1. Synthetic curry lunch batch.

No approval or rejection is scripted.

**Required process**

- ask_user (topic: batch) → scripted_answer → write.

**Expected final business state**

- Set remaining boxes to **3** for {"cooking_run_id": "run-seed", "name": "Synthetic curry lunch batch"}.
- Add one meal record: batch `batch-1`, date **2026-11-18**, meal **dinner**, 1 box(es). Use the specified stored nutrient/addon/source snapshot.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "batches",
    "match": {
      "cooking_run_id": "run-seed",
      "name": "Synthetic curry lunch batch"
    },
    "values": {
      "remaining_boxes": 3
    }
  },
  {
    "op": "insert",
    "entity": "events",
    "match": {
      "batch_id": "batch-1",
      "eaten_on": "2026-11-18",
      "meal": "dinner",
      "boxes": 1
    },
    "values": {
      "data": {
        "batch_id": "batch-1",
        "batch_name": "Synthetic curry lunch batch",
        "eaten_on": "2026-11-18",
        "meal": "dinner",
        "box_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Confirm batch, date, and meal; claim completion only after the event and remaining boxes were successfully updated.

<a id="c01"></a>

## C01 — Corrections

**Question**

> Correct the unique November 17 lunch record to breakfast on 2026-11-18.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **approve** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval → write.

**Expected final business state**

- Update the existing meal matching {"batch_id": "batch-1", "eaten_on": "2026-11-17", "meal": "lunch"} to date **2026-11-18**, meal **breakfast**. Preserve the previous snapshot in history and retain unchanged nutrition and batch data as specified.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "events",
    "match": {
      "batch_id": "batch-1",
      "eaten_on": "2026-11-17",
      "meal": "lunch"
    },
    "values": {
      "eaten_on": "2026-11-18",
      "meal": "breakfast",
      "data": {
        "batch_id": "batch-1",
        "batch_name": "Synthetic curry lunch batch",
        "eaten_on": "2026-11-18",
        "meal": "breakfast",
        "box_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ],
        "history": [
          {
            "snapshot": {
              "batch_id": "batch-1",
              "batch_name": "Synthetic curry lunch batch",
              "eaten_on": "2026-11-17",
              "meal": "lunch",
              "box_nutrients": {
                "kcal": "600",
                "protein_g": "40",
                "carbs_g": "65",
                "fat_g": "20"
              },
              "addon_items": [],
              "addon_nutrients": {
                "kcal": "0",
                "protein_g": "0",
                "carbs_g": "0",
                "fat_g": "0"
              },
              "total_nutrients": {
                "kcal": "600",
                "protein_g": "40",
                "carbs_g": "65",
                "fat_g": "20"
              },
              "addon_version": 0,
              "box_sources": [
                {
                  "status": "synthetic",
                  "source_id": "evaluation-fixture:batch"
                }
              ]
            },
            "corrected_at": "2026-11-18T07:30:00-08:00"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval.

<a id="c02"></a>

## C02 — Corrections

**Question**

> Correct the unique November 17 lunch record to a snack on 2026-11-16.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **approve** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval → write.

**Expected final business state**

- Update the existing meal matching {"batch_id": "batch-1", "eaten_on": "2026-11-17", "meal": "lunch"} to date **2026-11-16**, meal **snack**. Preserve the previous snapshot in history and retain unchanged nutrition and batch data as specified.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "events",
    "match": {
      "batch_id": "batch-1",
      "eaten_on": "2026-11-17",
      "meal": "lunch"
    },
    "values": {
      "eaten_on": "2026-11-16",
      "meal": "snack",
      "data": {
        "batch_id": "batch-1",
        "batch_name": "Synthetic curry lunch batch",
        "eaten_on": "2026-11-16",
        "meal": "snack",
        "box_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ],
        "history": [
          {
            "snapshot": {
              "batch_id": "batch-1",
              "batch_name": "Synthetic curry lunch batch",
              "eaten_on": "2026-11-17",
              "meal": "lunch",
              "box_nutrients": {
                "kcal": "600",
                "protein_g": "40",
                "carbs_g": "65",
                "fat_g": "20"
              },
              "addon_items": [],
              "addon_nutrients": {
                "kcal": "0",
                "protein_g": "0",
                "carbs_g": "0",
                "fat_g": "0"
              },
              "total_nutrients": {
                "kcal": "600",
                "protein_g": "40",
                "carbs_g": "65",
                "fat_g": "20"
              },
              "addon_version": 0,
              "box_sources": [
                {
                  "status": "synthetic",
                  "source_id": "evaluation-fixture:batch"
                }
              ]
            },
            "corrected_at": "2026-11-18T07:30:00-08:00"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval.

<a id="c03"></a>

## C03 — Corrections

**Question**

> Correct the unique November 17 lunch record to dinner on 2026-11-18.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **approve** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval → write.

**Expected final business state**

- Update the existing meal matching {"batch_id": "batch-1", "eaten_on": "2026-11-17", "meal": "lunch"} to date **2026-11-18**, meal **dinner**. Preserve the previous snapshot in history and retain unchanged nutrition and batch data as specified.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "events",
    "match": {
      "batch_id": "batch-1",
      "eaten_on": "2026-11-17",
      "meal": "lunch"
    },
    "values": {
      "eaten_on": "2026-11-18",
      "meal": "dinner",
      "data": {
        "batch_id": "batch-1",
        "batch_name": "Synthetic curry lunch batch",
        "eaten_on": "2026-11-18",
        "meal": "dinner",
        "box_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ],
        "history": [
          {
            "snapshot": {
              "batch_id": "batch-1",
              "batch_name": "Synthetic curry lunch batch",
              "eaten_on": "2026-11-17",
              "meal": "lunch",
              "box_nutrients": {
                "kcal": "600",
                "protein_g": "40",
                "carbs_g": "65",
                "fat_g": "20"
              },
              "addon_items": [],
              "addon_nutrients": {
                "kcal": "0",
                "protein_g": "0",
                "carbs_g": "0",
                "fat_g": "0"
              },
              "total_nutrients": {
                "kcal": "600",
                "protein_g": "40",
                "carbs_g": "65",
                "fat_g": "20"
              },
              "addon_version": 0,
              "box_sources": [
                {
                  "status": "synthetic",
                  "source_id": "evaluation-fixture:batch"
                }
              ]
            },
            "corrected_at": "2026-11-18T07:30:00-08:00"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval.

<a id="c04"></a>

## C04 — Corrections

**Question**

> Correct the unique November 17 lunch record to breakfast on 2026-11-16.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **approve** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval → write.

**Expected final business state**

- Update the existing meal matching {"batch_id": "batch-1", "eaten_on": "2026-11-17", "meal": "lunch"} to date **2026-11-16**, meal **breakfast**. Preserve the previous snapshot in history and retain unchanged nutrition and batch data as specified.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "events",
    "match": {
      "batch_id": "batch-1",
      "eaten_on": "2026-11-17",
      "meal": "lunch"
    },
    "values": {
      "eaten_on": "2026-11-16",
      "meal": "breakfast",
      "data": {
        "batch_id": "batch-1",
        "batch_name": "Synthetic curry lunch batch",
        "eaten_on": "2026-11-16",
        "meal": "breakfast",
        "box_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ],
        "history": [
          {
            "snapshot": {
              "batch_id": "batch-1",
              "batch_name": "Synthetic curry lunch batch",
              "eaten_on": "2026-11-17",
              "meal": "lunch",
              "box_nutrients": {
                "kcal": "600",
                "protein_g": "40",
                "carbs_g": "65",
                "fat_g": "20"
              },
              "addon_items": [],
              "addon_nutrients": {
                "kcal": "0",
                "protein_g": "0",
                "carbs_g": "0",
                "fat_g": "0"
              },
              "total_nutrients": {
                "kcal": "600",
                "protein_g": "40",
                "carbs_g": "65",
                "fat_g": "20"
              },
              "addon_version": 0,
              "box_sources": [
                {
                  "status": "synthetic",
                  "source_id": "evaluation-fixture:batch"
                }
              ]
            },
            "corrected_at": "2026-11-18T07:30:00-08:00"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval.

<a id="c05"></a>

## C05 — Corrections

**Question**

> Correct the unique November 17 lunch record to a snack on 2026-11-18.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **approve** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval → write.

**Expected final business state**

- Update the existing meal matching {"batch_id": "batch-1", "eaten_on": "2026-11-17", "meal": "lunch"} to date **2026-11-18**, meal **snack**. Preserve the previous snapshot in history and retain unchanged nutrition and batch data as specified.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "events",
    "match": {
      "batch_id": "batch-1",
      "eaten_on": "2026-11-17",
      "meal": "lunch"
    },
    "values": {
      "eaten_on": "2026-11-18",
      "meal": "snack",
      "data": {
        "batch_id": "batch-1",
        "batch_name": "Synthetic curry lunch batch",
        "eaten_on": "2026-11-18",
        "meal": "snack",
        "box_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ],
        "history": [
          {
            "snapshot": {
              "batch_id": "batch-1",
              "batch_name": "Synthetic curry lunch batch",
              "eaten_on": "2026-11-17",
              "meal": "lunch",
              "box_nutrients": {
                "kcal": "600",
                "protein_g": "40",
                "carbs_g": "65",
                "fat_g": "20"
              },
              "addon_items": [],
              "addon_nutrients": {
                "kcal": "0",
                "protein_g": "0",
                "carbs_g": "0",
                "fat_g": "0"
              },
              "total_nutrients": {
                "kcal": "600",
                "protein_g": "40",
                "carbs_g": "65",
                "fat_g": "20"
              },
              "addon_version": 0,
              "box_sources": [
                {
                  "status": "synthetic",
                  "source_id": "evaluation-fixture:batch"
                }
              ]
            },
            "corrected_at": "2026-11-18T07:30:00-08:00"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval.

<a id="c06"></a>

## C06 — Corrections

**Question**

> Correct the unique November 17 lunch record to dinner on 2026-11-16.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **approve** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval → write.

**Expected final business state**

- Update the existing meal matching {"batch_id": "batch-1", "eaten_on": "2026-11-17", "meal": "lunch"} to date **2026-11-16**, meal **dinner**. Preserve the previous snapshot in history and retain unchanged nutrition and batch data as specified.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "events",
    "match": {
      "batch_id": "batch-1",
      "eaten_on": "2026-11-17",
      "meal": "lunch"
    },
    "values": {
      "eaten_on": "2026-11-16",
      "meal": "dinner",
      "data": {
        "batch_id": "batch-1",
        "batch_name": "Synthetic curry lunch batch",
        "eaten_on": "2026-11-16",
        "meal": "dinner",
        "box_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ],
        "history": [
          {
            "snapshot": {
              "batch_id": "batch-1",
              "batch_name": "Synthetic curry lunch batch",
              "eaten_on": "2026-11-17",
              "meal": "lunch",
              "box_nutrients": {
                "kcal": "600",
                "protein_g": "40",
                "carbs_g": "65",
                "fat_g": "20"
              },
              "addon_items": [],
              "addon_nutrients": {
                "kcal": "0",
                "protein_g": "0",
                "carbs_g": "0",
                "fat_g": "0"
              },
              "total_nutrients": {
                "kcal": "600",
                "protein_g": "40",
                "carbs_g": "65",
                "fat_g": "20"
              },
              "addon_version": 0,
              "box_sources": [
                {
                  "status": "synthetic",
                  "source_id": "evaluation-fixture:batch"
                }
              ]
            },
            "corrected_at": "2026-11-18T07:30:00-08:00"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval.

<a id="c07"></a>

## C07 — Corrections

**Question**

> Correct the unique November 17 lunch record to breakfast on 2026-11-18.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **approve** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval → write.

**Expected final business state**

- Update the existing meal matching {"batch_id": "batch-1", "eaten_on": "2026-11-17", "meal": "lunch"} to date **2026-11-18**, meal **breakfast**. Preserve the previous snapshot in history and retain unchanged nutrition and batch data as specified.
- All business data not specified above remains unchanged.

<details>
<summary>Exact state-change answer key</summary>

```json
[
  {
    "op": "update",
    "entity": "events",
    "match": {
      "batch_id": "batch-1",
      "eaten_on": "2026-11-17",
      "meal": "lunch"
    },
    "values": {
      "eaten_on": "2026-11-18",
      "meal": "breakfast",
      "data": {
        "batch_id": "batch-1",
        "batch_name": "Synthetic curry lunch batch",
        "eaten_on": "2026-11-18",
        "meal": "breakfast",
        "box_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_items": [],
        "addon_nutrients": {
          "kcal": "0",
          "protein_g": "0",
          "carbs_g": "0",
          "fat_g": "0"
        },
        "total_nutrients": {
          "kcal": "600",
          "protein_g": "40",
          "carbs_g": "65",
          "fat_g": "20"
        },
        "addon_version": 0,
        "box_sources": [
          {
            "status": "synthetic",
            "source_id": "evaluation-fixture:batch"
          }
        ],
        "history": [
          {
            "snapshot": {
              "batch_id": "batch-1",
              "batch_name": "Synthetic curry lunch batch",
              "eaten_on": "2026-11-17",
              "meal": "lunch",
              "box_nutrients": {
                "kcal": "600",
                "protein_g": "40",
                "carbs_g": "65",
                "fat_g": "20"
              },
              "addon_items": [],
              "addon_nutrients": {
                "kcal": "0",
                "protein_g": "0",
                "carbs_g": "0",
                "fat_g": "0"
              },
              "total_nutrients": {
                "kcal": "600",
                "protein_g": "40",
                "carbs_g": "65",
                "fat_g": "20"
              },
              "addon_version": 0,
              "box_sources": [
                {
                  "status": "synthetic",
                  "source_id": "evaluation-fixture:batch"
                }
              ]
            },
            "corrected_at": "2026-11-18T07:30:00-08:00"
          }
        ]
      }
    }
  }
]
```

</details>

**Response passing standard**

1. Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval.

<a id="c08"></a>

## C08 — Corrections

**Question**

> Correct the unique November 17 lunch record to a snack on 2026-11-16.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **reject** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval.

<a id="c09"></a>

## C09 — Corrections

**Question**

> Correct the unique November 17 lunch record to dinner on 2026-11-18.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **reject** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval.

<a id="c10"></a>

## C10 — Corrections

**Question**

> Correct the unique November 17 lunch record to breakfast on 2026-11-16.

**Starting context**

- Labels: `edge`.
- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

After a preview is displayed, the scripted user will **reject** it. This is the test user’s decision, not a judgment that the preview is correct or incorrect.

**Required process**

- preview → approval.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Restate the preview date and meal, preserve historical snapshots, and claim correction only after approval.

<a id="q01"></a>

## Q01 — Queries

**Question**

> How many boxes remain in each synthetic curry batch?

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. List remaining boxes for both batches without changing inventory.

<a id="q02"></a>

## Q02 — Queries

**Question**

> What are the four exact per-box nutrient values for the synthetic curry lunch batch?

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. List all four per-box nutrient values from the fixture and identify them as synthetic.

<a id="q03"></a>

## Q03 — Queries

**Question**

> List synthetic inventory ingredient quantities and units.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Report only synthetic inventory quantities and units from the fixture; do not describe them as real inventory.

<a id="q04"></a>

## Q04 — Queries

**Question**

> Summarize recorded meals and exact totals for November 16.

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Summarize only November 16 meals and state that totals cover recorded prepared meals.

<a id="q05"></a>

## Q05 — Queries

**Question**

> What are my configured meal and daily nutrient targets?

**Starting context**

- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Inventory: chicken 2000 g (raw), rice 2000 g (dry), potato 1000 g (raw), yogurt 8 serving (packaged), oats 500 g (dry), beans 1000 g (cooked).

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. List meal and daily targets separately, with all four values for each.

<a id="u01"></a>

## U01 — Missing information

**Question**

> How many calories were in my homemade lunch on November 10, 2026?

**Starting context**

- Labels: `unanswerable`.
- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Explain that no matching meal record exists and exact nutrition is unavailable; invent no numbers.

<a id="u02"></a>

## U02 — Missing information

**Question**

> What dish did I eat on November 10, and how many calories did it contain?

**Starting context**

- Labels: `unanswerable`.
- Inventory is confirmed. Workflow stage: `ready`.
- Meal targets (kcal / protein g / carbohydrate g / fat g): **600 / 40 / 65 / 20**.
- Daily targets in the same order: **1800 / 120 / 195 / 60**.

| Batch | ID | Remaining / total boxes | Per box: kcal / protein g / carbohydrate g / fat g |
|---|---|---:|---|
| Synthetic curry lunch batch | `batch-1` | 4 / 6 | 600 / 40 / 65 / 20 |
| Synthetic curry dinner batch | `batch-2` | 3 / 4 | 550 / 38 / 60 / 18 |

Existing meal records:
- `event-old`: 2026-11-16, dinner, batch `batch-1`, 1 box(es).
- `event-correct`: 2026-11-17, lunch, batch `batch-1`, 1 box(es).
- `event-batch2`: 2026-11-16, dinner, batch `batch-2`, 1 box(es).

**Scripted user interaction**

No scripted clarification answers are supplied. Additional questions do not receive invented answers.

No approval or rejection is scripted.

**Required process**

No additional task-specific order rule. General approval and write-safety checks still apply.

**Expected final business state**

No business changes. Existing inventory, batches, meal records, and all other business data must remain unchanged.

**Response passing standard**

1. Explain that no matching record exists, so neither the dish nor calories can be determined; invent neither.

## Results are separate from standards

See the [latest formal report](../results/formal-50-english-2026-11-20-v2/report.md) for actual results: Agent 57/150 (38%), baseline 25/50 (50%). A passing standard describes what should happen; the saved episodes document what did happen.
