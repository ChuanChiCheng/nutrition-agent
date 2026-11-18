# 環境證據

2026-11-17，Apple Silicon：Docker Engine 29.9.3 arm64、Compose 5.7.0、host uv 0.13.6。
Python、uv、PostgreSQL 映像固定 digest，詳見 Dockerfile 與 compose.yaml。Python dependencies 固定於 uv.lock。

官方設計依據：
- https://hub.docker.com/_/postgres（PostgreSQL 18 volume 根目錄）
- https://docs.astral.sh/uv/guides/integration/docker/（locked dependency installation）
- https://www.psycopg.org/psycopg3/docs/basic/transactions.html（短交易）
- https://developers.openai.com/api/docs/guides/function-calling（Responses 工具輸出）

`.env` 僅本機、Git 與 build context 排除；資料庫無 host port。預設密碼僅供本機開發，兩庫使用不同 volume。所有測試另外使用唯一 schema。
