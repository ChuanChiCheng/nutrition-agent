---
type: project
status: active
created: 2026-11-17
updated: 2026-11-17
topics: [agentic-ai, meal-prep, requirements]
entities: [EEP 500, Nutrition Agent]
sources: ["[[00 Inbox/EEP500 Nutrition Agent — 備餐流程訪談]]"]
related: ["[[50 Projects/Personal Scrum/Projects/EEP500 Nutrition Agent Final Project]]", "[[20 Learning/eep500-graduate-seminar-fall-2026/04-final-report/product/第一版 Python Demo 範圍]]"]
---

# Nutrition Agent 完整產品範圍

## 目標與依據

協助 Isaac 從營養目標、現有食材與廚房條件出發，完成規劃、採買、烹調、分裝、食用紀錄與後續改善。最終介面為 iOS App。

本文件整理 2026-11-17 訪談中 Isaac 確認的需求。完整範圍獲確認後，Isaac 另外確認了第一版 Python 示範範圍。原始訪談保留於 [[00 Inbox/EEP500 Nutrition Agent — 備餐流程訪談]]。

## 已確認需求

### 個人設定與規劃

- 跨次使用保存營養目標、鍋具與餐盒容量。
- 預設沿用先前營養目標，直到 Isaac 要求更改。
- 每批預設六餐、同一道料理，可由 Isaac 改餐數或要求更多變化。
- 優先使用現有食材，需要時建議購買新食材。
- 選食譜前解釋較困難的操作，讓 Isaac 決定本次是否願意學習。
- 推薦時考量鍋具與餐盒容量。餐盒容量是參考，實際裝盒結果由烹調後確認。

### 食材庫存

- 每次開始規劃時，列出已記錄的食材與剩餘數量，讓 Isaac 一次確認或修正。
- 購入資訊接受訂單截圖或純文字，確認商品與數量後入庫。
- 烹調後確認實際用量，再自動扣除食材庫存。

### 採買與成本

- 預設 Walmart，提供商品連結，由 Isaac 加入購物車。
- 商品缺貨時尋找合適替代品，經確認後更新購物清單與食譜。
- 顯示整批及每餐預估成本，目前沒有嚴格預算上限。
- 成本計算前核對實際用量，這是 Isaac 接受且認為必要的確認。

### 烹調與分裝

- 開始前提供完整食譜與全部步驟，開始後逐步協助完成。
- 需要時簡化操作或安排分批烹調。
- 按確認的實際用量與最終盒數重算每盒營養。
- 如果每盒低於原定目標，建議簡單的補充食物。

### 風味回饋

- 餐點完成後主動用幾個簡單問題協助描述風味。
- 保存回饋與下次調整方向。
- 再做同一道料理時提出先前建議，經 Isaac 確認後套用。

### 食用紀錄、更正與查詢

- 可指定吃了哪批已完成的備餐，預設食用一整盒。
- 資訊明確時直接記錄一盒，計入當日營養並扣除該批一盒。
- 批次不明確時先列出候選批次，確認後才寫入。
- 可透過對話更正日期或批次，先顯示影響並取得確認，再同步更新營養與盒數。
- 查詢每日熱量、蛋白質、碳水化合物與脂肪相對目標的進度。
- 查詢每批剩餘盒數與每盒營養。

### 資料來源

- 優先使用實際購入商品的營養標示。
- 一般食材使用 USDA 資料。
- 缺資料而需估算時清楚標示。

## 版本決定

- 第一版介面為 Python 互動示範，詳見 [[20 Learning/eep500-graduate-seminar-fall-2026/04-final-report/product/第一版 Python Demo 範圍]]。
- 外食、零食與飲料紀錄留到後續版本，互動細節尚待訪談。
- 主動備餐提醒目前暫不需要。
- 半盒與克數紀錄曾由助理提出，但尚未確認為需求。

## 與既有提案的關係

2026-10-27 的提案聚焦跨日更正，當時將食材庫存、食譜推薦與影像排除於研究原型之外。本次訪談確認的產品願景更廣，並新增第一版範圍。舊提案保留作為歷史與課程研究脈絡。

本文件代表產品決定。課程指定的 controller 比較、題數與交件要求，仍需依課程原始要求獨立核對，產品示範完成不代表評估作業完成。

## 來源

- [[00 Inbox/EEP500 Nutrition Agent — 備餐流程訪談]]
- [[20 Learning/eep500-graduate-seminar-fall-2026/04-final-report/proposal/google-docs-team-snapshot-2026-10-27]]
- [USDA 資料說明](https://fdc.nal.usda.gov/data-documentation/)
- [FDA 份量說明](https://www.fda.gov/food/nutrition-facts-label/serving-size-nutrition-facts-label)

## Repository 文件來源

此為 2026-11-17 建立新 repo 時的需求快照，來源為 `/Users/wolverine/Library/Mobile Documents/iCloud~md~obsidian/Documents/wolverine-mind-palace/20 Learning/eep500-graduate-seminar-fall-2026/04-final-report/product/完整產品範圍.md`。
