# line_bot_server.py

import os
import logging
import json
import re
import threading
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
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

def get_ai_response(user_id, history):
    """獲取 AI 的回應或工具呼叫"""
    system_prompt = """
    你是一個名為「五餅二魚」的智慧發文助理。你的任務是與使用者自然地對話，幫助他們構思、撰寫並最終確認一篇要發布到網站上的文章。

    你的能力與規則如下：
    1.  **識別意圖**: 從對話中，判斷使用者是想「開始寫新文章」、「修改草稿」，還是「確認發文」。
    2.  **生成草稿**: 當使用者提出主題時，為他生成一篇文情並茂的草稿。
    3.  **理解修改指令**: 當使用者提出修改意見時（例如「把標題改得活潑一點」、「內容第三段可以多加一些細節」），你必須理解並生成一篇修改後的新草稿。
    4.  **最終確認**: 在你認為草稿已經完美時，要主動詢問使用者：「請問這份最終的稿件可以直接發布了嗎？」
    5.  **觸發工具 (Function Calling)**: 當且僅當使用者明確表示「確認發文」、「可以了，就這樣發吧」或類似的最終同意時，你必須呼叫一個名為 `execute_post_article` 的工具，並將最終確認的**標題**和**內容**作為參數傳遞給它。在其他任何情況下，你都只能與使用者對話。

    輸出格式：
    *   如果需要繼續對話，請直接輸出你的回覆。
    *   如果決定要觸發工具，請嚴格按照以下 JSON 格式輸出：
        ```json
        {
          "tool_call": "execute_post_article",
          "parameters": {
            "title": "最終的標題",
            "content": "最終的內容"
          }
        }
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
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content

def execute_scraper(user_id, title, content):
    """在背景執行爬蟲並回報結果"""
    def send_push_message(message_text):
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
                        customAggregationUnits='bot'
                    )
                )
        except Exception as e:
            logging.error(f"發送 Push Message 失敗: {e}", exc_info=True)

    scraper = None
    try:
        scraper = SeleniumScraper()
        login_ok = scraper.login_process()
        if login_ok:
            send_push_message("✅ 登入成功！正準備發布文章...")
            post_ok = scraper.post_new_article(title=title, content=content)
            if post_ok:
                send_push_message("🎉 恭喜！已成功自動發布新文章！")
            else:
                send_push_message("😭 遺憾！文章發布流程失敗。")
        else:
            send_push_message("❌ 登錄失敗，無法發布文章。")
    except Exception as e:
        error_message = f"💥 程序發生未預期的致命錯誤: {e}"
        logging.error(error_message, exc_info=True)
        send_push_message(error_message)
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

# --- 伺服器啟動 ---
if __name__ == "__main__":
    app.run(port=5001)