# line_bot_server.py

import os
import logging
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

# 導入我們的設定和爬蟲
import config
from scraper import SeleniumScraper

# --- 初始化 ---
app = Flask(__name__)

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# LINE Bot 設定
# 在雲端環境中，這些值會從環境變數讀取
# 在本地測試時，如果 config.py 中沒有填寫，則會觸發錯誤
if not config.LINE_CHANNEL_ACCESS_TOKEN or "YOUR_CHANNEL_ACCESS_TOKEN" in config.LINE_CHANNEL_ACCESS_TOKEN:
    logging.warning("LINE_CHANNEL_ACCESS_TOKEN 未設定或為預設值。")
if not config.LINE_CHANNEL_SECRET:
    logging.warning("LINE_CHANNEL_SECRET 未設定。")

configuration = Configuration(access_token=config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)

# --- Webhook 路由 ---
@app.route("/callback", methods=['POST'])
def callback():
    # 獲取 X-Line-Signature 標頭值
    signature = request.headers['X-Line-Signature']

    # 獲取請求主體為文字
    body = request.get_data(as_text=True)
    logging.info("Request body: " + body)

    # 處理 webhook 主體
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logging.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

# --- 訊息處理邏輯 ---
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理文字訊息事件"""
    text = event.message.text.strip()
    user_id = event.source.user_id

    def send_push_message(message_text):
        """一個用來發送 Push Message 的輔助函式"""
        try:
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.push_message(
                    PushMessageRequest(
                        to=user_id,
                        messages=[TextMessage(text=message_text)]
                    )
                )
        except Exception as e:
            logging.error(f"發送 Push Message 失敗: {e}", exc_info=True)
    
    # 檢查是否為發文指令
    if text.startswith("發文"):
        try:
            # 解析指令
            # 格式: 發文 標題：[您的標題] 內容：[您的內容]
            parts = text.split("內容：")
            content = parts[1].strip()
            title = parts[0].replace("發文", "").replace("標題：", "").strip()

            if not title or not content:
                raise ValueError("標題或內容為空")

            # 回覆一個「正在處理」的訊息
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=f"🤖 收到指令！\n標題：{title}\n正在啟動自動化機器人，請稍候...")]
                    )
                )
            
            # --- 執行爬蟲 ---
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
                        send_push_message("😭 遺憾！文章發布流程失敗。請查看 Render 日誌以獲取詳細資訊。")
                else:
                    send_push_message("❌ 登錄失敗，無法發布文章。請查看 Render 日誌以獲取詳細資訊。")

            except Exception as e:
                error_message = f"💥 程序發生未預期的致命錯誤: {e}"
                logging.error(error_message, exc_info=True)
                send_push_message(error_message)
            finally:
                if scraper:
                    scraper.close()

        except (IndexError, ValueError) as e:
            reply_text = f"指令格式錯誤！\n請使用以下格式：\n發文 標題：[您的標題] 內容：[您的內容]\n\n錯誤詳情: {e}"
            logging.error(f"指令解析錯誤: {e}", exc_info=True)
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)]
                    )
                )

# --- 伺服器啟動 ---
if __name__ == "__main__":
    # 注意：在生產環境中，應使用 Gunicorn 或 uWSGI 等 WSGI 伺服器
    app.run(port=5001)