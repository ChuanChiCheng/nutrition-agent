# Nutrition Agent

Isaac 的單人備餐助理，第一版為 Python 互動介面，最終介面為 iOS App。

已實作可持久保存的資料與交易核心、四道來源食譜、精確營養驗算、同次烹調多批分配、加餐與食用、更正預覽，以及 Responses API 工具流程。離線測試、合成完整情境、真實模型合成流程、容器重開及獨立備份還原均有實際驗證。這些驗收使用合成資料，不代表個人目標或真實料理營養已核實。

## 首次啟動

需要 Docker Desktop 已啟動。在 repo 根目錄執行：

```bash
cp -n .env.example .env
docker compose build app
docker compose up -d --wait db
docker compose run --rm app --init-db
docker compose run --rm app --db-info
docker compose run --rm app
```

`.env` 只保留本機。將自己的 key 填在 `OPENAI_API_KEY=` 後，不要貼到聊天、提交 Git 或放入食譜。未設定 key 時仍可初始化、查詢、跑測試與 scripted 情境。預設資料庫密碼只適合這個本機開發環境；修改時同步更新對應 DSN。現有 volume 的密碼須另外透過資料庫修改，不能只改 `.env`。

一般啟動會檢查 migrations，不會自動清空或重建資料。更新後如提示 schema 尚未初始化或有新 migration，執行 `--init-db`。未知版本或 checksum 改變會拒絕啟動。

## 實際對話

第一次請分別提供每餐與每日四項營養目標、時區、廚具與餐盒容量。程式不會自行把每餐目標乘三。可用自然語言描述購入、想吃的料理、實際烹調結果、食用及更正。

1. 輸入 `/new-plan`，檢查庫存；確認後輸入 `/inventory-ok`。
2. 選料理，例如 `/select curry`；也支援 `nikujaga`、`bbq`、`rice_pot`。預設六餐、同一道料理。
3. 用自然語言要求客製化。模型提案後由程式驗算，最多三輪；核對食材、成本與四項差距。
4. 輸入 `/accept-recipe <proposal-id>` 確認整份配方。未達全部目標時必須明確加上 `outside`，仍保留未達標狀態。
5. 做完後描述實際用量、各種組成的盒數及原料分配。確認具體預覽才扣除一次總原料並建立各批。剩料／耗損需明確列出，分配總量必須守恆。
6. 加餐方案確認後保存，食用時才扣原料；明確表示已食用才記一盒＋預設加餐。查詢、假設或要求不要記錄的訊息不會扣料；不足或批次歧義會要求澄清。
7. 更正先顯示原事件與差額，再輸入 `/confirm <preview-id>`；拒絕用 `/reject <preview-id>`。
8. 重開後輸入 `/preview` 重看尚待確認的變更。若食用操作已提交但模型回覆中斷，重送原訊息會取回結果一次；`/retry` 也可取回。一般成功後再次描述同一句會視為另一餐。

可直接 `/inventory`、`/batches`、`/daily`、`/daily 2026-11-17`、`/help`、`/quit`。等待使用者時不持有資料庫交易。預覽在狀態改變或 30 分鐘後失效，需重新產生。

食譜問題會顯示已保存的來源片段與頁碼，或本次已確認的操作步驟；答案不採用未核對的模型自由文字。

盒內、預設整餐與實際加餐分開顯示。每日摘要只計已記錄備餐，不代表完整全天飲食。

### 來源與資料缺漏

- [四道食譜與固定資料](demo_data/catalog.json)、[來源 manifest](demo_data/source_manifest.json) 與 [保留的來源轉錄](demo_data/sources/) 保留歷史估算及版本語意。
- 一般食材使用 USDA SR Legacy，保留 record ID、原始資料集指紋及所選欄位。實際商品標示優先。使用者可透過對話提供標示與計價基準，由 `preview_product_label` 預覽確認後保存，只影響後續計算。
- 缺品牌標示、單位／生熟／瀝乾重量或密度資料時要求補齊；不以歷史每盒估算冒充新配方驗算。
- 咖哩來源為六份完整便當＋一份純咖哩；BBQ 為五份含菜＋兩份無菜。Nikujaga 原先六份與後續未確認七份方案分開保存，沒有匯入成實績。
- 蒜、油與罐頭瀝乾重量等來源缺漏仍需實際提供。**四道來源可讀取，不表示所有商品已具備可計算資料。**
- 成本顯示已知小計與完整性，不把未計價的原有食材當零。歷史價格不是即時報價。
- 固定資料目前核對了 S&B 咖哩及冷凍花椰菜的 Walmart 商品頁與包裝數量；其他商品未核對連結會明確標示缺漏。未查當地即時庫存。

## 模型設定及執行紀錄

```bash
docker compose run --rm app --model gpt-6-luna
```

模型優先順序為 `--model` → `OPENAI_MODEL` → `gpt-6-luna`。gpt-6-luna 預設 `reasoning.effort=medium`；其他模型預設不傳未驗證的 reasoning 參數。可選 `OPENAI_REASONING_EFFORT`，不相容設定明確失敗，沒有偷偷換模型。

每回合上限 12 次模型呼叫、24 次工具呼叫，連續澄清上限三輪。SDK 內建重試關閉、單次請求 timeout 45 秒。每個 `agent_runs` 保存實際模型、完整參數、SDK／工具版本、工具輸入與結果、用量與延遲；不保存 key。日常資料及對話 trace 保存在本機 PostgreSQL，真實對話會將相關使用者資料傳給所設定的模型服務。

模型無法呼叫確認工具。程式不以模型未驗證的自由文字宣告達標或寫入成功。相同回合重複食用工具使用相同操作編號；若模型服務中斷，只有在確認該筆操作已提交後才開啟一次取回結果。新回合使用新操作編號。寫交易先鎖定單人狀態列，先查去重記錄，再驗證 preview；相同 request_id 不同輸入拒絕。

## 離線完整示範

請使用全新的獨立 Compose project，保留日常資料：

```bash
docker compose -p nutrition-demo up -d --wait db
docker compose -p nutrition-demo build app
docker compose -p nutrition-demo run --rm app --init-db
docker compose -p nutrition-demo run --rm app --seed demo_data/scenario.json --scripted
docker compose -p nutrition-demo run --rm app --db-info
```

這是清楚標示的**合成資料**，假模型透過同一 Workflow、工具與服務跑「規劃六餐 → 實際八盒 → 加餐 → 一餐 → 日期更正」。預期剩七盒、合成原料 200 g、合成加餐九份，更正後當日 550 kcal。這些不是 Isaac 的目標或真實食譜營養。

Seed 在同一交易先鎖定並確認 schema 完全空白；非空會拒絕。重跑請換另一個 project 名稱，避免刪除資料。

## 測試

```bash
docker compose --profile test up -d --wait db_test
docker compose --profile test run --rm --no-deps --entrypoint uv app run --locked python -m pytest tests/ -q
```

測試只接受 `db_test/nutrition_test`，不會回退日常 DSN。每個需要資料庫的 case 建立唯一 schema，同 migrations、finally 清理。整合測試使用真實 PostgreSQL；只有外部模型回覆採固定假模型。固定時鐘與兩個 schema 的完整情境產生相同語意結果。

## 重開、備份與還原

```bash
docker compose down
docker compose up -d --wait db
docker compose run --rm app --db-info
```

一般停止及重建會保留 named volume。不要在日常環境使用刪除 volume 的操作。

備份請自行命名新檔案，避免覆寫既有備份：

```bash
mkdir -p backups
docker compose exec -T db pg_dump -U nutrition -d nutrition -Fc > backups/nutrition-YYYY-MM-DD.dump
```

還原到**新的獨立 project**，不先執行 migrations（dump 內含 schema）：

```bash
docker compose -p nutrition-restore up -d --wait db
docker compose -p nutrition-restore exec -T db pg_restore -U nutrition -d nutrition --no-owner --exit-on-error < backups/nutrition-YYYY-MM-DD.dump
docker compose -p nutrition-restore build app
docker compose -p nutrition-restore run --rm app --db-info
```

若改過使用者／庫名，對應調整命令。還原後核對 migrations、個人設定、庫存、批次、事件及筆數。PostgreSQL major version 更換要另外設計升級，不以新映像直接覆蓋舊 volume。

## 驗證狀態與後續

實際證據及凍結版本見 [驗收紀錄](docs/verification/v1-acceptance.md)，環境見 [環境紀錄](docs/verification/environment.md)。本機提交保留實作進度，沒有合併或推送到共享分支。

課程雲端網頁、正式 baseline 比較、50／200 題 benchmark 與 safety suite 尚未實作，也沒有宣稱相關評估結果。iOS、截圖辨識、即時購物與完整逐步陪煮在後續版本。

- [第一版範圍](docs/specs/v1-python-demo-scope.md)
- [完整產品範圍](docs/specs/full-product-scope.md)
- [實作計畫](docs/superpowers/plans/2026-11-17-nutrition-agent-v1.md)
- [課程要求](docs/course-requirements.md)
