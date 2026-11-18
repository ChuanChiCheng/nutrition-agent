# Nutrition Agent

Isaac 的備餐助理。完整產品目標為 iOS App，第一個開發里程碑為 Python 互動式示範。

## 文件

- [完整產品範圍](docs/specs/full-product-scope.md)
- [第一版 Python demo 範圍](docs/specs/v1-python-demo-scope.md)
- [實作計畫](docs/superpowers/plans/2026-11-17-nutrition-demo.md)
- [課程要求對照](docs/course-requirements.md)

## 狀態與範圍

2026-11-17 已完成需求訪談及設計選項確認，repo 保存整合範圍與實作計畫。環境、資料庫與產品程式尚待實作。

第一版流程為規劃一批備餐、確認實際用量與盒數、記錄食用及更正紀錄。互動與後續評估預計共用資料及工具核心。課程另要求雲端互動網頁、baseline 比較、benchmark 與安全評估，依課程要求對照安排。

原始需求與決策保存於 canonical Obsidian vault。隊友的 `meal-log-agent` 是依舊規格建立的獨立實作。

## 已確認技術方向

Docker Compose＋PostgreSQL，Python app 內使用 uv 管理依賴。單一使用者，預設 gpt-6-luna，模型可透過設定切換。固定主流程搭配階段內的彈性工具迴圈。

同次烹調的不同成品組成各建一批，原料總用量只扣一次；食用時計入確認的加餐並扣除加餐食材，更正前預覽與核准。四道實際食譜及營養容差詳見第一版範圍。
