# config.py (Corrected)

import os
from selenium.webdriver.common.by import By

"""
這份文件集中管理所有爬蟲的設定值。
當目標網站的結構、URL或需要使用的憑證改變時，
優先修改此文件，而不是去動爬蟲的核心邏輯。
"""

# --- 登錄資訊 (優先從環境變數讀取) ---
LOGIN_URL = "https://www.fq94i.com/webtech"
USERNAME = os.environ.get("USERNAME", "jinny0831")
PASSWORD = os.environ.get("PASSWORD", "uCvMhAK6q")

# --- OpenAI API (優先從環境變數讀取) ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "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")
OPENAI_MODELS_TO_TRY = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]

# --- 爬蟲行為設定 ---
MAX_LOGIN_RETRIES = 5
BROWSER_HEADLESS = True # 在雲端環境中，必須使用無頭模式
DEFAULT_WAIT_TIMEOUT = 15  # 增加預設等待時間以應對較慢的加載
PAGE_LOAD_TIMEOUT = 15
RETRY_DELAY_BASE = 2

# --- 元素定位器 (Locators) - 登錄 ---
# **FIX: Using By constants instead of strings**
USERNAME_FIELD = (By.NAME, "username")
PASSWORD_FIELD = (By.NAME, "userpwd")
CAPTCHA_FIELD = (By.NAME, "checknum")
CAPTCHA_IMAGE_SELECTORS = [
    "img[src*='img.php']", "img[src*='captcha']", "img[src*='verify']",
    "img[src*='code']", "img[alt*='驗證碼']", "img[alt*='captcha']",
    ".captcha img", "#captcha img"
]
SUBMIT_BUTTON_KEYWORDS = ['登', 'login', 'submit', '提交', '確認', 'ok']

# --- 結果檢查關鍵字 ---
LOGIN_SUCCESS_KEYWORDS = ["成功", "歡迎", "welcome", "dashboard", "admin", "system"]
LOGIN_ERROR_KEYWORDS = [
    "驗證碼錯誤", "verification code", "captcha", "驗證失敗",
    "登錄失敗", "login failed", "用戶名或密碼錯誤", "帳號或密碼錯誤"
]

# --- 瀏覽器設定 ---
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# --- Cloudinary API 設定 (優先從環境變數讀取) ---
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "YOUR_CLOUD_NAME")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "YOUR_API_KEY")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "YOUR_API_SECRET")

# ==============================================================================
# --- 文章發布設定 ---
# ==============================================================================

# --- LINE Bot 設定 (優先從環境變數讀取) ---
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "781aaf0501ef15b2a5baf0382f9cccea")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "FlUfHAVLKA2Q5n6Tac8H14vLm1pV/vw/NSJMVwzaLUpbIPOJ6zjaJrF+GQEeZTloMBqtQ+zIqSu9D4LKo/H9gwjQ9gLhUnkDvyWKoDEoqhpoK9PvLegyjygGcHz4PqG0v+EykJ/GcKzoAK5vgt6MfQdB04t89/1O/w1cDnyilFU=")

# --- 發布內容 (此部分未來將由 LINE Bot 動態提供) ---
# POST_TITLE = "hello! world!"
# POST_CONTENT = "This is the content body, also saying hello! world!"

# --- 元素定位器 (Locators) - 文章發布 ---
# **FIX: Using By constants instead of strings**
NAV_MENU_NEWS_LINK = (By.XPATH, "//li[contains(@class, 'haschild')]//a[contains(text(), '最新消息')]")

# "新增文章" 按鈕
ADD_NEW_POST_BUTTON = (By.CSS_SELECTOR, "a.btn.new[href*='#/article-edit']")

# 文章列表的第一行 (用於確認列表已加載，根據用戶提供的 HTML 進行精準定位)
ARTICLE_LIST_TABLE_ROW = (By.CSS_SELECTOR, "div.list-data ul.list-con li.li-data")

# 文章標題輸入框
POST_TITLE_INPUT = (By.CSS_SELECTOR, "div.form-input input[placeholder='輸入文章標題']")

# 主文內容區塊的 "新增" 按鈕
ADD_CONTENT_BLOCK_BUTTON = (By.CSS_SELECTOR, "div.add-style > button.btn.new[title='新增']")

# CKEditor (富文本編輯器) 的 iframe
CKEDITOR_IFRAME = (By.CSS_SELECTOR, "iframe.cke_wysiwyg_frame")

# CKEditor 內容編輯區 (在 iframe 內)
CKEDITOR_BODY = (By.TAG_NAME, "body")

# CKEditor "原始碼" 按鈕
CKEDITOR_SOURCE_BUTTON = (By.CSS_SELECTOR, "a.cke_button__source[title='原始碼']")

# CKEditor "原始碼" 輸入區 (是一個 textarea)
CKEDITOR_SOURCE_TEXTAREA = (By.CSS_SELECTOR, "textarea.cke_source")

# 儲存按鈕 (根據用戶提供的 HTML 進行精準定位，鎖定在底部固定欄位)
SAVE_POST_BUTTON = (By.CSS_SELECTOR, "div#fixed-bottom button.btn.send")

# 發文成功提示訊息 (用於驗證)
# 策略：尋找包含 'el-message' 和 'success' 類別的元素，或任何包含 "成功" 文字的元素
POST_SUCCESS_MESSAGE = (By.XPATH, "//*[contains(@class, 'el-message') and contains(@class, 'success')] | //*[contains(text(), '成功')]")