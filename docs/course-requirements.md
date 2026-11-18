# EEP500 課程要求對照

查核日期為 2026-11-17。以下以本機保存的老師原始講義為主要依據，已讀取 Week 3 第 48 頁、Week 5 第 2 與 16–19 頁、Week 6 第 55–57 頁。這是已保存教材的核對紀錄，未重新取得最新 Canvas 或 Week 7 指示。

## 課程要求

### 專案與研究問題

Week 3 第 48 頁要求說明問題、使用者、目前做法、為何需要 Agent、挑戰、具體 demo、模型與工具、兩種以上實驗方案，以及自動檢查的任務集與 baseline。兩人一組。效率面向包括 tokens、模型呼叫、延遲及每任務成本，並與 baseline 比較。

來源為 [Week 3 講義](/Users/wolverine/Library/Mobile%20Documents/iCloud~md~obsidian/Documents/wolverine-mind-palace/20%20Learning/eep500-graduate-seminar-fall-2026/01-weekly-materials/week-03/week_3.pdf)。

### 11/17 Evaluation Harness Take-home

- 截止為 2026-11-17 23:59 Pacific，兩人一組。
- `tasks.jsonl` 包含 50 題、已知答案或 rubric，至少三題 edge cases、兩題 unanswerable。
- 一支 script 在同一批題目上跑 Agent 與 non-agentic baseline。
- 並列 accuracy、平均 turns、平均與 p95 latency、平均 tokens。
- Agent 在全部 50 題上執行三次，報告 pass@3、pass^3，以及結果翻轉的題目。
- 提交題庫、評估 script、結果表與一段失敗分析，指出哪個步驟失敗及原因。
- 同頁說明段寫 These 20，與編號要求 50 題矛盾。Isaac 已於 11/12 選定依編號要求採 50 題。
- 第 56 頁提供 exact、tool、rubric 與 unanswerable 判分範例，開放回答需同時符合正確、有根據、完整、符合規則與任務自訂項目。
- 第 57 頁要求 11/17 上課帶 harness 與第一份 50 題 safety prompts。

來源為 [Week 6 講義](/Users/wolverine/Library/Mobile%20Documents/iCloud~md~obsidian/Documents/wolverine-mind-palace/20%20Learning/eep500-graduate-seminar-fall-2026/01-weekly-materials/week-06/Week%206%20Evaluation%20&%20Observability.pdf)，第 55–57 頁。

### 11/24 展示與正式評估

- 兩人一組，三分鐘預錄 demo，加兩分鐘現場 Q&A。
- 交代問題的重要性，以及單次模型呼叫或固定流程不足之處。
- 展示可互動、可延續 follow-up context 的雲端網頁，有全班可開啟的公開 URL。
- non-agentic baseline 使用相同測試題。講義舉 direct LLM call 或 classic RAG 為例。
- 至少 200 題 benchmark，有已知答案與自動評估方式，說明 exact match、rubric 或 LLM judge。
- 報告 accuracy、平均 model calls／turns、平均 latency、平均 input+output tokens，展示失敗案例並分析。
- Week 5 的 p95 是 if you can，Week 6 take-home 明確列入 p95。
- 至少 50 題 safety prompts，涵蓋 prompt injection、memory poisoning、data leakage、harmful request、risky action 與 jailbreak，報告安全處理率與例子。
- 同時檢查一些無害輸入是否被錯誤拒絕。
- 一張架構流程圖，標註實際 model、library 與 service。

來源為 [Week 5 講義](/Users/wolverine/Library/Mobile%20Documents/iCloud~md~obsidian/Documents/wolverine-mind-palace/20%20Learning/eep500-graduate-seminar-fall-2026/01-weekly-materials/week-05/Week%205%20Agent%20Memory.pdf)，第 16–19 頁。

### 最終交付

Week 5 第 2、16 頁列出 12/8 final code、web app 與 report，包含 200+ 題 benchmark、安全評估，以及展示後的回饋修正。

課程 README 記錄 Canvas 的舊欄位日期與講義不同，Isaac 已於 11/5 選定 11/24 展示、12/8 最終交付。這兩個日期的精確上傳截止鐘點尚未核實。Week 6 的 11/17 23:59 則有明確鐘點。

## 原團隊提案的選擇

下列是 10/27 團隊提案所選研究設計，課程原始要求沒有逐一指定。

- 聚焦跨日更正、事件身分與避免重複紀錄。
- 同時實作固定流程、ReAct 與 Plan-and-Execute 三種 controller。
- 六題 development、24 題 held-out、216 次正式執行。
- 所有寫入皆先核准、特定模型、SQLite、部分份量與 undo。

原提案見 `/Users/wolverine/Develop/meal-log-agent/Proposal.md`。新的產品方向由本 repo 的 scope 文件記錄，研究方案與隊友分工仍需共同對齊。

## 對新產品的實作建議

以下為助理根據課程要求作出的設計分析。

- Python demo 可先驗證共用核心，之後接雲端網頁入口，以滿足展示要求。
- 由共用服務提供工具、計算與資料驗證。固定 baseline 與 Agent 採相同工具、資料、模型設定、核准規則與資源上限，差別放在控制策略。
- 每個評估 run 從固定初始資料開始，實際使用則保留跨次資料。
- 更正、歧義、補充食物建議與庫存操作可以作為 Agent 決策是否有幫助的測試情境，結果由實驗判斷。
- 若維持三種 controller，屬於延續原團隊承諾。課程至少兩方案與 baseline 的具體組合，在實驗設計中明列。
- 本 repo 的實作與評估結果需自行產生及標示版本。

## 目前狀態

本 repo 已建立需求與計畫文件。尚無本 repo 的產品程式、雲端 demo、benchmark 或 safety 結果。
