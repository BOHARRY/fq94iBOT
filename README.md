# 智慧自動化發文機器人 - 開發與除錯紀實

## 專案概述

本專案旨在透過 Selenium 自動化技術，實現對特定後台管理系統的自動登入及文章發布功能。其核心挑戰在於應對現代前端框架（如 Vue.js 或 React）帶來的複雜性，包括非同步數據加載、動態 DOM 更新以及複雜的客戶端驗證機制。

經過一段艱辛但富有成效的除錯過程，我們成功打造了一個極其健壯、穩定且可靠的自動化腳本。本文件旨在記錄這段寶貴的開發歷程以及最終的程式碼架構。

---

## 程式碼架構

整個專案由三個核心 Python 檔案組成，各司其職，實現了高度的模組化和可維護性。

### `config.py` - 設定中心

此檔案是整個機器人的大腦中樞。所有可變的設定，如登入憑證、目標網址、API 金鑰以及最重要的 **Selenium 元素定位器 (Locators)**，都集中在此管理。這種設計將設定與邏輯分離，當網站前端結構變更時，我們僅需修改此檔案，而無需觸及核心程式碼。

### `scraper.py` - 核心爬蟲邏輯

`SeleniumScraper` 類別封裝了所有與瀏覽器互動的複雜操作。它是整個專案的執行者，其關鍵功能包括：

- **智慧登入 (`login_process`)**: 包含重試機制與 OpenAI 驗證碼識別。
- **健壯的發文流程 (`post_new_article`)**: 這是我們除錯過程的重點，最終版本包含了應對各種前端挑戰的精密邏輯。
- **多策略互動**: 綜合運用了 `WebDriverWait` 智慧等待、JavaScript 點擊、DOM 狀態驗證等多種高階技巧。

### `run.py` - 執行入口

作為程式的啟動點，此檔案負責協調整個自動化流程，並向使用者提供清晰、友善的執行結果報告。

---

## 史詩級的除錯之旅

我們的成功並非一蹴可幾，而是經歷了一系列系統性的問題排查與策略演進。以下是我們解決這個頑固問題的完整歷程：

### 階段一：初步失敗與 `StaleElementReferenceException`

- **問題**: 在填寫完內容後，點擊「儲存」按鈕時程式崩潰。
- **原因**: 腳本與富文本編輯器 (CKEditor) 互動後，頁面 DOM 發生了刷新，導致之前獲取的「儲存」按鈕參考失效。
- **解決方案**: 為點擊「儲存」按鈕的操作加入了重試迴圈，若按鈕失效則重新尋找。

### 階段二：前端驗證的挑戰

- **問題**: 點擊儲存後，標題和內文被清空，並提示「請輸入標題」。
- **原因**: 自動化腳本填寫速度過快，未觸發前端框架的 `onchange` 或 `onblur` 等驗證事件，導致框架認為欄位是空的。
- **我們的嘗試與演進**:
    1.  **模擬 `Tab` 鍵**: 嘗試在輸入標題後 `send_keys(Keys.TAB)`。**副作用**: 這意外地將焦點轉移到下一個元素，導致出現了「幽靈下拉選單」的 Bug。
    2.  **點擊 `<body>`**: 改為點擊頁面背景來讓輸入框失去焦點。更安全，但仍未解決根本問題。
    3.  **JavaScript 點擊**: 為了解決可能的「抖動」或元素遮擋問題，改用 `execute_script` 來點擊儲存按鈕。
    4.  **直接提交表單**: 嘗試繞過按鈕，直接 `form.submit()`。

### 階段三：決定性的突破 - 非同步載入陷阱 (Race Condition)

- **問題**: 儘管我們用盡了各種點擊和提交技巧，問題依舊存在。
- **您的關鍵洞察**: 您發現，**一進入文章編輯頁面，頁面狀態就已經是錯誤的**。
- **根本原因**: 我們點擊「最新消息」後，腳本在文章列表的**數據流**完全加載完成前，就點擊了那個「搶跑」的「新增文章」按鈕。我們進入了一個基於不完整數據的、已損壞的編輯頁面。

### 階段四：最終的完美解決方案

基於這個決定性的發現，我們制定了最終的、萬無一失的策略：

1.  **等待真正的數據標誌**: 點擊「最新消息」後，我們不再等待「新增文章」按鈕，而是耐心等待**文章列表的第一筆數據 (`li.li-data`)** 被渲染出來。
2.  **加入強制延遲**: 為了給予頁面最充裕的穩定時間，我們在列表出現後，額外**強制等待 5 秒**。
3.  **最穩定的跳轉**: 在確認頁面完全就緒後，我們採用最不會產生副作用的方式——**直接讀取「新增文章」按鈕的 `href` 屬性，並使用 `driver.get()` 進行導航**。

這個結合了「智慧等待」、「強制等待」和「直接導航」的策略，最終完美地解決了所有問題。

---

## 如何執行

### 方案一：直接執行 (手動)

1.  確保已安裝所有必要的套件 (如 `selenium`, `openai`, `webdriver-manager`)。
2.  在 `config.py` 中填寫您的登入憑證和 OpenAI API 金鑰。
3.  **手動修改 `scraper.py`** 中的 `post_new_article` 函式呼叫，填入您想發布的標題和內容。
4.  執行以下指令：
    ```bash
    python run.py
    ```

### 方案二：透過 LINE Bot 執行 (雲端部署 - 推薦)

本專案已成功部署至 [Render.com](https://render.com/)，實現了 24/7 全自動在線服務。

1.  **Fork & Clone**: 將此專案的 GitHub 儲存庫 Fork 到您自己的帳號下，並 Clone 到本地。
2.  **建立 LINE Bot**:
    *   前往 [LINE Developers](https://developers.line.biz/zh-hant/) 建立一個 `Messaging API` Channel。
3.  **部署到 Render.com**:
    *   登入 Render Dashboard，建立一個新的 "Web Service"，並連結到您 Fork 的 GitHub 儲存庫。
    *   在設定中，**Runtime** 選擇 **`Docker`**。Render 會自動找到專案中的 `Dockerfile`。
    *   在 **Environment Variables** 中，設定以下所有必要的金鑰：
        *   `USERNAME`: 網站登入帳號
        *   `PASSWORD`: 網站登入密碼
        *   `OPENAI_API_KEY`: 您的 OpenAI 金鑰
        *   `LINE_CHANNEL_SECRET`: 您的 LINE Channel Secret
        *   `LINE_CHANNEL_ACCESS_TOKEN`: 您的 LINE Channel Access Token
        *   `PYTHON_VERSION`: `3.11`
4.  **設定 Webhook**:
    *   部署成功後，Render 會提供一個永久的 `.onrender.com` 網址。
    *   將此網址加上 `/callback` (例如 `https://your-app.onrender.com/callback`)，填入 LINE Developers 後台的 `Webhook URL` 中，並啟用 Webhook。
5.  **開始使用**:
    *   將您的 LINE Bot 加入好友。
    *   傳送符合格式的訊息即可自動發文：
        `發文 標題：[您的標題] 內容：[您的內容]`

---

### 方案三：本地開發與測試

本專案的架構完美支持「本地開發、雲端部署」的流程。您可以在本地進行完整的端到端測試，確保所有功能正常後，再推送到 GitHub 進行自動部署。

**測試流程：**

1.  **啟動 Flask 伺服器**:
    *   開啟第一個終端機。
    *   執行 `python line_bot_server.py`。
    *   伺服器將會運行在 `http://127.0.0.1:5001`。

2.  **啟動 ngrok 隧道**:
    *   保持第一個終端機運行，開啟**第二個**終端機。
    *   執行 `ngrok http 5001`。
    *   `ngrok` 將會提供一個公開的 `https://` 網址。

3.  **設定 LINE Webhook**:
    *   複製 `ngrok` 提供的 `https://` 網址，並在後面加上 `/callback`。
    *   將這個完整的 URL 更新到您 LINE Bot 的 `Webhook URL` 設定中。
    *   **注意**: `ngrok` 的免費版每次重啟，網址都會改變，屆時需要重新更新 Webhook。

4.  **開始測試**:
    *   用您的手機對 LINE Bot 發送指令，即可在本地觸發並觀察完整的自動化流程。

---

這個專案是耐心、觀察和技術結合的最佳典範。恭喜我們，成功了！

---

## 附錄：從本地到雲端 - 史詩級的 Render.com 部署之旅

在成功實現本地自動化後，我們決定將專案推向一個新的高度：實現 24/7 全自動雲端運行。我們選擇了 [Render.com](https://render.com/) 作為我們的部署平台，但這段旅程充滿了挑戰與學習。

### 核心挑戰：在雲端建立一個包含瀏覽器的環境

我們的專案依賴 Selenium 和 Google Chrome，但標準的雲端伺服器預設沒有這些。因此，我們的核心任務是使用 **Docker** 來打造一個客製化的運行環境。

### 我們的除錯與進化之路

1.  **`Exit status 128` (Git 權限問題)**:
    *   **問題**: 在推送程式碼後，Render 在拉取 GitHub 儲存庫的第一步就失敗了。
    *   **原因**: Render 與 GitHub 之間的授權連結，在我們推送了包含 `Dockerfile` 的新設定後失效了。
    *   **解決方案**: 在 Render 儀表板上，對我們的服務**「斷開並重新連結」**GitHub 儲存庫，強制刷新授權。

2.  **`Dockerfile` 的反覆試煉**: 這是我們遇到最多困難的地方，目標是在 Docker 環境中穩定地安裝 Google Chrome 和對應的 ChromeDriver。
    *   **`bsdtar: not found`**: 第一次嘗試的指令使用了一個基礎環境中不存在的工具。**解決方案**: 在 `apt-get install` 中明確加入 `libarchive-tools`。
    *   **`Argument list too long` / `grep` 失敗**: 嘗試動態獲取最新版本號的指令，因過於複雜而在 Docker 的 shell 環境中屢次失敗。
    *   **`404 Not Found`**: 改用寫死的版本號下載，卻發現 Google 已將舊版本的下載連結遷移。
    *   **`jq: error`**: 嘗試用 `jq` 解析官方 JSON 端點，再次因 shell 環境的複雜性而失敗。
    *   **最終方案**: 我們回歸到最簡單、最穩定的方法——在 `Dockerfile` 中**直接寫死一個已知的、完整的 ChromeDriver 下載 URL**，徹底消除了所有不確定性。

3.  **`gunicorn` 啟動失敗**:
    *   **問題**: Docker 映像檔成功建立，但在最後啟動服務時失敗。
    *   **原因**: 我們從未在 `requirements.txt` 中告訴 Render 需要安裝 `gunicorn` 這個 WSGI 伺服器。
    *   **解決方案**: 將 `gunicorn` 加入 `requirements.txt`。

4.  **`401 Unauthorized` (API Key 讀取失敗)**:
    *   **您的關鍵洞察**: 您發現錯誤訊息顯示的是 `config.py` 中的備用金鑰，而不是您在 Render 上設定的環境變數。
    *   **根本原因**: `gunicorn` 啟動時的工作目錄或 Python 搜尋路徑不正確，導致程式載入到舊的或快取中的 `config.py`。
    *   **解決方案**: 修改 `Dockerfile` 的 `CMD` 指令，加入 `--pythonpath /app` 參數，強制 `gunicorn` 使用正確的程式碼路徑。

5.  **使用者體驗優化**:
    *   **統一日誌系統**: 將專案中所有的 `print()` 都升級為 `logging` 模組，確保在 Render 的日誌控制台中能看到完整、清晰且格式一致的執行紀錄。
    *   **即時進度回報**: 放棄了只能使用一次的 `Reply API`，改用功能更強大的 **`Push API`**，在爬蟲執行的各個關鍵階段（如登入成功、發文成功/失敗），主動向您的手機推送即時的進度更新，極大地提升了使用者體驗。

最終，我們克服了所有挑戰，成功地將一個複雜的 Selenium 專案，轉化為一個穩定、可靠、全自動的雲端服務。