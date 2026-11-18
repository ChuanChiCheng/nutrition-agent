# EEP500 Nutrition Agent 評估題庫與 Harness 設計

## 意圖

為 Nutrition Agent V1 建立一份可重跑、可核對的 50 題評估題庫，並用同一支程式比較 Agent 與 non-agentic fixed-workflow baseline。目標是測量使用者任務的正確率、互動輪數、模型呼叫、延遲與 tokens，同時檢查營養、庫存、餐點紀錄與核准流程是否符合 V1 行為。

Week 6 take-home 的截止時間為 2026-11-17 23:59 Pacific。這份設計整理於 2026-11-18；截止已過。題庫、程式、結果或 failure analysis 的實際完成狀態須另行核對，不因本文件而視為已完成。此 harness 設計亦可供 11/24 展示和 12/8 最終專案擴充。

## 課程要求與產品決定

課程要求 `tasks.jsonl` 恰含 50 題、答案或 rubric、至少 3 題 edge cases、至少 2 題 unanswerable；一支 script 對同一批 50 題執行 Agent 和 baseline；並列 accuracy、平均 turns、平均及 p95 latency、平均 tokens。Agent 全題執行三次，報告 pass@3、pass^3、翻轉題目，並提交一段指出失敗步驟與原因的 failure analysis。第 55 頁內文提到 These 20，與同頁編號要求 50 矛盾；Isaac 已選定依編號要求採 50 題。課程要求以本地核讀的 [course-requirements.md](../../course-requirements.md) 為索引，原始講義為 Week 6 第 55–57 頁。

V1 的行為規則來自 [v1-python-demo-scope.md](../../specs/v1-python-demo-scope.md) 與 [V1 實作計畫](../plans/2026-11-17-nutrition-agent-v1.md)，屬產品決定而非課程指定：明確的食用紀錄可直接執行；批次不明時先問；更正先預覽並等使用者核准；加餐庫存不足時先釐清並將校正與食用紀錄一起處理；一次烹調可建立多個組成不同的批次，但食材總用量只扣一次；四項營養範圍都符合才標示達標，使用未四捨五入的精確數值比較。

## 範圍與限制

本次交付範圍為 development cases、正式 `tasks.jsonl`、單一評估入口、結果表與一段 failure analysis 的可重現格式。每個正式任務有固定初始商業資料、使用者要求、必要時的 scripted answers、預期資料變化、操作順序條件及文字回覆 rubric。評估以隔離測試資料庫和共用產品服務執行，不接觸個人實際資料。

課堂展示及期末所需的 200+ 題 benchmark、至少 50 題獨立 safety prompts、雲端網站、正式展示素材均不屬於本次 50 題題庫；之後可重用 runner，但須另外標版本與資料集。寫入重試的故障注入檢查屬開發／可靠性驗證，不佔正式 50 題。Agent 每次三次重跑仍是正式評估的一部分，每一次都從乾淨起始狀態開始。

## 考慮過的作法

1. **直接呼叫 Agent 與共用服務（選定）**：runner 載入題目，在每次試跑建立隔離狀態，直接呼叫 `DemoAgent` 或 fixed-workflow baseline，再讀取結構化結果、操作 trace 與最終資料。這和 V1 的 `NutritionService`、`DemoAgent.handle(message)` 及工具介面相接，能精確固定資料、時間、答案和核准，也能自動比較整份商業狀態。
2. **模擬人手操作 CLI**：runner 啟動互動式命令列、模擬輸入，再分析終端輸出。這會測到 CLI 外層，但固定資料、動態 preview ID、service trace 和量測邊界較難穩定取得。

Isaac 選擇第一種。正式 Agent 與 baseline 使用相同模型設定、題目資料、服務操作、資源上限、scripted user answers 與核准規則。baseline 的 Python 固定流程決定下一步；Agent 可依工具回傳結果選擇下一步。兩者差異聚焦於控制策略。

實作預設：baseline 每次收到使用者訊息時以一次受限 JSON action extraction 取得意圖與參數，再由 Python 固定 routing table 呼叫共用 service operations；它不使用模型挑選工具的迴圈，也不在觀察工具結果後再讓模型選下一步。這是助理依已選 fixed-workflow 方向補足的工程決定，不是課程指定。若實際 SDK 無法穩定輸出受限 action，實作者可調整實作方式，但需保留 Python 決定步驟的差異並記錄。

## 題庫分布

48 題按主要能力分布如下，另加 2 題 unanswerable，總數正好 50。Edge case 標籤與能力分類重疊，不額外加題。

| 主要能力 | 題數 |
|---|---:|
| 選料理與營養調整 | 10 |
| 烹調結果與多批次分配 | 8 |
| 加餐與庫存 | 7 |
| 記錄食用 | 8 |
| 更正紀錄 | 10 |
| 查詢 | 5 |
| 無法回答 | 2 |
| **合計** | **50** |

至少五題標記為 edge cases：營養邊界剛好通過、略微超出營養界線、加餐庫存不足後先釐清、多批次分配守恆正確，以及分配超量時拒絕寫入。其餘案例涵蓋一般成功路徑、歧義、拒絕／不變狀態與 V1 各項功能。

兩題 unanswerable 使用不可由 fixture 或 scripted answer 得知的資料：詢問未記錄餐點的精確營養；詢問紀錄中不存在的過去餐點。兩題皆需坦白說明資料不足，不補造數字或紀錄，商業狀態不變。

營養邊界測試使用合成目標 600 kcal、40 g protein、65 g carbs、20 g fat，合法區間分別是 570–630、40–44、58.5–71.5、18–22。至少一題使用含邊界的精確值並預期通過，另一題只在一項超出界線的微小量並預期失敗；判分使用 Decimal 完整值，不以顯示時的四捨五入代替。

多批次合成案例例如一次烹調使用 800 g 雞肉，600 g 分配到六盒便當、200 g 分配到一批純咖哩：庫存總扣量為 800 g，批次營養依分配計算。對照案例若分配總量為 850 g，預覽／確認應失敗，不留下部分批次或庫存異動。所有食材分配、confirmed remaining／loss 及 cooking-run 總用量須遵守 V1 守恆規則。

## 任務資料格式與 fixture

正式題庫使用 UTF-8 JSONL，一行一題，且總行數固定 50。每個 JSON object 最少包含：

- `id`、`category`、`labels`：唯一題號、主要能力與 `edge`／`unanswerable` 標籤。
- `fixture`：該題完整的起始狀態；明列 profile、營養目標、庫存、批次、加餐方案、既有事件、題目需要的 catalog 狀態，以及必要的 workflow stage／pending state。每次執行從此狀態重新建立。
- `request`：使用者第一句要求。
- `scripted_answers`：若助理呼叫結構化 `ask_user` 工具，依序送出的預寫回答。若未詢問就不送答案；評分器另檢查問題是否切中必要澄清。答案用完後不提供額外資訊。沒有補充資料的 unanswerable 題不提供答案。
- `approval`：本題的 scripted 核准結果；僅在操作預覽出現後送出。每次使用實際產生的 preview ID 綁定使用者核准。
- `expected_changes`：評分器用來由 fixture 建立預期終態的語意變更清單。新紀錄使用可比對的欄位，不要求資料庫自動 ID 固定。
- `required_order`：需符合的動作條件，例如先問批次再寫入，或更正先預覽並等核准。
- `reply_rubric`：固定 judge 逐項評分的任務專屬標準。

Answers、expected changes、required order 和 rubric 可與 fixture 放在同一行，符合題庫攜帶已知答案／rubric 的要求；runner 對控制器只傳送 fixture、request 及實際得到的 scripted answers／approval，不傳送答案鍵或 rubric。固定應用程式時鐘設於版本化的全域 eval config，不在每題重複；Agent、baseline 和所有重跑共用同一個 America/Los_Angeles 時刻。

fixture 中可預期的數值優先採有來源且可核對的商品標示／資料集。多數狀態與數值採清楚標示為 synthetic 的控制資料，以便預先精算正確答案與邊界。舊 PDF 的估算值不當作精確 ground truth；缺漏資料題只評分助理是否說明限制。保留來源、狀態及版本欄位，避免合成值與實際資料混淆。

## 執行與隔離

1. 讀取版本化 eval config 與任一 JSONL task，驗證必填欄位、題數、ID 唯一性及 edge／unanswerable 最低數量。
2. 在明確指定的測試資料庫中，為每一個 controller/task/repeat 建立新的 schema，套用目前 migrations，載入 fixture，並注入全域固定 clock。嚴禁從 DATABASE_URL 或任何個人資料 seed 回退。
3. 執行一個完整 scripted user episode。當 controller 以結構化 `ask_user` 工具詢問時，runner 依序傳入下一個預寫答案；若 controller 未詢問，就沒有答案可取。Grader 檢查詢問是否解決題目中的必要歧義。預覽核准只於 preview 已顯示後依 task script 傳入，並以當下 preview ID 執行使用者核准／拒絕。使用者等待時間為零，不計入 latency。
4. Agent 對 50 題各跑 3 次；baseline 對 50 題各跑 1 次。所有 episode 使用相同 initial fixture 和 frozen runtime settings，各自 schema 於 grading 後清除，沒有任何 run 沿用另一 run 的狀態。
5. 記錄 response、controller trace、資料庫最終商業狀態、逐次模型使用量與 wall-clock latency。保存 run metadata：程式 commit、model ID、SDK／推理設定、tool/schema 版本、catalog／fixture 版本、DB migration 版本與資源上限。

runner 需在執行前檢查 `DemoAgent`、`NutritionService`、`Workflow`、service methods 與 `TOOL_VERSION` 的當前介面。設計時 repository snapshot 為 commit `751b55b`，tool version 為 `v1.0`；共用工作區可並行更新，因此實作及正式 run 前須重新核對，不應把 snapshot 當成永不變動的 API。

## 判分

一題只在以下三面全數通過時算 pass：

1. **商業終態**：獨立 grader 從 fixture 套用 expected changes，與實際完整商業狀態做語意比對。核對 profile、庫存、烹調 run、批次、加餐及食用事件；保留所有無關資料不變。對新事件可忽略隨機 ID 和時間戳，但不可忽略數量、日期、批次、營養快照、加餐、movement 次數或多出的寫入。純 agent-run telemetry 不屬於商業終態。
2. **流程順序**：按 trace 和 scripted interaction 檢查澄清、preview、approval、寫入的先後。例如明確食用無需核准；不明批次要先問；更正要 preview 後等明確核准；加餐不足要先釐清，再以核准的 reconciliation-plus-meal 操作一起更新。
3. **文字回答**：固定 rubric 評分正確、資料有根據、完整、遵守規則及 task-specific criteria。明確檢查沒有宣稱未完成的寫入，沒有將估算或未知營養說成確定值，unanswerable 時沒有捏造。

狀態與流程採程式化語意檢查；自由文字採固定、版本化的 judge model 和逐項 rubric。實作者依評估時可用的模型選定 judge，優先採用與 controller 不同的模型；正式評估前凍結並記錄 judge model ID、prompt、輸出格式與推理設定。Judge 只評分 response，不參與 Agent 或 baseline 的模型選擇。Judge 的 latency／tokens 不進入 controller 指標。Development cases 先用已知的通過與錯誤輸出校驗判分規則；如 judge 有歧義，先修正 rubric，再凍結正式題庫及 judge 設定。

同一 request ID 的寫入重試應另以開發／可靠性檢查驗證不重複扣庫存，不列入 50 題。benchmark 的 agent rerun 隔離由每次建立新 schema 保證；兩者不可混為一件測試。

Episode 開始後的 controller exception、timeout 或資源上限耗盡皆算該次 task failure，保存當時 trace 和用量，不以替代重跑覆蓋。若在 controller 開始前發生測試 schema 建立、fixture 載入等 harness infrastructure failure，該次正式評估標示為 incomplete；修正後以新 run ID 從頭重跑整批，不能只挑選失敗題重跑。Judge 服務中斷亦使整批評估 incomplete，因該批文字答案尚無完整判分。

## 指標與交付

- `turns` 是單次助理回覆數；一次澄清問答後再回覆，計 2 turns。`model_calls` 另行統計，不以內部呼叫替代互動輪數。
- 每次 episode 的 latency 從第一個使用者要求送出到最終助理回覆完成，包含 controller 的模型與工具操作時間，不含 scripted user 的等待與 judge 評分時間。
- 每次 episode 的 tokens 是 controller 這次所有模型呼叫的 input + output token 總數。平均值與 p95 以 episode 為樣本：Agent 150 筆、baseline 50 筆；報告同時列出樣本數。
- p95 使用 nearest-rank 定義，並在結果表標記；這是助理選定的統計慣例，講義只指定 p95 指標。
- 報告 baseline accuracy、Agent 單次 episode accuracy（150 次總體與三次各自的準確率）、pass@3（同題至少一次通過）、pass^3（同題三次全通過）及重跑結果翻轉的題目。對比模型／工具設定一致，明確標記 baseline 僅跑一次。
- 保存一段 failure analysis，附題號、trace 中失敗步驟、造成原因、資料狀態後果及可能改善方向。結果表連同 task、runner、judge 與 runtime 版本。
- 先建立建議 3–5 題、獨立於正式題庫的 `development_tasks.jsonl`，包含一般成功、需要澄清／核准、資料不足及至少一項關鍵邊界。這些只用來修正格式、runner 和 grader，不計入正式 50 題或報告 accuracy。

## 尚待實作／驗證

本文件是設計，不代表 `tasks.jsonl`、development cases、eval runner、正式評估或課程上傳已完成。實作前需重新核對共用 V1 工作區和 team decision；正式執行前凍結題庫、model／SDK／tool 版本及設定。課程要求的 200+ 題 benchmark 與獨立 safety suite 另行規劃及追蹤。
