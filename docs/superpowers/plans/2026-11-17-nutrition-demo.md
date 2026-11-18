# Nutrition Agent Python Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal** — 建立可保存資料、支援自然語言互動的備餐示範，從食譜選擇走到實際分裝、食用紀錄與日期／批次更正。

**Architecture** — 在新 repository `/Users/wolverine/Develop/nutrition-agent` 建立 `nutrition_demo`。單一助理使用驗證過的服務工具，本機 SQLite 保存設定、食材、批次與食用事件，程式計算營養、成本與剩餘盒數。互動 demo 與後續評估共用同一組服務與工具。互動使用檔案型資料庫，評估以相同 schema 載入各題獨立初始資料，兩者透過不同的使用者回覆入口取得澄清及核准。

**Tech Stack** — 建議專案使用 uv 管理 Python 3.12 與 `.venv`，使用標準函式庫 sqlite3／decimal／zoneinfo、模型 client 與 pytest。套件精確版本於環境建立時解析並寫入 `uv.lock`，模型名稱與 API 設定透過環境設定傳入。這是本計畫選定的技術基準，尚待實際建立與驗證。

**Spec** — `docs/specs/v1-python-demo-scope.md`。完整願景為 `docs/specs/full-product-scope.md`，課程對照為 `docs/course-requirements.md`，原始訪談保留於 canonical Obsidian vault。

## Global Constraints

- 第一版介面為 Python 互動式示範，資料可跨次使用保存。
- 每批預設六餐、同一道料理。一般食用預設一整盒。
- 先確認庫存。購入資訊確認後入庫，實際用量確認後扣除。
- 資訊明確的一般食用直接記錄，更正先預覽並確認，批次不明時先澄清。
- 固定營養與價格資料附來源，合成測試資料與估算清楚標示。
- 每日熱量、蛋白質、碳水與脂肪可與個人目標比較，顯示每批剩餘盒數及每盒營養。
- 容量是規劃參考，最終盒數由使用者確認。每盒營養採均分假設並顯示此假設。
- 第一版支援已確認範圍，後續功能依 scope 文件分期。
- 本計畫是實作建議，文件完成不代表程式已完成或測試通過。

## Review Focus

- 重開程式後資料與營養來源仍存在，對應 Task 1、2、8 的 persistence 檢查。
- 重試同一次操作不重複扣庫存或記錄食用，對應 Task 3、4 的 request_id 測試。相同文字的新操作不能直接視為重試。
- 更正日期維持剩餘盒數，更正批次恢復來源並扣除目的批次，對應 Task 5 的狀態檢查。
- 拒絕、過期確認及部分失敗不能留下半筆操作，對應 Task 3、5 的 rollback 與 stale-preview 檢查。
- 缺碳水／脂肪、單位不明與生熟資料不符不能被當成零或靜默換算，對應 Task 2 的資料驗證。

## 現況與工作區

Isaac 於 2026-11-17 明確選定新 repo `/Users/wolverine/Develop/nutrition-agent`。隊友的 `/Users/wolverine/Develop/meal-log-agent` 依舊規格實作，其提案、程式與結果保留原有脈絡。舊實作可作為設計討論的參考，本 repo 從本次已確認需求建立新介面與資料。

- 新 repo 初始包含需求快照、實作計畫與課程要求對照，產品程式尚待實作。
- 數據、驗證、更正與交易集中在共用服務。互動 Agent、固定流程 baseline 與測試使用相同公開工具契約。
- 工具呼叫追蹤可加入共用呼叫入口，記錄工具參數、結果、模型呼叫、tokens 與時間。使用者確認由應用程式接收。
- 互動使用持久化資料庫。評估時每題建立隔離資料庫、設定固定時鐘並注入 scripted 使用者回覆。
- 同一輪 controller 比較必須採相同模型、工具、初始資料、核准規則與資源上限，並記錄版本。
- 新 repo 的一般食用可直接記錄、更正前核准，依本次確認需求執行。

## 預計新增檔案

| 檔案 | 責任 |
|---|---|
| `nutrition_demo/__init__.py` | Python package |
| `nutrition_demo/models.py` | Nutrients、Result、Preview 與輸入型別 |
| `nutrition_demo/store.py` | SQLite schema、交易、版本與操作去重 |
| `nutrition_demo/nutrition.py` | 四項營養、份量與成本換算 |
| `nutrition_demo/catalog.py` | 固定食材／食譜資料驗證、建議與補充食物選項 |
| `nutrition_demo/service.py` | 設定、庫存、完成備餐、食用、更正與查詢 |
| `nutrition_demo/agent.py` | 自然語言互動與受限工具介面 |
| `nutrition_demo/__main__.py` | 互動 CLI、確認輸入、資料庫與模型選項 |
| `demo_data/catalog.json` | 少量附來源的食材、食譜與補充食物資料 |
| `demo_data/scenario.json` | 明確標示為合成的可重跑測試情境 |
| `tests/test_demo_*.py` | 各階段的狀態與互動回歸測試 |
| `pyproject.toml`、`uv.lock`、`.python-version` | 專案依賴、鎖定版本與 Python 選擇 |
| `.env.example`、`README.md` | 設定欄位範例、環境與資料庫操作說明 |

執行入口規劃為 `uv run python -m nutrition_demo --db data/demo.sqlite3`。`--seed demo_data/scenario.json` 僅載入尚無商業資料的資料庫。已有個人設定、庫存、批次或事件時明確拒絕 seed，重新示範採另一個檔案。`--scripted` 提供可重跑的工具流程驗證，明確標示為 scripted。一般模式採真正模型工具互動。

## 資料與共用介面

以下均為規劃中的介面，數值使用 Decimal，金額以 USD 保存，顯示時才四捨五入。

- `Nutrients(kcal: Decimal, protein_g: Decimal, carbs_g: Decimal, fat_g: Decimal)`，四項都要明確提供。
- `Result(ok: bool, data: dict, error: str | None)`，失敗結果回到互動層，不中斷整段 session。
- `Preview(id: str, kind: str, state_version: int, changes: list[dict], summary: str)`，確認必須綁定具體預覽與版本。
- `Store(path: Path)`，`initialize() -> None`、`close() -> None`、`transaction()` 以單一 SQLite transaction 管理一個操作。
- `NutritionService(store: Store, catalog: Catalog, timezone: str)`，所有寫入透過此服務。
- `request_id` 代表應用程式的一次操作，重試沿用原 ID。再次輸入相同文字有新的 ID。

資料表包含 profile、inventory、batches、batch_ingredients、events、previews、operations 與 state_meta。`events` 保存 date、meal、batch_id、boxes 與食用時的每盒營養快照。剩餘盒數由批次成品盒數減事件盒數推導，每日營養由事件推導。每批保存成品營養、實際用量、成本、來源與估算標示。profile 分別保存每餐與每日目標，缺少任一目標時詢問使用者，不推測每日目標等於每餐乘三。

## 環境與資料庫設定的驗收基準

2026-11-17 已確認本機可使用 uv 0.13.6，系統 `python3` 為 3.9.6。以下為實作階段要執行的步驟，目前尚未建立專案 `.venv`、依賴或資料庫。所有命令從 `/Users/wolverine/Develop/nutrition-agent` 執行。

### 環境初始化

首次建立環境採以下順序，Task 0 完成後才執行產品程式。`uv init` 僅在尚無 `pyproject.toml` 時執行。

```bash
cd /Users/wolverine/Develop/nutrition-agent
uv python install 3.12
uv init --bare --no-package --no-workspace --python 3.12 --name nutrition-agent
uv python pin 3.12
uv add openai
uv add --dev pytest
uv sync --locked
uv run python --version
uv run python -c 'import sqlite3, openai, pytest; print(sqlite3.sqlite_version)'
```

預期 Python 為 3.12.x，三個模組均可匯入，輸出 SQLite 版本。建立的 `pyproject.toml`、`uv.lock` 與 `.python-version` 納入版本控制，`.venv/` 由 `.gitignore` 排除。日後其他電腦取得 repo 後，使用 `uv sync --locked` 重建環境，依 `.python-version` 選擇 Python。

本機環境不需要手動啟用 `.venv`，啟動與測試統一使用 `uv run`。首次建立時記錄實際 Python、uv 與模型 client 版本，後續執行保留 lockfile。

### 模型設定與離線操作

Task 0 建立 `.env.example`，包含 `OPENAI_API_KEY=` 與 `OPENAI_MODEL=`。使用者複製成 `.env` 後自行填入可使用的 key 與模型 ID。若課程提供相容服務，也可選填 `OPENAI_BASE_URL`。模型名稱於確認權限後設定，實驗時記錄確切模型與解碼參數。

```bash
cp .env.example .env
```

一般對話入口使用 `uv run --env-file .env python -m nutrition_demo --db data/demo.sqlite3`。CLI 在初始化真正模型 client 前檢查 key 與模型，缺資料時提供設定指引。設定值不輸出至紀錄。

初始化資料庫、查詢資料庫資訊、scripted 示範與本機單元測試可獨立於模型憑證執行。`.env` 與本機資料庫依目前 ignore 規則排除於 Git。

### 資料庫建立與重開

SQLite 資料庫由 Python 的 sqlite3 模組操作。Task 1 實作以下 CLI 選項，這些命令在 Task 1 完成前屬於規劃中的入口。

```bash
uv run python -m nutrition_demo --db data/demo.sqlite3 --init-db
uv run python -m nutrition_demo --db data/demo.sqlite3 --db-info
uv run python -m nutrition_demo --db data/demo.sqlite3 --seed demo_data/scenario.json --scripted
uv run --env-file .env python -m nutrition_demo --db data/demo.sqlite3
```

- `--init-db` 建立父目錄、資料庫與 schema version 1，完成後退出。重複執行只檢查版本並保留既有資料。
- `--db-info` 採唯讀連線，顯示資料庫絕對路徑、schema version 與各表筆數。不存在時報錯，不建立空檔案。
- `--seed` 在單一交易驗證並載入固定初始資料，失敗時回復。已有商業資料時拒絕，避免重複匯入。
- 一般啟動呼叫相同 `Store.initialize()`，新資料庫自動建立。既有版本 1 直接讀取，較新或未知版本顯示明確錯誤，等待相容處理。
- 重新示範指定新的資料庫路徑，例如 `data/demo-second.sqlite3`。日常使用固定同一個路徑。
- schema 結構與 seed 檔納入版本控制，實際使用者資料留在本機。

### 表格與資料完整性

| 表 | 最小資料內容與約束 |
|---|---|
| `profile` | 單一使用者設定、時區、每餐與每日四項目標、鍋具與餐盒資料。 |
| `inventory` | 食材 ID、剩餘數量、單位、生熟狀態、營養基準、來源與估算標示、價格與計價基準。 |
| `batches` | 批次 ID、食譜 ID、名稱、製作日期、實際整數盒數、整批與每盒營養快照、成本與來源。 |
| `batch_ingredients` | 批次與食材外鍵、實際用量及營養／成本來源快照。 |
| `events` | 事件 ID、批次外鍵、當地食用日期、餐別、一整盒及食用營養快照。 |
| `previews` | 預覽 ID、類型、狀態版本、完整變更、狀態及確認時間。 |
| `operations` | 唯一 request_id、輸入摘要、結果、確認／預覽關聯、前後變更與時間。相同 ID 搭配不同輸入時拒絕。 |
| `state_meta` | 單一狀態版本，用於檢查預覽是否過期。schema version 使用 `PRAGMA user_version`。 |

每個資料庫連線在交易開始前啟用並確認 `PRAGMA foreign_keys = ON`，外鍵關聯採限制刪除。事件按日期、批次建立查詢索引。Decimal 使用精確字串保存，服務層驗證單位、非負值、有限值及盒數有效性。

單次庫存更新、完成備餐或更正採明確交易邊界，成功一起提交，失敗一起回復。確認檢查、版本檢查、操作去重與寫入位於同一交易。交易方式統一由 Store 管理，使用 `sqlite3.connect(path, isolation_level=None)` 並明確執行 BEGIN IMMEDIATE／COMMIT／ROLLBACK。schema 初始化逐條執行 SQL，與設定 schema version 保持同一交易。資料庫忙碌或遭鎖定時回報可重試錯誤，重試沿用相同 request_id。

### 設定來源

- [uv 專案建立](https://docs.astral.sh/uv/concepts/projects/init/)
- [uv lock 與 sync](https://docs.astral.sh/uv/concepts/projects/sync/)
- [Python 3.12 sqlite3](https://docs.python.org/3.12/library/sqlite3.html)
- [SQLite 外鍵設定](https://www.sqlite.org/foreignkeys.html)

## Task 0 — 建立可重現的 Python 環境

**Files** — `pyproject.toml`、`uv.lock`、`.python-version`、`.env.example`、`README.md`，必要時調整 `.gitignore`。

**Interfaces** — 後續任務使用 `uv run python`，測試使用 `uv run python -m pytest`。CLI 接收 OPENAI_API_KEY、OPENAI_MODEL 及選用的 OPENAI_BASE_URL。

- [ ] 確認 repository instructions 與 Git 狀態，按照環境初始化節建立 Python 3.12 與依賴。
- [ ] 建立 `.env.example` 及 README 設定說明。所有實際 credentials 由使用者在本機提供。
- [ ] 執行上述版本與匯入檢查，確認 `.venv` 位於本 repo，保留實際結果。
- [ ] 執行 `uv sync --locked` 確認 lockfile 可重建環境，檢查 `.venv`、`.env` 與資料庫 ignore 規則。
- [ ] 將環境設定與操作文件作為獨立 commit，接著執行 Task 1。

## Task 1 — 持久化資料與可重開的入口

**Files** — `models.py`、`store.py`、`__main__.py`、`__init__.py`、`tests/test_demo_store.py`。

**Interfaces** — 產出共用資料型別、Store 及 `uv run python -m nutrition_demo` 入口。

- [ ] 確認 Task 0 的環境與依賴檢查已通過，從環境與資料庫設定節實作 Store 和 CLI 的初始化契約。
- [ ] 加入 `test_profile_survives_reopen`，寫入目標後關閉再開啟資料庫，四項目標與廚具資料完全相同。加入 seed 遇非空庫會拒絕、重複初始化保留資料、唯讀 db-info 不建立新檔、未知 schema version 拒絕、外鍵有效與 seed 失敗回復的測試。
- [ ] 執行 `uv run python -m pytest tests/test_demo_store.py -q`，確認因尚未提供介面而失敗。
- [ ] 依資料庫設定節實作八張表、schema version、外鍵、索引、交易、--init-db、--db-info 與 seed 邏輯。離線入口可在未提供模型憑證時執行。
- [ ] 重跑該測試，再以兩次啟動確認同一檔案可讀取設定。檢查差異後將本任務檔案作為獨立 commit。

## Task 2 — 營養、成本與固定食譜資料

**Files** — `nutrition.py`、`catalog.py`、`demo_data/catalog.json`、`demo_data/scenario.json`、`tests/test_demo_nutrition.py`。

**Interfaces** — `scale_nutrients(value: Nutrients, used: Decimal, reference: Decimal) -> Nutrients`、`per_box(total: Nutrients, boxes: int) -> Nutrients`、`used_cost(package_price: Decimal, used: Decimal, package_quantity: Decimal) -> Decimal`。`Catalog.load(path: Path) -> Catalog`、`recommend(inventory: list[dict], profile: dict, meals: int = 6) -> list[dict]`、`suggest_additions(actual: Nutrients, target: Nutrients) -> list[dict]`。

- [ ] 寫入已知數字測試。合成整批營養為 3600 kcal、240 g 蛋白質、390 g 碳水與 120 g 脂肪，八盒結果為 450、30、48.75、15。12 USD／1000 g 用 250 g 的成本為 3 USD。
- [ ] 加入零盒／負數／非有限值、缺任一營養欄位、生熟狀態不符與無密度資料的 g／ml 轉換拒絕測試。執行測試確認失敗。
- [ ] 實作計算與驗證。資料保存基準重量、生熟狀態、來源、來源日期、估算標示與價格基準。合成情境和真實來源資料分別標示。
- [ ] 準備少量食譜，包含用量、完整步驟、困難操作、鍋具條件與分批方式。候選比較顯示現有／需買食材、營養差距與成本，使用者選定後才形成備餐計畫。產生需買數量清單，固定資料有可核對的商品連結時一併提供，標示查核日期。
- [ ] 補充食物建議列出對四項目標的影響。無法兼顧時說明差距，不能宣稱精確達標。建議本身不計入已食用營養。
- [ ] 執行 `uv run python -m pytest tests/test_demo_nutrition.py -q` 通過，核對來源與數字後提交本任務。

## Task 3 — 庫存與完成備餐的確認交易

**Files** — `service.py`、`store.py`、`tests/test_demo_preparation.py`。

**Interfaces** — `get_profile() -> Result`、`set_profile(values: dict) -> Result`、`list_inventory() -> Result`、`preview_inventory_change(items: list[dict], mode: str) -> Result`、`preview_preparation(recipe_id: str, actual_usage: list[dict], boxes: int, prepared_on: str) -> Result`、`confirm_preview(preview_id: str, request_id: str) -> Result`。mode 為 `purchase` 或 `reconcile`。

- [ ] 寫入測試，預覽不寫商業資料，拒絕不更新。確認後一次扣除實際用量並建立八盒批次。相同 request_id 重試只生效一次。
- [ ] 加入庫存不足拒絕與插入批次失敗時庫存回復的測試，執行確認失敗。
- [ ] 實作 profile／庫存讀寫、文字購入資訊確認、庫存校正及完成備餐交易。新增購入使用已確認價格，成本資料不齊時顯示未完整估算。
- [ ] 以一次交易保存用量、營養／成本快照與盒數。回傳資料包含每盒營養、均分假設及補充建議。
- [ ] 執行 `uv run python -m pytest tests/test_demo_preparation.py -q`，通過後提交本任務。

## Task 4 — 整盒食用與每日／批次查詢

**Files** — `service.py`、`tests/test_demo_meals.py`。

**Interfaces** — `find_batches(query: str) -> Result`、`log_meal(batch_id: str, eaten_on: str, meal: str | None, request_id: str) -> Result`、`daily_summary(day: str) -> Result`、`batch_summary() -> Result`。

- [ ] 寫入八盒中吃一盒的測試，剩七盒，該日加入 450 kcal、30 g 蛋白質、48.75 g 碳水、15 g 脂肪。加入零庫存拒絕及同一 request_id 重試不重複的測試。
- [ ] 執行測試確認失敗，再實作直接記錄一盒與查詢。日期由 America/Los_Angeles 的明確時鐘解析。
- [ ] 加入「昨日」跨午夜解析與兩批同名需回傳候選的測試。單靠相同文字或份量不能自行合併事件。
- [ ] 查詢標為已記錄備餐營養，顯示四項每日目標差距與各批剩餘盒數；此版可查詢的攝取來自已支援的備餐紀錄。
- [ ] 執行 `uv run python -m pytest tests/test_demo_meals.py -q`，通過後提交本任務。

## Task 5 — 更正預覽、核准與一致性

**Files** — `service.py`、`store.py`、`tests/test_demo_corrections.py`。

**Interfaces** — `find_events(query: dict) -> Result`、`preview_correction(event_id: str, changes: dict) -> Result`、`reject_preview(preview_id: str) -> Result`。確認沿用 Task 3 的 `confirm_preview`。本版 changes 限 date、meal、batch_id。

- [ ] 寫入日期更正測試，今天的一盒移到昨天後，今天扣除相同營養、昨天加入、批次仍剩七盒，事件 ID 保持相同。
- [ ] 加入批次更正測試，來源批次恢復一盒、目的批次扣一盒，當日營養切換為目的批次值。目的無剩餘盒時拒絕並保持全部原狀。
- [ ] 加入拒絕、過期預覽、核准 ID 不相符、重複確認以及原紀錄已正確的測試。無變更時直接說明，無需核准。
- [ ] 執行測試確認失敗，實作版本檢查、由應用程式接收的確認及原子更正。更新事件營養快照與記錄異動。
- [ ] 執行 `uv run python -m pytest tests/test_demo_corrections.py -q`，通過後提交本任務。

## Task 6 — 自然語言助理與確認互動

**Files** — `agent.py`、`__main__.py`、`tests/test_demo_agent.py`。

**Interfaces** — `DemoAgent(service: NutritionService, client: object, model: str, max_tool_calls: int = 24)`、`handle(message: str) -> Result`。CLI 將明確的確認／拒絕輸入送至服務層，模型工具集包含查詢與建立預覽，核准動作由應用程式處理。

- [ ] 以假模型回覆測試工具選擇與觀察回傳。涵蓋讀取設定、食譜選擇、完成備餐、食用、歧義澄清與更正。
- [ ] 加入模型提供非法參數、呼叫未知工具、達工具上限、API 失敗與將工具文字當成核准的測試，確認無未核准寫入且 session 可恢復。
- [ ] 實作工具 loop，context 僅包含個人資料、catalog 與服務查詢結果。API 失敗不切換成偽造成功，scripted 模式明確顯示用途。
- [ ] 啟動時沿用目標，規劃時列出庫存待確認，候選說明難點與成本。基本烹調問答以選定食譜與廚具為依據。
- [ ] 資訊明確的食用直接執行。缺失批次、日期或事件身分會改變結果時先詢問。所有完成回覆依工具成功結果產生。
- [ ] 執行 `uv run python -m pytest tests/test_demo_agent.py -q`，通過後提交本任務。

## Task 7 — 代表情境與共用工具驗證

**Files** — `tests/test_demo_scenario.py`、`README.md`，必要時新增 `demo_data` 中的具來源說明資料。

**Interfaces** — 沿用 Tasks 1–6 的公開服務及 CLI。此任務不新增第二套商業邏輯。

- [ ] 建立六餐計畫、實際八盒、吃一盒、日期更正、重新開啟仍有七盒的端到端情境。再驗證兩批同名澄清與改批次。
- [ ] 執行 `uv run python -m pytest tests/test_demo_*.py -q`，確認持久化、庫存、四項營養、成本、核准與更正的關鍵斷言。
- [ ] 在獨立示範資料庫執行 `uv run python -m nutrition_demo --db /tmp/nutrition-demo-check.sqlite3 --seed demo_data/scenario.json --scripted`，確認輸出與已知結果一致。
- [ ] 用同一服務建立兩個獨立測試資料庫，載入相同 fixture 與固定時鐘，確認同一操作序列產生相同語意狀態。互動與後續評估都使用這組操作入口。
- [ ] 以已設定的模型做一次自然語言 smoke test，確認真正工具互動可完成情境，記錄模型設定、工具步數與結果。若缺 API 憑證，明確保留此項未驗證狀態。
- [ ] README 寫明啟動、設定、重開、重跑及來源／估算標示。確認 `.gitignore` 涵蓋本機資料庫與 credentials，檢查差異後提交本任務。

## Task 8 — 交付驗收與後續課程評估銜接

**Files** — 更新 `README.md` 中的示範驗收紀錄，視需要回填計畫核取方塊。

- [ ] 從新的空資料庫走一次正常入口，確認每個 V1 範圍項目都能對應到實際操作及已通過的檢查。
- [ ] 關閉後重新啟動，確認目標、庫存、批次、食用紀錄與來源均保留。
- [ ] 檢查正式模型與 scripted 模式的標示，以及未食用的補充建議不會增加已攝取總量。
- [ ] 記錄實際已完成、尚未完成與限制。課程的 50 題、controller 比較、重跑與 failure analysis 另依作業要求驗證。
- [ ] 記錄新 repo 的規格與核准規則版本，後續評估以該版本建立題目與 checker。舊 repo 的結果僅對應其原始系統。

## 課程交付的後續里程碑

以下根據老師講義列出課程交付所需的工作，不自動改變已確認的 Python V1 產品範圍。V1 能完成後，仍需完成下列項目，詳見 `docs/course-requirements.md`。

1. 建立新 repo 的 non-agentic baseline，與 Agent 共用工具、資料與規則。另明確定義至少兩種實驗方案。是否將 baseline 計入兩方案或另加 Agent variant，在實驗設計時明列。
2. 使用共用服務建立可重設的 eval runner 與獨立 checker。Week 6 需 50 題、其中至少三題 edge cases 與兩題 unanswerable，完成三次 Agent 重跑、指標與 failure analysis。
3. 擴充至至少 200 題 benchmark 與至少 50 題獨立 safety prompts，含 harmless prompts 的誤拒檢查。依實際能力與規則建題，題目與結果記錄版本。
4. 為共用服務增加雲端互動網頁入口，提供公開 URL 並保留 follow-up context。Python V1 的服務與工具由網頁重用。
5. 準備架構圖、三分鐘預錄 demo、兩分鐘現場 Q&A，以及最終 code、web app、report。

## 方案選擇與自我檢查

Isaac 已選定獨立 repo，基礎程式依新規格建立。相較於直接擴充隊友的舊程式，此選擇讓產品需求、測試規則與工作責任具有清楚起點。共同核心供互動與評估使用，避免出現兩套更正邏輯。

環境建立對應 Task 0，覆蓋檢查已對應每個 V1 功能至 Tasks 1–7，交付檢查於 Task 8。資料型別與服務名稱以前述介面為準。課程額外交付列為後續里程碑，完成 V1 不能直接宣稱滿足全部課程要求。

此次建立新 repo 並修訂文件。程式實作尚待執行，實際模型、依賴與測試結果於實作時驗證。
