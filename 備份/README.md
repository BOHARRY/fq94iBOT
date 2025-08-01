# 🤖 WebTech 自動化系統

一個功能完整的網站自動登錄和文章發布自動化解決方案，支持AI驗證碼識別、智能重試機制和批量操作。

## ✨ 主要特性

- 🔐 **自動登錄** - 支持複雜登錄流程和驗證碼處理
- 🧠 **AI驗證碼識別** - 集成OpenAI GPT-4V進行驗證碼自動識別
- 🔄 **智能重試機制** - 多層級錯誤處理和自動重試
- 📝 **自動發文** - 支持標題、內容、圖片、分類等完整發布
- 🖼️ **圖片處理** - 自動上傳、壓縮、格式轉換
- 📱 **Line Bot集成** - 可擴展支持Line Bot觸發發文
- 🛡️ **錯誤處理** - 完善的異常處理和日志記錄
- 🏗️ **模塊化設計** - 清晰的代碼結構，易於維護和擴展

## 📦 項目結構

```
webtech_automation/
├── __init__.py              # 包初始化文件
├── config.py               # 配置管理
├── base_scraper.py         # 基礎爬蟲功能
├── auth_manager.py         # 登錄管理
├── captcha_solver.py       # 驗證碼處理
├── article_publisher.py    # 文章發布
├── exceptions.py           # 自定義異常
├── utils.py               # 通用工具函數
├── main.py                # 主程序入口
├── example_usage.py       # 使用示例
├── requirements.txt       # 項目依賴
└── README.md             # 使用說明
```

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 配置設置

編輯 `config.py` 文件，設置你的登錄信息和API密鑰：

```python
# 登錄相關配置
LOGIN_URL = "https://www.fq94i.com/webtech"
USERNAME = "your_username"
PASSWORD = "your_password"

# OpenAI API 配置 (用於驗證碼識別)
OPENAI_API_KEY = "your_openai_api_key"
```

### 3. 基本使用

```python
from webtech_automation import WebTechAutomation

# 創建自動化實例
with WebTechAutomation() as automation:
    # 登錄
    if automation.login():
        print("✅ 登錄成功！")
        
        # 發布文章
        success = automation.publish_article(
            title="測試文章",
            content="這是測試內容",
            images=["path/to/image.jpg"]  # 可選
        )
        
        if success:
            print("🎉 文章發布成功！")
```

## 📖 詳細使用說明

### 登錄功能

#### 基本登錄
```python
from webtech_automation import WebTechAutomation

automation = WebTechAutomation()
success = automation.login()
```

#### 自定義登錄參數
```python
success = automation.login(
    url="https://custom-site.com/login",
    username="custom_user",
    password="custom_pass",
    max_retries=5
)
```

#### 快速登錄
```python
from webtech_automation import quick_login

automation = quick_login(username="user", password="pass")
```

### 文章發布

#### 基本發布
```python
success = automation.publish_article(
    title="文章標題",
    content="文章內容"
)
```

#### 完整發布（包含圖片和分類）
```python
success = automation.publish_article(
    title="完整文章",
    content="詳細內容...",
    images=["image1.jpg", "image2.png"],
    category="技術分享"
)
```

#### 一鍵登錄並發布
```python
success = automation.auto_login_and_publish(
    title="一鍵發布",
    content="自動登錄並發布的文章"
)
```

#### 快速發布
```python
from webtech_automation import quick_publish

success = quick_publish(
    title="快速發布測試",
    content="使用便捷函數發布",
    auto_login=True
)
```

### 批量操作

```python
articles = [
    {"title": "文章1", "content": "內容1"},
    {"title": "文章2", "content": "內容2"},
    {"title": "文章3", "content": "內容3"}
]

with WebTechAutomation() as automation:
    automation.login()
    
    for article in articles:
        success = automation.publish_article(
            title=article["title"],
            content=article["content"]
        )
        time.sleep(5)  # 避免發布過快
```

### Line Bot 消息解析

```python
from webtech_automation import parse_line_message

# Line Bot 收到的消息
message = """#標題: 今日工作總結

完成了以下任務：
1. 系統開發
2. 文檔編寫
3. 功能測試

#分類: 工作日誌
#標籤: 工作, 開發, 測試"""

# 解析消息
parsed = parse_line_message(message)
print(f"標題: {parsed['title']}")
print(f"內容: {parsed['content']}")
print(f"分類: {parsed['category']}")
print(f"標籤: {parsed['tags']}")

# 直接發布
quick_publish(parsed['title'], parsed['content'])
```

## ⚙️ 配置選項

### 基本配置

```python
from webtech_automation.config import config

# 修改配置
config.LOGIN_URL = "https://your-site.com/login"
config.USERNAME = "your_username"
config.PASSWORD = "your_password"
config.OPENAI_API_KEY = "your_api_key"

# 瀏覽器配置
config.HEADLESS = True  # 無頭模式
config.WINDOW_SIZE = (1920, 1080)
config.PAGE_LOAD_TIMEOUT = 30

# 重試配置
config.MAX_LOGIN_RETRIES = 5
config.RETRY_DELAYS = {
    "captcha_error": 2,
    "other_error": 3,
    "max_delay": 15
}
```

### 環境變量配置

```bash
export WEBTECH_LOGIN_URL="https://your-site.com/login"
export WEBTECH_USERNAME="your_username"
export WEBTECH_PASSWORD="your_password"
export OPENAI_API_KEY="your_api_key"
export WEBTECH_HEADLESS="true"
```

## 🔧 進階功能

### 自定義驗證碼處理

```python
from webtech_automation import CaptchaSolver

solver = CaptchaSolver(api_key="your_api_key")

# 手動識別驗證碼
captcha_code = solver.recognize_captcha("captcha_image.png")
print(f"識別結果: {captcha_code}")
```

### 自定義錯誤處理

```python
from webtech_automation.exceptions import LoginError, PublishError

try:
    automation.login()
except LoginError as e:
    print(f"登錄失敗: {e}")
    # 自定義處理邏輯
```

### 添加自定義工具函數

```python
from webtech_automation.utils import log_operation

# 記錄操作日志
log_operation("用戶登錄", True, "登錄成功")
log_operation("文章發布", False, "網絡錯誤")
```

## 🛠️ 開發和擴展

### 添加新功能

1. **繼承基礎類**：
```python
from webtech_automation import BaseScraper

class CustomScraper(BaseScraper):
    def custom_function(self):
        # 你的自定義功能
        pass
```

2. **添加新的發布類型**：
```python
from webtech_automation import ArticlePublisher

class VideoPublisher(ArticlePublisher):
    def publish_video(self, title, video_file):
        # 視頻發布邏輯
        pass
```

### 集成 Line Bot

```python
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from webtech_automation import quick_publish, parse_line_message

app = Flask(__name__)

@app.route("/webhook", methods=['POST'])
def webhook():
    # 接收 Line 消息
    body = request.get_data(as_text=True)
    
    # 解析消息
    parsed = parse_line_message(body)
    
    # 自動發布
    success = quick_publish(
        title=parsed['title'],
        content=parsed['content']
    )
    
    return 'OK'
```

## 📊 監控和日志

### 查看操作日志

系統會自動記錄操作日志到 `webtech_automation.log` 文件：

```
[2025-08-01 17:30:15] 登錄嘗試 - ✅ 成功 - 第1次嘗試成功
[2025-08-01 17:30:45] 文章發布 - ✅ 成功 - 標題: 測試文章
[2025-08-01 17:31:02] 圖片上傳 - ❌ 失敗 - 文件不存在
```

### 截圖文件

系統會自動保存截圖到 `screenshots/` 目錄：

- `login_page_attempt_1.png` - 登錄頁面
- `captcha_area_attempt_1.png` - 驗證碼區域
- `login_result_attempt_1.png` - 登錄結果
- `before_submit.png` - 提交前狀態
- `after_submit.png` - 提交後狀態

## 🐛 故障排除

### 常見問題

1. **登錄失敗**
   - 檢查用戶名和密碼是否正確
   - 確認網站URL是否可訪問
   - 查看截圖文件確認頁面狀態

2. **驗證碼識別失敗**
   - 確認OpenAI API Key是否有效
   - 檢查API額度是否充足
   - 驗證網絡連接是否正常

3. **文章發布失敗**
   - 確認已成功登錄
   - 檢查網站結構是否發生變化
   - 查看錯誤日志了解具體原因

4. **瀏覽器啟動失敗**
   - 安裝或更新Chrome瀏覽器
   - 確認ChromeDriver版本兼容性
   - 檢查系統權限設置

### 調試模式

```python
# 啟用詳細日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 使用可視模式查看操作過程
automation = WebTechAutomation(headless=False)
```

## 📄 API 文檔

### 主要類

#### WebTechAutomation
- `login(url, username, password, max_retries)` - 登錄系統
- `publish_article(title, content, images, category)` - 發布文章
- `auto_login_and_publish(...)` - 一鍵登錄並發布
- `screenshot(filename)` - 截圖當前頁面
- `close()` - 關閉所有資源

#### AuthManager
- `login_with_retry(...)` - 帶重試的登錄
- `is_logged_in()` - 檢查登錄狀態

#### ArticlePublisher  
- `publish_article(...)` - 發布文章
- `_upload_images(image_paths)` - 上傳圖片

#### CaptchaSolver
- `recognize_captcha(image_path)` - 識別驗證碼
- `find_captcha_image(driver)` - 尋找驗證碼圖片

### 工具函數

- `quick_login(username, password, headless)` - 快速登錄
- `quick_publish(title, content, images, auto_login)` - 快速發布
- `parse_line_message(message_text)` - 解析Line消息
- `validate_image_file(file_path)` - 驗證圖片文件
- `resize_image(input_path, output_path, max_size)` - 調整圖片大小

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 項目
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📝 許可證

本項目使用 MIT 許可證 - 查看 [LICENSE](LICENSE) 文件了解詳情。

## 🙏 致謝

- [Selenium](https://selenium.dev/) - Web自動化框架
- [OpenAI](https://openai.com/) - AI驗證碼識別
- [Pillow](https://pillow.readthedocs.io/) - 圖片處理
- [WebDriver Manager](https://github.com/SergeyPirogov/webdriver_manager) - WebDriver管理

## 📞 支持

如果你喜歡這個項目，請給它一個 ⭐！

如有問題或建議，請提交 [Issue](https://github.com/your-repo/webtech-automation/issues)。

---

*用 ❤️ 和 ☕ 製作*