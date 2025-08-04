# line_bot_server.py

import os
import logging
import json
import re
import threading
import cloudinary
import cloudinary.uploader
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)

# 導入我們的設定和爬蟲
import config
from scraper import SeleniumScraper

# --- 初始化 ---
app = Flask(__name__)

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# LINE Bot 設定
configuration = Configuration(access_token=config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)

# OpenAI Client
openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

# Cloudinary 設定
cloudinary.config(
  cloud_name = config.CLOUDINARY_CLOUD_NAME,
  api_key = config.CLOUDINARY_API_KEY,
  api_secret = config.CLOUDINARY_API_SECRET,
  secure = True
)

# 對話歷史資料庫
CONVERSATION_HISTORY_FILE = "conversation_history.json"

# --- 輔助函式 ---
def load_history():
    """讀取對話歷史"""
    if os.path.exists(CONVERSATION_HISTORY_FILE):
        with open(CONVERSATION_HISTORY_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_history(history):
    """儲存對話歷史"""
    with open(CONVERSATION_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def upload_to_cloudinary(image_bytes):
    """將圖片上傳到 Cloudinary 並返回安全的 URL"""
    try:
        # 使用 Cloudinary SDK 上傳圖片
        # SDK 會自動處理授權和請求細節
        upload_result = cloudinary.uploader.upload(image_bytes)
        
        # 從回傳結果中獲取安全的 https URL
        secure_url = upload_result.get('secure_url')
        if secure_url:
            logging.info(f"🎉 圖片成功上傳到 Cloudinary: {secure_url}")
            return secure_url
        else:
            logging.error(f"❌ Cloudinary API 回傳結果中未找到 secure_url: {upload_result}")
            return None
    except Exception as e:
        logging.error(f"💥 上傳到 Cloudinary 時發生錯誤: {e}", exc_info=True)
        return None

def get_ai_response(user_id, history):
    """獲取 AI 的回應或工具呼叫"""
    system_prompt = """
    你是一個名為「五餅二魚」的智慧圖文發文助理。你的核心任務是與使用者自然地對話，幫助他們構思、撰寫並最終確認一篇包含文字和圖片的、將要發布到網站上的文章。

    ### 你的能力與規則：

    1.  **識別意圖**: 從對話中，判斷使用者是想「開始寫新文章」、「修改草稿」，還是「確認發文」。
    2.  **識別圖片上下文**: 當你在對話歷史中看到 `[系統訊息：使用者已成功上傳一張圖片，網址為：...]` 這樣的訊息時，你必須知道這就是接下來要發布文章的核心圖片。如果看到多條此類訊息，代表這是一篇多圖文章。
    3.  **生成草稿**: 當使用者提出主題時，為他生成一篇文情並茂的草稿。如果上下文中已有圖片，你的草稿需要自然地將圖片融合進去。
    4.  **理解修改指令**: 當使用者提出修改意見時（例如「把標題改得活潑一點」、「在第二段後面加上剛才那張圖」），你必須理解並生成一篇修改後的新草稿。
    5.  **最終確認**: 在你認為稿件已經完美時，要主動詢問使用者：「請問這份包含 O 張圖片的稿件，可以直接發布了嗎？」（請自行計算圖片數量）。

    ### 關於工具呼叫 (Function Calling)：

    **觸發時機**: 當且僅當使用者明確表示「確認發文」、「可以了，就這樣發吧」或類似的最終同意時，你才可以使用 `execute_post_article` 工具。

    **輸出格式**:
    *   如果需要繼續對話，請直接輸出你的回覆。
    *   如果決定要觸發工具，請**嚴格**按照以下 JSON 格式輸出：
        ```json
        {
          "tool_call": "execute_post_article",
          "parameters": {
            "title": "最終的純文字標題",
            "content": "最終的、包含 HTML 標籤的完整文章內容"
          }
        }
        ```

    ### 關於 `content` 欄位的 HTML 生成規則：

    1.  **必須是 HTML**: `content` 的值**必須**是一段 HTML 字串。
    2.  **處理圖片**:
        *   如果上下文中**有**圖片網址，生成的 HTML **必須**包含對應的 `<img src="..." style="max-width:100%;">` 標籤。你需要根據對話，決定將圖片放在文章的哪個位置。
        *   如果上下文中**沒有**任何圖片網址，生成的 HTML 則**不應該**包含 `<img>` 標籤。
    3.  **基本排版**: 你可以使用 `<p>`, `<strong>`, `<ul>`, `<li>` 等基本標籤來美化文章排版。

    **HTML 範例 (一篇包含兩張圖片的文章):**
    ```html
    <p>這是一個關於寵物倉鼠的有趣故事。</p>
    <p>首先，我們來看看小倉鼠「皮蛋」可愛的模樣。</p>
    <img src="https://i.imgur.com/hamster1.png" alt="可愛的倉鼠皮蛋" style="max-width:100%;">
    <p>皮蛋最喜歡在牠的滾輪上奔跑，就像下面這張圖一樣，充滿活力！</p>
    <img src="https://i.imgur.com/hamster2.png" alt="正在跑滾輪的皮蛋" style="max-width:100%;">
    <p>總而言之，養寵物能為生活帶來許多樂趣。</p>
    ```
    """
    
    messages: list[ChatCompletionMessageParam] = [{"role": "system", "content": system_prompt}]
    user_history = history.get(user_id, [])
    
    # 確保歷史紀錄中的每一項都是正確的格式，並符合型別定義
    for item in user_history:
        if isinstance(item, dict) and "role" in item and "content" in item:
            role = item["role"]
            content = item["content"]
            if role == "user":
                # 明確建立一個 ChatCompletionUserMessageParam
                user_message: ChatCompletionUserMessageParam = {"role": "user", "content": content}
                messages.append(user_message)
            elif role == "assistant":
                # 明確建立一個 ChatCompletionAssistantMessageParam
                assistant_message: ChatCompletionAssistantMessageParam = {"role": "assistant", "content": content}
                messages.append(assistant_message)

    response = openai_client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content

def execute_scraper(user_id, title, content):
    """在背景執行爬蟲並回報結果"""
    scraper = None
    try:
        scraper = SeleniumScraper()
        login_ok = scraper.login_process()
        if login_ok:
            send_push_message(user_id, "✅ 登入成功！正準備發布文章...")
            post_ok = scraper.post_new_article(title=title, content=content)
            if post_ok:
                send_push_message(user_id, "🎉 恭喜！已成功自動發布新文章！")
            else:
                send_push_message(user_id, "😭 遺憾！文章發布流程失敗。")
        else:
            send_push_message(user_id, "❌ 登錄失敗，無法發布文章。")
    except Exception as e:
        error_message = f"💥 程序發生未預期的致命錯誤: {e}"
        logging.error(error_message, exc_info=True)
        send_push_message(user_id, error_message)
    finally:
        if scraper:
            scraper.close()
        # 清除該用戶的對話歷史，開始新的會話
        history = load_history()
        if user_id in history:
            del history[user_id]
            save_history(history)
            logging.info(f"已清除用戶 {user_id} 的對話歷史。")


# --- Webhook 路由 ---
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    logging.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logging.error("Invalid signature.")
        abort(400)
    return 'OK'

# --- 訊息處理邏輯 ---
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    # 讀取並更新對話歷史
    history = load_history()
    if user_id not in history:
        history[user_id] = []
    history[user_id].append({"role": "user", "content": text})

    # 獲取 AI 回應
    ai_response = get_ai_response(user_id, history)
    
    # 預設回覆
    reply_text = "抱歉，AI 沒有提供回應，請稍後再試。"
    assistant_history_content = reply_text

    if ai_response:
        # 使用正則表達式從 AI 回應中提取純淨的 JSON
        json_match = re.search(r"```json\s*({.*?})\s*```", ai_response, re.DOTALL)
        
        if json_match:
            json_string = json_match.group(1)
            try:
                response_json = json.loads(json_string)
                if response_json.get("tool_call") == "execute_post_article":
                    params = response_json.get("parameters", {})
                    title = params.get("title")
                    content = params.get("content")
                    if title and content:
                        logging.info(f"觸發工具呼叫：execute_post_article, 標題: {title}")
                        scraper_thread = threading.Thread(
                            target=execute_scraper,
                            args=(user_id, title, content)
                        )
                        scraper_thread.start()
                        reply_text = "好的，已收到最終確認！我現在就去幫您發布文章，完成後會通知您。🚀"
                        assistant_history_content = ai_response
                    else:
                        reply_text = "AI 決定呼叫工具，但缺少必要的標題或內容。"
                        assistant_history_content = reply_text
                        logging.error(reply_text)
                else:
                    # 如果是 JSON 但不是工具呼叫，直接回覆原始 AI 回應
                    reply_text = ai_response
                    assistant_history_content = ai_response
            except json.JSONDecodeError:
                logging.error(f"無法解析從 AI 回應中提取的 JSON: {json_string}")
                reply_text = "抱歉，AI 回應的格式有誤，我暫時無法處理。"
                assistant_history_content = reply_text
        else:
            # 如果 AI 回應不包含 JSON 區塊，則視為一般對話
            reply_text = ai_response
            assistant_history_content = ai_response

    # 更新對話歷史並儲存
    history[user_id].append({"role": "assistant", "content": assistant_history_content})
    save_history(history)

    # 回覆訊息給使用者
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[
                    TextMessage(
                        text=reply_text,
                        quickReply=None,
                        quoteToken=None
                    )
                ],
                notificationDisabled=False
            )
        )

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    """處理使用者傳送的圖片訊息"""
    user_id = event.source.user_id
    
    # 立即回覆，告知使用者系統正在處理
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[
                    TextMessage(
                        text="收到圖片，正在上傳中，請稍候... 🖼️",
                        quickReply=None,
                        quoteToken=None
                    )
                ],
                notificationDisabled=False
            )
        )

    # 在背景執行緒中處理圖片下載與上傳，避免阻塞
    def process_image_in_background():
        try:
            # 1. 下載圖片
            with ApiClient(configuration) as api_client:
                line_bot_blob_api = MessagingApiBlob(api_client)
                # get_message_content 直接回傳一個 bytearray
                image_bytes = line_bot_blob_api.get_message_content(event.message.id)

            # 2. 上傳到 Cloudinary
            image_url = upload_to_cloudinary(image_bytes)

            # 3. 處理結果
            if image_url:
                # 將成功結果注入對話歷史
                history = load_history()
                if user_id not in history:
                    history[user_id] = []
                
                system_message = f"[系統訊息：使用者已成功上傳一張圖片，網址為 {image_url}]"
                history[user_id].append({"role": "user", "content": system_message})
                save_history(history)
                
                # 推播訊息，引導使用者繼續
                send_push_message(user_id, "✅ 圖片上傳成功！請現在告訴我這篇文章的標題和內容，或者繼續傳送更多圖片。")
            else:
                # 推播失敗訊息
                send_push_message(user_id, "❌ 抱歉，圖片上傳失敗，請稍後再試一次。")

        except Exception as e:
            logging.error(f"處理圖片時發生錯誤: {e}", exc_info=True)
            send_push_message(user_id, "❌ 處理您的圖片時發生未預期的錯誤。")

    # 啟動背景執行緒
    image_thread = threading.Thread(target=process_image_in_background)
    image_thread.start()


def send_push_message(user_id, message_text):
    """一個獨立的 Push Message 函式，方便在背景執行緒中呼叫"""
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[
                        TextMessage(
                            text=message_text,
                            quickReply=None,
                            quoteToken=None
                        )
                    ],
                    notificationDisabled=False,
                    customAggregationUnits=['bot']
                )
            )
    except Exception as e:
        logging.error(f"發送 Push Message 失敗: {e}", exc_info=True)


# --- 伺服器啟動 ---
if __name__ == "__main__":
    app.run(port=5001)