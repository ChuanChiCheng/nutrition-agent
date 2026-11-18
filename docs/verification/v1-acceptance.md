# Nutrition Agent V1 驗收紀錄

日期：2026-11-17（America/Los_Angeles）。基準文件 commit 8185889。實作沿用指定 checkout 與 codex/initial-plan 分支，保留原歷史。未推送、合併或部署。

## 已驗證

- Docker Engine 29.9.3 arm64、Compose 5.7.0，Python 3.12.14、uv 0.13.6、PostgreSQL 18.7。
- openai 2.54.0、psycopg 3.3.9、pytest 9.2.0。依賴固定 uv.lock；映像 digest 固定於 Dockerfile／compose.yaml。
- 初始化可重複、migration checksum／未知版本檢查、非空 seed 拒絕、失敗回復、外鍵。
- 四項 Decimal 容差與邊界；直接乘除避免先取倒數的尾數誤差；未知成本不當零。
- 四份 PDF 指紋全部符合計畫。咖哩、Nikujaga、炊飯保留全文抽取；BBQ 圖像人工核對轉錄。USDA SR Legacy 來源與所選營養欄位保留。
- 同次烹調分多批，一次扣原料，分配加確認剩料／耗損守恆；重複項、少分、超額及單位不符拒絕。
- 加餐確認不消耗，食用才扣庫存；略過加餐、歷史快照、庫存不足澄清、校正與食用一起成功或失敗。
- 日期更正不變總消耗；換批次歸還原盒並扣新盒；加餐差額按事件原快照；保留事件 ID 與歷史。
- 拒絕、過期、狀態變更、並行確認、重複 request_id、回覆遺失後其他寫入再重試均有真實 PostgreSQL 測試。
- 假模型走同一工具與服務：先選料理、三輪驗算、明確接受未達標、非法工具／參數、禁止模型核准、API 失敗、呼叫上限與用量 trace。
- 商品標示可預覽並確認保存；優先於一般資料，歷史快照不回寫。個人時區控制 today/yesterday。
- 相同回合重複食用工具不重複入帳；使用者回答後不殘留舊澄清問題。
- Scripted 完整情境通過：六餐計畫，實際八盒，確認加餐，食用一餐，更正日期，剩七盒；合成原料剩 200 g、合成加餐剩九份，更正日 550 kcal。
- 相同 fixture 與時鐘在兩個唯一 schema 產生相同語意結果。
- 獨立 nutrition-demo-check project 實際 down/up，所有表筆數保持一致。
- pg_dump custom backup 已於 nutrition-restore-check 新 volume 實際 pg_restore，schema 版本及 profile／inventory／batches／events 等 13 表筆數相同。原始 stdout 包含首次 build 訊息，改以實際 JSON 資料比對確認。
- CLI 離線互動已實際執行 /inventory、/batches、/daily、/quit，呈現可閱讀結果。

## 待完成與驗證限制

- 本機 OpenAI key 等待 Isaac 設定後通知；目前未進行任何真實 API 請求，沒有真實 tokens、成本、模型權限或完整自然語言表現證據。
- 四道來源食譜可讀，但部分品牌、液體單位、罐頭瀝乾重量、蒜／油用量仍需實際資料。系統會要求澄清，不能宣稱全部食譜的個人實作營養已核實。
- 目前只有 S&B 咖哩與冷凍花椰菜核對 Walmart 商品頁與包裝數，其他品項連結明確缺漏。未驗證當地庫存，歷史價格不是即時售價。
- 配方步驟使用確認清單產生份量，保留原始全文供對照。鍋具容量、液體用量與最終熟度仍依實際條件確認。
- 尚未提供雲端網頁、正式 baseline、benchmark、安全評估或 iOS。這些是獨立後續里程碑。

## 開發預設與凍結界線

工具 schema 版本 v1.0，來源資料版本 v1.0；實際 fingerprint 與最後測試數於最終檢查後補入。每次客製化三輪，每回合 12 次模型／24 次工具，澄清三輪，模型 max_output_tokens=4096、timeout=45 秒，SDK 自動重試關閉。預設模型 gpt-6-luna、medium。假模型開發題已覆蓋停止與失敗分支，尚無真實模型的效能調整證據；正式比較前需凍結實際 API 的 model ID 與全部參數。

## 實作判斷紀錄

- 使用指定現有 checkout，未另建 worktree，沒有改動其他 repo 或 Obsidian。
- Skill 包裝腳本缺執行權限，採 bash／等價紀錄；未改動已安裝指引檔。
- 未知成本沒有可信上限，因此呈現已知小計與未知總額；不編造估算區間。
- 原始料理與估算保留，缺漏商品允許經使用者確認標示補齊，不把歷史每盒數字套到新配方。
- 規劃與確認由應用程式保存。未驗證模型自由文字不作為執行或達標依據，介面顯示服務結果與來源步驟。
- 每個回合的普通食用工具共用一個操作編號，防止模型重複工具迴圈把同一餐記兩次；若同一句有多餐，需分開明確記錄。
