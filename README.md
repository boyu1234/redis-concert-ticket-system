# Redis 演唱會秒殺搶票系統

用 FastAPI、Redis 和原生 JavaScript 示範限量售票。請使用 demo_001 等測試代號。

- **Transactions**：WATCH / MULTI / EXEC 檢查庫存與重複購買，同一筆交易扣庫存、登記買家、寫入訂單及發布庫存事件。
- **Queue**：API 用 LPUSH 入列，Worker 用 BRPOP 依序取出，模擬寫入資料庫、產生結帳連結與寄信。Worker 在取出後中斷時，該訂單不會自動重送。
- **Pub/Sub**：訂閱事件後透過 WebSocket 推送目前庫存。瀏覽器重連時會重新取得庫存。

## 本機啟動

準備 Python 3.10+ 與專用的 Redis。以下使用 PowerShell，在專案資料夾執行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn main:app --port 8000
```

在另一個終端機執行 `.\.venv\Scripts\python.exe -u worker.py`。從瀏覽器開啟 [搶票頁](http://127.0.0.1:8000/) 或 [Swagger UI](http://127.0.0.1:8000/docs)。

| 環境變數 | 用途 |
| --- | --- |
| REDIS_URL | API 與 Worker 共用的 Redis 連線。支援 redis:// 和 rediss://。 |
| INITIAL_STOCK | 首次啟動時的票數，預設 10。Redis 已有庫存時保留現值。 |
| TEST_REDIS_URL | 併發測試專用的空 Redis 資料庫。 |

## 驗收

在專用空白測試 Redis 執行，測試會建立並清除三個專題鍵。測試時請停用該資料庫的 Worker。

```powershell
$env:TEST_REDIS_URL = 'redis://127.0.0.1:6379/1'
.\.venv\Scripts\python.exe test_concurrency.py
```

預期 100 個不同代號共售出 10 張、剩餘 0、佇列有 10 筆，重複代號被拒絕。另用兩個瀏覽器分頁開啟網站，購票後確認兩邊顯示新庫存，再檢查 Worker 日誌是否完成該筆模擬訂單。用相同代號再次提交，確認庫存維持原值。

## GitHub 與雲端部署

1. 檢查待提交的檔案後，建立 GitHub 儲存庫 `redis-concert-ticket-system`，將此目錄的專案檔案提交並推送。實際 `.env`、Redis 匯出及快照由 `.gitignore` 排除。
2. 在 Render 的同一工作區及區域建立專用 **Key Value**、**Web Service**、**Background Worker**。Key Value 為 Redis 相容的 Valkey。建立前在控制台確認方案及費用。[Key Value](https://render.com/docs/key-value) · [Background Worker](https://render.com/docs/background-workers)
3. 兩個運算服務選同一 GitHub 儲存庫與分支，建置指令皆為 `pip install -r requirements.txt`。在兩個服務的環境設定中填入 Key Value 的內部連線網址 `REDIS_URL`，並在 Web Service 設定 `INITIAL_STOCK=10`。
4. Web Service 啟動指令為 `uvicorn main:app --host 0.0.0.0 --port $PORT`，健康檢查路徑為 `/healthz`。Worker 啟動指令為 `python -u worker.py`。[Web Service](https://render.com/docs/web-services)
5. 用 Web Service 提供的 HTTPS 網址進行雙分頁驗收。前端會使用同一網域的 HTTPS API 和 WSS。[WebSocket](https://render.com/docs/websocket)

公開示範使用共用庫存，用完後可由管理者配置新的專用資料庫重新展示。Redis 連線網址只存於服務端，公開頁面僅提供模擬購票。

## 本機實測結果（2026-11-14）

使用隔離的 Redis 8.0.5 實例。100 個不同代號競購 10 張票，成功 10 筆，庫存歸零，買家及佇列各 10 筆。整合測試中，兩條 WebSocket 皆收到庫存從 10 更新為 9。重複購票回傳 HTTP 400。Worker 取出並完成該筆模擬訂單，佇列回到 0。

## 目前的公開部署

- [Render 搶票示範](https://redis-concert-ticket-system.onrender.com/) 使用免費 Web Service 與 Redis 相容的 Key Value。
- 雲端實測購票成功，兩個分頁庫存透過 WSS 同步由 10 變為 9。雲端訂單會入列，Worker 取單及模擬處理已於本機驗證。上方 Background Worker 步驟適用於另行部署。
- GitHub `main` 為部署版。[學校 Drive](https://drive.google.com/drive/folders/1709z8aGOYQzZ3TDJepCkl-B3S5CBAO9N) 收錄原始本機版、簡報、影片、UML 與 Redis 匯出。
