---
type: project
status: active
created: 2026-11-17
updated: 2026-11-17
topics: [agentic-ai, meal-prep, python-demo]
entities: [EEP 500, Nutrition Agent]
sources: ["[[00 Inbox/EEP500 Nutrition Agent — 備餐流程訪談]]"]
related: ["[[20 Learning/eep500-graduate-seminar-fall-2026/04-final-report/product/完整產品範圍]]", "[[50 Projects/Personal Scrum/Projects/EEP500 Nutrition Agent Final Project]]"]
---

# Nutrition Agent 第一版 Python Demo 範圍

## 已確認範圍

Isaac 於 2026-11-17 確認，以 Python 互動式示範完成一批備餐的規劃、實際分裝、食用紀錄與更正，使用本機資料儲存。

| 能力 | 第一版行為 |
|---|---|
| 個人設定 | 保存營養目標、鍋具與餐盒容量，重開程式後可沿用。預設六餐、同一道料理。 |
| 食材確認 | 顯示庫存供修正，以純文字輸入購入資訊，確認後加入。 |
| 食譜選擇 | 從少量事先準備的食譜推薦選項，解釋難點、提供完整步驟與成本估算。 |
| 烹調協助 | 提供完整步驟與基本問答，依現有鍋具安排必要的分批。 |
| 完成備餐 | 確認實際用量與最終盒數，扣除食材、建立備餐批次，計算每盒四項營養。 |
| 補充建議 | 每盒低於原目標時，顯示差距與簡單補充食物建議。 |
| 記錄食用 | 指定批次後預設一盒，資訊明確時直接記錄，更新當日營養與剩餘盒數。 |
| 澄清與更正 | 批次不明先詢問。更正日期或批次前預覽並確認，連動更新受影響資料。 |
| 查詢 | 每日熱量、蛋白質、碳水與脂肪相對目標的進度，各批剩餘盒數與每盒營養。 |

## 已確認的版本取捨

- 營養與價格使用事先核對、附來源的固定資料，估算明確標示。
- Walmart 即時查貨與替代商品搜尋放到後續版本。
- 訂單截圖辨識放到後續版本，第一版採純文字購入資訊。
- 完整逐步烹調陪伴與風味回饋循環放到後續版本。
- iOS App 是最終介面，第一版採 Python。
- 外食、零食與飲料記錄放到後續版本。

## 代表性示範

1. 讀取既有營養目標與食材庫存，確認庫存，選一道原定六餐的料理。
2. 提供完整步驟與成本估算，使用者完成烹調後回報實際用量與八盒成品。
3. 經確認後一次扣除食材並建立八盒批次，重算每盒營養，提出補充建議。
4. 使用者記錄今天午餐吃一盒，顯示當日營養與七盒剩餘。
5. 使用者說其實是昨天吃的，顯示更正預覽並取得確認。
6. 將營養從今天移到昨天，批次仍剩七盒。
7. 重開程式，設定、庫存、批次及事件均可查詢。

另用兩個名稱相似的批次，示範澄清與更正批次。只準備一個批次無法展示這條需求。

## 完成條件

- 自然語言互動可走完代表性示範，寫入成功後才回報完成。
- 本機狀態可跨次保存，示範可以用獨立資料庫重設與重跑。
- 日營養、剩餘盒數與更正結果由程式計算，避免對話文字與資料脫節。
- 更正遭拒、資料不足或批次不明時，資料維持一致並能繼續互動。
- 每項示範資料具有來源或清楚的合成／估算標示。

## 待驗證的技術建議

下列為助理的實作建議，尚未以程式驗證。

- 沿用 `/Users/wolverine/Develop/meal-log-agent`，新增獨立的互動 demo 模組及檔案型 SQLite 資料庫。
- 現有評估環境採每次重設的記憶體資料庫，目前批次營養只有熱量與蛋白質。需處理持久化及碳水、脂肪欄位差異。
- 現有 controller 採所有變更先核准的規則。新的互動 demo 應遵守本次確認的直接記錄與更正前核准規則。
- 單一助理透過受驗證的工具查詢與操作資料，算術與資料更新由程式執行。
- 實作計畫位於 `/Users/wolverine/Develop/meal-log-agent/docs/superpowers/plans/2026-11-17-nutrition-demo.md`。

## 來源

- [[00 Inbox/EEP500 Nutrition Agent — 備餐流程訪談]]
- [[20 Learning/eep500-graduate-seminar-fall-2026/04-final-report/product/完整產品範圍]]

## Repository 文件來源

此為 2026-11-17 建立新 repo 時的需求快照，來源為 `/Users/wolverine/Library/Mobile Documents/iCloud~md~obsidian/Documents/wolverine-mind-palace/20 Learning/eep500-graduate-seminar-fall-2026/04-final-report/product/第一版 Python Demo 範圍.md`。

## 2026-11-17 工作區決定

Isaac 隨後明確要求另開 `/Users/wolverine/Develop/nutrition-agent`。前述沿用 meal-log-agent 的建議保留作為規劃歷史，實際計畫以本 repo 的 `docs/superpowers/plans/2026-11-17-nutrition-demo.md` 為準。
