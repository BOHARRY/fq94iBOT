# 功能規格書：LINE Bot 圖文混合發布功能

**作者：** Roo (AI 助理)
**日期：** 2025-08-04

## 1. 專案目標

本文件旨在規劃一個全新的功能模組，允許使用者透過「五餅二魚」LINE Bot，實現包含圖片和文字的混合內容發布。系統將能夠處理使用者在對話中任意時間點、發送任意數量圖片的複雜情境，並最終由 AI 助理將這些資訊整合成一篇包含 HTML 格式的圖文並茂的文章，自動發布到指定的網站後台。

## 2. 核心設計理念：AI 驅動的狀態管理

為了應對使用者非線性的、充滿變化的互動模式（例如：先傳圖、後傳文字；或在對話中途插入圖片），我們將放棄傳統的、由程式碼 `if/else` 決定的僵化流程。

我們的核心設計理念是：**將所有使用者輸入都轉化為對話歷史中的「事實陳述」，然後完全信任 AI 的上下文理解能力來決定下一步的行動。**

後端程式碼只負責執行最單純的任務：
1.  接收輸入 (文字或圖片)。
2.  處理輸入 (上傳圖片至 Cloudinary)。
3.  將處理結果記錄為一個「事實」。
4.  將完整的「事實」列表交給 AI 去做最終決策。

## 3. 技術實作步驟

### 步驟 3.1: 系統設定與環境準備

-   **檔案**：`config.py`, `requirements.txt`
-   **動作**：
    1.  在 `config.py` 中，移除 `IMGUR_CLIENT_ID`，並新增 Cloudinary 所需的三個金鑰：`CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`。所有金鑰都將優先從環境變數讀取。
    2.  在 `requirements.txt` 中，新增 Cloudinary 的官方 Python SDK：`cloudinary`。

### 步驟 3.2: LINE Bot 圖片訊息處理

-   **檔案**：`line_bot_server.py`
-   **動作**：
    1.  **新增圖片處理器**：除了現有的 `TextMessageContent` 處理器，再新增一個 `ImageMessageContent` 處理器 (`handle_image_message`)，專門用來接收使用者傳送的圖片。
    2.  **下載圖片內容**：在 `handle_image_message` 中，使用 `MessagingApiBlob` 的 `get_message_content()` 方法獲取使用者上傳的圖片二進位資料 (`bytearray`)。
    3.  **建立 Cloudinary 上傳模組**：建立一個新的輔助函式 `upload_to_cloudinary(image_bytes)`。此函式將使用 `cloudinary.uploader.upload()` 方法來處理圖片上傳。SDK 會自動處理所有授權和請求細節，我們只需從回傳結果中獲取 `secure_url` 即可。此模組必須包含完整的錯誤處理機制。
    4.  **注入「事實」到對話歷史**：當圖片成功上傳後，系統**不會**立即要求 AI 回覆。而是會將一個結構化的「事實陳述」以使用者身份 (`role: "user"`) 注入到 `conversation_history.json` 中。
        -   **範例**：`{"role": "user", "content": "[系統訊息：使用者已成功上傳一張圖片，網址為 https://i.imgur.com/xxxxxxx.png]"}`
    5.  **引導使用者**：在注入事實後，系統會回覆一則制式但友善的訊息，例如：「✅ 圖片已收到！請繼續告訴我關於這篇文章的細節。」

### 步驟 3.3: AI 提示詞 (Prompt) 升級

-   **檔案**：`line_bot_server.py` (於 `get_ai_response` 函式中)
-   **動作**：這是整個功能的靈魂。我將對 `system_prompt` 進行大幅度修改，賦予 AI 以下新能力：
    1.  **上下文識別**：明確告知 AI，當它在歷史紀錄中看到 `[系統訊息：使用者已成功上傳一張圖片...]` 時，這代表使用者希望將此圖片用於文章中。
    2.  **多圖片處理**：指示 AI，如果看到多條圖片上傳的系統訊息，它需要理解這是一篇多圖文章。
    3.  **HTML 生成能力**：要求 AI 在觸發 `execute_post_article` 工具時，其 `content` 參數**必須**是一段 HTML 字串。
    4.  **條件化 HTML**：
        -   如果上下文中**有**圖片網址，生成的 HTML **必須**包含對應的 `<img>` 標籤。AI 需要自行判斷如何將圖片和文字段落進行排版。
        -   如果上下文中**沒有**任何圖片網址，生成的 HTML 則**不應該**包含 `<img>` 標籤。
    5.  **提供清晰範例**：在 Prompt 中提供一個完整的圖文混合 HTML 範例，以確保 AI 的輸出格式穩定可靠。

### 步驟 3.4: 爬蟲功能升級以支援 HTML 輸入

-   **檔案**：`scraper.py`, `config.py`
-   **動作**：
    1.  **新增定位器**：在 `config.py` 中，根據使用者提供的 HTML 結構，新增 `CKEDITOR_SOURCE_BUTTON` (`a[title='原始碼']`) 和 `CKEDITOR_SOURCE_TEXTAREA` 的定位器。
    2.  **改造發文流程 (`post_new_article`)**：
        -   在現有的「點擊新增按鈕」步驟後，插入新的核心邏輯。
        -   **判斷內容類型**：檢查傳入的 `content` 字串是否包含 HTML 標籤（例如，檢查是否以 `<` 開頭）。
        -   **如果包含 HTML**：
            a.  等待並點擊「原始碼」按鈕。
            b.  等待 `textarea` 元素出現。
            c.  將完整的 HTML `content` 字串一次性 `send_keys` 到 `textarea` 中。
            d.  再次點擊「原始碼」按鈕，切換回視覺化編輯模式，以觸發 CKEditor 的內部狀態更新。
        -   **如果不包含 HTML (純文字)**：
            a.  執行與目前相同的邏輯：切換到 `iframe`，然後對 `<body>` 元素 `send_keys`。
    3.  後續的儲存和驗證步驟保持不變。

## 4. 風險評估與應對

-   **Cloudinary API 限制**：Cloudinary 的免費方案有儲存空間和轉換次數的限制。雖然額度相對寬裕，但若未來用量極大，仍需考慮升級。我們應在 `README.md` 中註明，建議使用者在部署時填寫自己的 Cloudinary 金鑰。
-   **AI 生成 HTML 的穩定性**：這是最大的風險。解決方案是透過在 Prompt 中提供精確的指令和高品質的範例，來最大程度地約束 AI 的輸出行為。
-   **CKEditor 互動的複雜性**：切換「原始碼」模式會引入新的非同步操作。每一步都必須使用穩健的 `WebDriverWait` 顯式等待，確保在與元素互動前，它已經是可見且可點擊的。

---
我已對此功能的實作進行了全面且深入的思考，並將所有細節記錄在此文件中。