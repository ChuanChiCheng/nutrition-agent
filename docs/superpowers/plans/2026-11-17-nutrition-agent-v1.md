# Nutrition Agent V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal** — 依 Isaac 的實際備餐流程，建立可持續保存資料的單人 Python V1，完成料理選擇、營養客製化、分裝、食用與更正。

**Architecture** — Docker Compose 管理 Python app 與 PostgreSQL。固定主流程的各階段內使用彈性工具迴圈，營養計算、庫存、核准與交易集中在共用服務。互動使用持久化資料，後續評估使用相同服務與工具，從各題隔離的初始狀態執行。

**Tech Stack** — Docker Compose、Python 3.12、uv、PostgreSQL、psycopg 3、OpenAI Responses API、Decimal、zoneinfo、pytest。技術預設採 PostgreSQL 18 與版本化 SQL migrations，實作時鎖定已驗證的映像與套件版本。

**Spec** — `docs/specs/v1-python-demo-scope.md`。完整願景在 `docs/specs/full-product-scope.md`，課程要求在 `docs/course-requirements.md`。工作區為 `/Users/wolverine/Develop/nutrition-agent`。

## Global Constraints

以下是 Isaac 在需求訪談及本輪設計討論中確認的決定。

- 第一版為單一使用者的 Python 互動 demo，最終產品介面為 iOS App。課堂展示採獨立示範資料。
- 環境與資料庫採 Docker 與 PostgreSQL。容器重建後仍保存使用者資料。
- 使用 Isaac 自己的 OpenAI API。第一版預設 `gpt-6-luna`，模型保留為可設定選項。
- 模型優先順序為 `--model`、`OPENAI_MODEL`、`gpt-6-luna`。每次執行記錄實際模型與推理參數，參數依模型能力驗證。
- 主流程為確認食材、選定料理、客製化、確認食譜、烹調與分裝、食用紀錄。階段內依工具結果與使用者回答選擇下一步。
- 記錄、查詢與更正可直接進入對應階段。階段進度及確認狀態由應用程式保存。
- 預設沿用既有營養目標，直到使用者要求更改。每次規劃先列出庫存與數量供確認，優先使用現有食材，可建議採買新食材。
- 每次備餐預設六餐、同一道料理，使用者可指定其他餐數或更多變化。
- 先選料理，再客製化。可調整食材用量與少量替換，保留料理特色，最後由使用者確認整份食譜。
- 食譜客製化驗收為熱量目標的 95%–105%、蛋白質 100%–110%、碳水與脂肪各 90%–110%。四項同時符合才標示達標。這是產品驗收規則。
- 模型提出調整，程式計算與驗算，有限次迭代。達上限仍無解時顯示差距與選項，交由使用者決定，超出範圍仍保留未達標標示。
- 容量作為事前參考，最終份數與組成由做完後確認。同一批次每盒的組成與營養相同，營養按該批次均分。
- 同次烹調的不同餐點組成分成不同批次。該次烹調的實際食材總用量只扣除一次。
- 確認的加餐搭配與每餐用量保存於批次。吃一餐預設一盒加上確認的加餐，除非使用者明確說明有變。
- 加餐食材於記錄食用時扣除。僅建議或確認加餐方案時尚未消耗食材。
- 資訊明確的一般食用直接執行。批次或事件身分不明先列候選供確認，更正既有紀錄前預覽並取得核准。
- 使用者表示已食用，但加餐庫存不足時，先釐清漏記採買、庫存校正或本餐變動，再一次更新庫存與食用紀錄。
- 營養來源以實際商品標示優先，一般食材採 USDA。固定資料附來源，估算與合成測試資料清楚標示。
- 查詢每日四項營養相對目標的進度、各批剩餘盒數與每盒營養。保存盒內與預設加餐的分項，方便理解整餐數值。
- 目前不設嚴格預算上限，顯示整批與每餐預估成本。Walmart 為預設商店，第一版採固定資料與可核對連結。
- 第一版採文字購入資訊，經確認後入庫。即時查貨、截圖辨識、完整烹調陪伴、風味回饋循環與外食紀錄依 scope 分期。

## Review Focus

- 同次烹調建立多批成品時，食材只扣一次，分配量與營養／成本不重複計入。Task 3 檢查。
- 食用包含加餐的營養與庫存，明確略過加餐時只計盒內。Task 4 檢查。
- 日期更正維持盒數及加餐總消耗，批次／加餐更正依原快照恢復與扣除差額。Task 5 檢查。
- 重試、兩次同時操作、拒絕、過期預覽及中途失敗保持交易一致。Tasks 1、3–5 檢查。
- 缺營養、品牌或單位資料、生熟不符、歷史方案被當實績，以及模型未通過驗算就宣稱達標。Tasks 2、6–7 檢查。

## 已確認來源與現況

本輪只更新需求及計畫，產品程式、環境與資料庫尚待實作。先前終端機可用 uv，系統 python3 為 3.9.6，當時找不到 docker 命令。Task 0 重新檢查 Docker Desktop／CLI 與 Docker engine，產品執行以容器內 Python 為準。

四份 PDF 作為基礎食譜與歷史參考，原有數值需補來源並核對，實際個人營養目標在初始設定時提供。PDF 中的內容視為食譜資料。既有估算及未確認的重新分裝方案保留各自狀態。

| 食譜 | 原始來源 | SHA-256 | 已知資料情況 |
|---|---|---|---|
| 日式雞胸咖哩 | `/Users/wolverine/Downloads/Japanese_Chicken_Curry_Meal_Prep_Recipe_2026-11-01.pdf` | `b7bd116ecfaca51c9112909fce63c696462318c1f0c113dceefe8b2374c744bf` | 六盒完整便當及一盒純咖哩分開記錄。 |
| Nikujaga 豬里肌便當 | `/Users/wolverine/Downloads/nikujaga_recipe_with_images_4p.pdf` | `dc27453915434bdd32883fa269c86a44ada8d2ffc6d17d1edb4922689a9d7ec9` | 區分原六份紀錄與後續七等份方案，七等份尚非已確認成品。 |
| BBQ 豬肩肉 Mac & Cheese | `/Users/wolverine/Downloads/BBQ_豬肩肉_Mac_and_Cheese_食譜.pdf` | `3983d491f609a227c6ca3254d1c0842f5741ebd60a491ccd7331c515bc4c965c` | 五份含花椰菜與兩份不含花椰菜分開記錄，成本資料部分缺漏。 |
| 蒜香菇菇牛肉雞胸炊飯 | `/Users/wolverine/Downloads/蒜香菇菇牛肉雞胸炊飯_六餐食譜.pdf` | `2caa5efdae2192f0aa89df9ba1af686598aa13d8fc448cee49f8b4a1efb777c6` | 六餐分兩鍋，每鍋三餐，既有營養為估算。 |

Task 2 建立結構化食譜與來源 manifest，保存商品標示、USDA record ID／網址、計價基準與查核日期。圖像式 BBQ PDF 需以視覺核對抽取結果。部分價格缺漏時呈現已知小計與估算範圍，不將未知成本當零。

## 預計新增檔案

| 檔案 | 責任 |
|---|---|
| `Dockerfile`、`compose.yaml`、`.dockerignore` | app、db、db_test、鎖定環境與持久化 volume |
| `pyproject.toml`、`uv.lock`、`.python-version` | Python 3.12、依賴與鎖定版本 |
| `.env.example` | 模型及本機資料庫設定欄位 |
| `nutrition_demo/models.py` | Nutrients、Result、Preview、BatchOutput 等型別 |
| `nutrition_demo/store.py` | PostgreSQL 連線、交易、migrations、去重、狀態版本 |
| `nutrition_demo/migrations/001_initial.sql` | 初始 schema、約束及索引 |
| `nutrition_demo/nutrition.py` | 營養、成本、分配與容差檢查 |
| `nutrition_demo/catalog.py` | 四份基礎食譜與固定資料載入、候選及補充食物建議 |
| `nutrition_demo/service.py` | 個人設定、庫存、烹調成品、加餐、食用、更正及查詢 |
| `nutrition_demo/workflow.py` | 主流程、階段進度與等待使用者的狀態 |
| `nutrition_demo/agent.py` | Responses API、受限工具迴圈及客製化迭代 |
| `nutrition_demo/__init__.py`、`nutrition_demo/__main__.py` | package 與 CLI |
| `demo_data/catalog.json`、`demo_data/source_manifest.json` | 結構化食譜及可追溯來源 |
| `demo_data/scenario.json` | 獨立且清楚標示的合成情境 |
| `tests/test_demo_*.py`、`tests/conftest.py` | 計算、資料庫、互動與完整情境測試 |
| `README.md` | 啟動、初始化、seed、重開、備份、測試與目前狀態 |

## 環境、設定與啟動契約

以下命令為實作完成後的驗收入口，Docker engine、環境設定與對應程式需先可用。所有命令從 repo 根目錄執行。

### 容器環境

- `app` 使用 Python 3.12 slim，容器內以 uv 安裝 lockfile 中的 `openai`、`psycopg[binary]` 與測試依賴 pytest。預設工作目錄 `/app`，ENTRYPOINT 為 `uv run --locked python -m nutrition_demo`。
- `db` 採 PostgreSQL 18。named volume 掛載 `/var/lib/postgresql`，對應 18 的版本化 PGDATA 目錄。實作時記錄已驗證的 minor version 與映像 digest，app、uv 映像也鎖定已驗證版本。
- `db` 以 pg_isready 檢查健康，app 依賴 service_healthy。重建 app 與一般停止／啟動沿用既有 volume。
- `db_test` 採同版 PostgreSQL、獨立資料與測試 profile，`TEST_DATABASE_URL` 指向它。測試與 seed 不能自動回退到日常資料庫。
- `.env.example` 提供 POSTGRES_USER、POSTGRES_PASSWORD、POSTGRES_DB、DATABASE_URL、TEST_DATABASE_URL、OPENAI_API_KEY、OPENAI_MODEL 與選用 OPENAI_BASE_URL。`OPENAI_MODEL` 範例預設 gpt-6-luna。
- 容器內資料庫主機為 db，測試為 db_test。`.env` 經 Compose env_file 傳入 app，credentials 只留本機，建置 context 排除 `.env` 與私有執行資料。
- Dockerfile 內建立 Python 環境，host 可用 uv 產生／更新 lockfile。一般使用入口為 Compose。

### 首次啟動及資料庫

```bash
cp -n .env.example .env
docker compose build app
docker compose up -d --wait db
docker compose run --rm app --init-db
docker compose run --rm app --db-info
docker compose run --rm app
```

使用者先在本機設定 `.env`。`--init-db` 執行版本化 migrations，重複執行不改變既有商業資料。一般啟動只檢查 schema 與連線，缺 migration 時提供執行入口。`--db-info` 顯示不含密碼的資料庫識別、schema version 與表筆數。

```bash
docker compose run --rm app --model gpt-6-luna
docker compose run --rm app --seed demo_data/scenario.json --scripted
docker compose --profile test up -d --wait db_test
docker compose --profile test run --rm --no-deps --entrypoint uv app run --locked python -m pytest tests/ -q
docker compose down
docker compose up -d --wait db
```

Seed 先確認目標 schema 的商業資料為空，整筆匯入放在單一交易，非空即拒絕。範例 scripted 命令僅適用空的示範環境，重跑示範以不同 Compose project 與獨立 volume 執行，例如 `docker compose -p nutrition-demo-check ...`。一般 down 不加刪除 volume 的參數。

測試以 TEST_DATABASE_URL 連線 db_test，fixture 強制檢查測試目標，對每個需要資料庫的 case 建立唯一 schema、載入相同 migrations，finally 清理該 schema。所有測試查詢使用一致 search_path，查表時限定該 schema。測試 profile 的 app 透過 --no-deps 避免連帶啟動日常 db。

備份文件提供以 pg_dump 輸出指定檔案及在獨立示範環境用 pg_restore 還原的操作，驗收時核對設定、庫存、批次與事件筆數。更換 PostgreSQL major version 需獨立升級流程。

### 模型與執行上限

採 Responses API，支援查詢、提出方案、計算與一般食用工具。確認／拒絕由應用程式接收並綁定具體 preview，模型或工具文字不能自行核准。離線初始化、seed、scripted 及假模型測試可在沒有 OpenAI key 時執行。

模型依 CLI、環境、預設的優先順序決定。gpt-6-luna 的初始 reasoning effort 建議 medium，切換模型時檢查該模型接受的參數。正式評估凍結確切模型 ID、SDK、參數與工具版本。模型無權限或不相容時回報明確錯誤，由使用者選擇另一個設定。

技術初始值建議為每次客製化最多三個提案／驗算輪次，每回合最多 12 次模型呼叫、24 次工具呼叫及三輪澄清。這些為助理選定的開發預設，由 development cases 試跑後定稿，正式比較時所有 controller 一致。等待使用者不持有資料庫交易。

## 資料模型與操作一致性

- `schema_migrations` 保存已套用 migration 與 checksum。
- `profile` 保存單人設定、當地時區、每餐與每日目標、廚具及餐盒容量。缺每日目標時詢問，不將每餐目標自行乘三。
- `inventory` 保存食材、單位、生熟狀態、數量、營養來源與價格基準，數量非負。
- `cooking_runs` 保存一次已確認烹調、食譜版本、日期與 request_id；`cooking_ingredients` 保存該次實際總用量、來源及營養／成本快照。
- `batches` 連結 cooking_run，每種組成一批，保存名稱、整數盒數、組成、盒內營養與成本快照。`batch_ingredients` 保存該批的食材分配，作為營養與成本計算依據。
- `batch_addons` 保存批次確認過的加餐與每餐用量、版本。`events` 保存批次、當地日期、餐別、一盒，以及實際吃下的盒內與加餐營養快照。
- `inventory_movements` 將食材增減連結到 cooking_run、食用事件或明確校正。`previews` 保存操作內容、版本、狀態及確認時間。`operations` 保存唯一 request_id、輸入摘要及結果。`workflow_sessions` 保存階段與待澄清內容。
- `state_meta` 保存單人狀態版本。寫交易先鎖定該列，再查 operations。已完成的相同 request_id 同輸入先回傳原結果，不重新驗證已完成 preview 的版本；同 ID 不同輸入拒絕。只有新操作才驗證 preview 與庫存，再一起提交異動及新版本。
- 數值用 PostgreSQL NUMERIC 與 Python Decimal，日期用 DATE，時間用 TIMESTAMPTZ，來源與快照結構可用 JSONB。所有庫存、盒數、數值有限性與外鍵由程式及資料庫約束共同檢查。
- 所有已確認寫入透過共用服務與參數化 SQL。交易失敗回復全部變更，連線中斷而結果不明時以同一 request_id 查詢／重試。

同次烹調的成品分配必須能核對總食材、營養與成本。每筆分配包含 cooking_ingredient_id、quantity、unit，quantity 代表該成品批次的總量。同一批對同一原料只保留一筆，跨批可合法分配。同一原料所有成品分配量加上已確認剩料／耗損，必須等於本次實際用量，並使用相同或已驗證可換算的單位。超額、少分、重複項與單位不符皆需修正後才能確認。每批只使用獲分配的份量計算營養與成本，剩料或耗損另列於 cooking_run 並清楚標估算。庫存消耗以 cooking_run 的總用量為準，多批輸出共用這筆消耗。

同一批次的加餐方案日後改變時，新事件採當時確認的方案，既有事件保留原快照。更正既有事件時，先使用原快照算恢復量，再套用本次確認的批次與加餐。只改日期不改盒數與總食材消耗。

## 共用介面

以下為規劃介面，dataclass 的欄位與 JSON schema 需一致。所有 ID 為字串，金額以 USD 記錄。

- `Nutrients(kcal: Decimal, protein_g: Decimal, carbs_g: Decimal, fat_g: Decimal)`。
- `IngredientAllocation(cooking_ingredient_id: str, quantity: Decimal, unit: str)`；`BatchOutput(name: str, boxes: int, allocations: list[IngredientAllocation])`。confirmed_dispositions 以相同原料、數量與單位另列 remaining／loss 類型，與各批分配共同通過守恆驗證。
- `Result(ok: bool, data: dict, error: str | None)`；`Preview(id: str, kind: str, state_version: int, changes: list[dict], summary: str)`。
- `Store(dsn: str, schema: str = "public")`，`migrate() -> None`、`info() -> dict`、`transaction()`、`close() -> None`。
- `NutritionService(store: Store, catalog: Catalog, timezone: str, clock: Callable)`，公開操作皆回傳 Result。
- `get_profile()`、`set_profile(values: dict)`、`list_inventory()`。
- `preview_inventory_change(items: list[dict], mode: str)`，mode 為 purchase 或 reconcile。
- `preview_preparation(recipe_id: str, actual_usage: list[dict], outputs: list[BatchOutput], prepared_on: str, confirmed_dispositions: list[dict] | None = None)`。disposition 缺省為空清單，所有實際用量需完全分配。
- `preview_batch_addons(batch_id: str, items: list[dict])`、`confirm_preview(preview_id: str, request_id: str)`、`reject_preview(preview_id: str)`。
- `find_batches(query: str)`、`find_events(query: dict)`、`log_meal(batch_id: str, eaten_on: str, meal: str | None, request_id: str, addon_override: list[dict] | None = None)`。None 沿用確認加餐，空 list 代表本餐不加餐。
- `preview_correction(event_id: str, changes: dict)`，changes 支援 date、meal、batch_id、addon_override。庫存校正與待記食用可經 `preview_reconciled_meal(items: list[dict], meal_input: dict)` 合併確認及提交。
- `daily_summary(day: str)`、`batch_summary()`。每日 summary 為已記錄備餐攝取，列盒內與實際加餐，並比較個人目標。
- `Workflow(service: NutritionService)` 保存每個 session 的階段；`DemoAgent(service, workflow, client, settings)` 的 `handle(message: str) -> Result` 使用同一組工具。

## Task 0 — Docker、Python 與資料庫服務

**Files** — Dockerfile、compose.yaml、.dockerignore、pyproject.toml、uv.lock、.python-version、.env.example、README.md。

**Interfaces** — app ENTRYPOINT 及 DATABASE_URL／TEST_DATABASE_URL；db 健康後可接受連線。此任務完成時先用 --entrypoint 覆寫檢查環境。

- [x] 檢查 Git 狀態、repository instructions、docker version、docker compose version 與 Docker engine。若 CLI 或 engine 缺失，診斷實際安裝狀況後處理可恢復設定；需要使用者安裝／啟動時給出明確步驟。
- [x] 建立鎖定依賴與容器定義。首次以可用 uv 產生 lockfile，Docker build 使用 uv sync --locked，記錄映像 digest 與實際 Python／套件版本。
- [x] 驗證 Compose config、db healthcheck、app 的 openai／psycopg／pytest 匯入與 Python 3.12。使用覆寫入口驗證 DATABASE_URL 可連線且 SELECT 1 成功。
- [x] 啟動 db_test 並檢查測試資料獨立性。驗證 secrets 與個人資料排除於 build context 及 Git。
- [x] 檢查差異後提交環境設定，Task 1 接著建立 schema 與正式 CLI。

## Task 1 — PostgreSQL schema、交易與重開

**Files** — models.py、store.py、migrations/001_initial.sql、__init__.py、__main__.py、tests/conftest.py、tests/test_demo_store.py。

**Interfaces** — Store、共用型別、--init-db、--db-info、--seed 與 CLI 離線分支。

- [x] 加入 test_profile_survives_reopen、test_migrations_repeat_safely、test_unknown_schema_version、test_foreign_keys、test_seed_rejects_nonempty 與 test_seed_failure_rolls_back。固定檢查目標 schema 的設定、來源及筆數。
- [x] 透過 Compose 測試入口執行測試，確認尚未提供介面而失敗。
- [x] 實作上述 PostgreSQL 表、約束、migration runner、單人狀態列鎖與 request_id 去重。設定 schema 的識別字使用 psycopg.sql 安全組合，查詢限制於該 schema。
- [x] 實作初始化、檢查、seed 與 CLI，讀寫 schema_migrations 在同一 migration 交易內。seed 對相同 schema 取得狀態鎖後才檢查是否為空。
- [x] 執行 tests/test_demo_store.py，核對重開與重複初始化保留資料，再提交本任務。

## Task 2 — 四道食譜、營養與客製化驗算

**Files** — nutrition.py、catalog.py、demo_data/catalog.json、demo_data/source_manifest.json、tests/test_demo_nutrition.py。

**Interfaces** — `scale_nutrients(value, used, reference) -> Nutrients`、`per_box(total, boxes) -> Nutrients`、`used_cost(price, used, package_quantity) -> Decimal`、`validate_targets(actual, targets) -> dict`；Catalog.load、recommend、suggest_additions。

- [x] 建立合成數字測試，整批 3600 kcal、240 g 蛋白質、390 g 碳水與 120 g 脂肪，八盒各為 450、30、48.75、15。12 USD／1000 g 用 250 g 成本為 3 USD。
- [x] 測試含邊界的容差。假設目標 600／40／65／20，通過範圍為 570–630／40–44／58.5–71.5／18–22。任一超出即未達標，計算以 Decimal 完整值判斷，顯示時才四捨五入。
- [x] 加入缺營養欄位、零盒／負數／非有限值、生熟或單位不符、無密度資料 g↔ml 換算與未知成本測試，確認先失敗。
- [x] 由四份 PDF 抽取食譜與步驟，核對營養來源、價格與份量版本，將已核對／估算／缺漏明確標示。來源 manifest 包含原路徑、hash、頁碼、品牌或 USDA ID。
- [x] 實作候選料理、困難步驟、廚具／分批資訊、需買清單與成本估算；客製化提案驗算時回傳四項差距及替換影響，支援後續模型迭代。
- [x] 補充建議顯示盒內加加餐的整餐營養，檢查四項限制並保留未達標的差距。僅提供建議不新增攝取。
- [x] 執行 tests/test_demo_nutrition.py 通過，人工核對四份來源抽取與來源標示，再提交。

## Task 3 — 庫存、同次烹調多批成品與加餐方案

**Files** — service.py、store.py、tests/test_demo_preparation.py。

**Interfaces** — 個人設定、inventory previews、preview_preparation、preview_batch_addons、confirm_preview。

- [x] 測試日式咖哩的完整便當六盒與純咖哩一盒建立為兩批。實際食材只扣一遍，兩批的營養與成本按各自組成分配。
- [x] 測試 BBQ Mac & Cheese 的含菜五盒與無菜兩盒，分配總量對應 cooking_run。測試各原料成品分配與確認剩料／耗損的合計等於實際用量，超額、少分、同批重複原料與單位不符時拒絕。
- [x] 測試預覽不寫商業資料、拒絕保留原狀、庫存不足與中途插入失敗全部回復、重複 request_id 不重複消耗，以及兩個同時確認只有一個可使用原版本。
- [x] 執行測試確認失敗，實作 purchase／reconcile、單次烹調與多批建立的原子操作。保存每批營養來源與成本快照。
- [x] 實作加餐方案確認及版本保存，測試確認加餐方案不扣食材、不新增飲食紀錄。
- [x] 執行 tests/test_demo_preparation.py 通過，提交本任務。

## Task 4 — 一盒加餐的食用與查詢

**Files** — service.py、workflow.py、tests/test_demo_meals.py。

**Interfaces** — find_batches、log_meal、preview_reconciled_meal、daily_summary、batch_summary。

- [x] 測試一盒預設搭配一份優格時，盒數減一、優格庫存減一、日營養為兩者合計，保存實際組成。測試 addon_override 空 list 時只記盒內。
- [x] 測試方案之後改變不回寫原事件；重試不重複扣除，零盒拒絕，多個同名候選先澄清。
- [x] 測試加餐不足時回傳待釐清狀態，食用與庫存均尚未寫入；經確認的補採買／庫存校正與食用一起提交，中途失敗全部回復。
- [x] 執行測試確認失敗，實作食用交易與等待澄清狀態。固定 America/Los_Angeles 時區，clock 可注入以測試跨午夜的昨日解析。
- [x] 查詢顯示已記錄備餐的四項營養、目標差距、剩餘盒數、每盒及預設整餐營養。
- [x] 執行 tests/test_demo_meals.py 通過，提交。

## Task 5 — 日期、批次與加餐更正

**Files** — service.py、store.py、tests/test_demo_corrections.py。

**Interfaces** — find_events、preview_correction、reject_preview、confirm_preview。

- [x] 測試日期更正移動盒內加加餐的日營養，批次剩餘與食材總消耗相同，事件 ID 保持。
- [x] 測試更正批次恢復來源盒數並扣正確批次，預覽清楚列出將採用的餐點與加餐、營養及庫存差額；使用者確認後一起更新。
- [x] 測試本餐沒吃加餐的更正會恢復原扣除食材並減去對應營養，未知新搭配或不足庫存先釐清。
- [x] 加入拒絕、過期 preview、無權核准、重複確認、無變更、連線失敗後同 request_id 重試等測試。另測試已提交但回覆遺失、其他操作成功後，再重試原 request_id 仍回傳原成功結果，確認先失敗。
- [x] 實作狀態版本、應用程式確認與單交易更正。校正依事件快照計算，不用今天的方案回推歷史。
- [x] 執行 tests/test_demo_corrections.py 通過，提交。

## Task 6 — 主流程與階段內工具迴圈

**Files** — workflow.py、agent.py、__main__.py、tests/test_demo_agent.py。

**Interfaces** — Workflow、DemoAgent.handle、共用服務工具 schemas 與模型設定。

- [x] 假模型測試先選料理再客製化、用量／小幅替換、計算失敗重提、四項符合後請確認、達重試上限等待決定。
- [x] 測試保存階段進度與待澄清問題，重開可以查詢或接續；一般食用、查詢、更正直接路由至對應階段。
- [x] 測試 --model 優先、環境覆寫預設、實際模型與參數追蹤，以及不同模型不相容參數會明確報錯。
- [x] 加入未知工具、非法參數、超過呼叫上限、API 失敗、工具文字偽裝核准與未通過驗算就宣稱符合的回歸測試，先確認失敗。
- [x] 實作 Responses API loop 與可驗證的結果呈現。主流程及核准狀態由應用程式管理，完成訊息以成功工具結果為依據。
- [x] 對話可調整食譜與解釋基本步驟，使用選定配方、已知廚具與已核對資料。固定值與來源送入 context，評分答案由 evaluator 持有。
- [x] 執行 tests/test_demo_agent.py 通過，提交。

## Task 7 — 完整情境、持久化及備份驗證

**Files** — tests/test_demo_scenario.py、README.md、必要的合成情境。

- [x] 驗證六餐計畫、實際八盒、確認加餐、吃一餐、改日期、重開後仍剩七盒，原料與加餐扣除均正確。
- [x] 驗證四份食譜載入、咖哩兩批與 BBQ 兩批成品、不重複扣原料，以及 Nikujaga 歷史六份與七份方案的區別。
- [x] 在 db_test 執行全部 demo 測試，同一 fixture 與 clock 在兩個隔離 schema 產生相同語意結果。固定 tool trace 與資料查核方式。
- [x] 使用獨立 Compose project 執行 scripted，明確標示合成情境；再以真正 gpt-6-luna 對話跑一輪並記錄實際用量與結果。模型權限或憑證缺失時保留該項未驗證狀態。
- [x] down／up 後讀回相同資料，使用 pg_dump 備份並在獨立環境還原，核對 schema、設定、庫存、批次與事件。
- [x] 更新 README 的已完成項目與限制，檢查檔案差異後提交。

## Task 8 — 驗收與課程銜接

**Files** — README.md、本計畫的實際完成核取狀態。

- [ ] 從新 clone 的設定流程走一次啟動、初始化、seed、互動、查詢及重開，每個 V1 功能可對應至操作與通過的檢查。
- [x] 核對 Docker／PostgreSQL、預設可切換模型、四項容差、確認範圍、加餐、庫存差異、分開批次與一次扣原料等所有確認決定。
- [x] 凍結 demo 設定與工具 schema，記錄模型、SDK、映像、規格及資料版本，列實際完成與未驗證事項。
- [x] 交付第一版 Python demo 的證據，課程評估依下列里程碑另行完成。
## 課程交付的後續里程碑

產品第一版範圍與課程完整交付分別追蹤，講義要求見 `docs/course-requirements.md`。

1. 建立固定流程 baseline，與本 Agent 採相同工具、模型、資料、資源上限、使用者回覆與確認規則。固定流程由程式決定檢索及分支，Agent 可依觀察選擇階段內工具。實驗文件清楚列出比較方案；若需要額外 variant，另行定義其差異。
2. 使用共用 Store／Service／Tools 建立 eval runner 與獨立 checker。每題用隔離 schema、固定時鐘與 scripted 回答，課程 50 題含至少三個 edge cases 與兩個 unanswerable，完成指標、三次重跑及 failure analysis。
3. 擴充至少 200 題 benchmark 與至少 50 題安全測試，涵蓋來源注入、記憶污染、資料洩漏、危險／有害請求與 jailbreak，加入無害請求誤拒檢查。
4. 為同一服務核心加上雲端網頁，公開展示使用獨立示範資料、保留 follow-up context，符合 11/24 展示要求。
5. 準備實際架構圖、三分鐘預錄 demo、兩分鐘 Q&A，以及 12/8 code、web app、report。題數、期限與指標以 course-requirements 的原始來源對照為準。

## 技術預設、驗證邊界與來源

Isaac 已確認產品行為。下列為助理補齊的工程預設，可在 development cases 驗證後調整並留紀錄。

- Python 3.12、PostgreSQL 18、psycopg 3 與版本化 SQL migrations；依賴與映像於實際建置時鎖定。
- 單人狀態版本列鎖管理短寫交易，NUMERIC／Decimal 保存數值，JSONB 保存來源與快照。
- cooking_run 連結多個成品批次，配合單次原料扣除及營養分配。
- 每次客製化初始三輪、每回合 12 次模型／24 次工具／三輪澄清；模型初始 reasoning effort 為 medium。正式比較前用開發題定稿。
- 既有事件採歷史快照，日後方案修改適用後續事件。更正既有事件仍需明確預覽與確認。

計畫自我檢查涵蓋規格、型別、每個決定對應的任務與主要失敗情境。Task 0–7 與 Task 8 的設定凍結及範圍核對已完成；Task 8 尚待最後以新 clone 重走初始化與合成互動流程後勾選。課程評估工作另列里程碑追蹤。

- [PostgreSQL 官方 Docker image 與 PGDATA](https://hub.docker.com/_/postgres)
- [Compose 健康檢查與啟動順序](https://docs.docker.com/compose/how-tos/startup-order/)
- [uv Docker 指南](https://docs.astral.sh/uv/guides/integration/docker/)
- [psycopg 安裝](https://www.psycopg.org/psycopg3/docs/basic/install.html)
- [PostgreSQL 鎖定與交易](https://www.postgresql.org/docs/current/explicit-locking.html)
- [GPT-6 Luna 官方模型文件](https://developers.openai.com/api/docs/models/gpt-6-luna)
- [USDA 資料來源說明](https://fdc.nal.usda.gov/data-documentation/)
