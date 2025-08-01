# 使用官方的 Python 3.11 Slim 版本作為基礎映像
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 更新套件列表並安裝必要的系統依賴
# wget 和 unzip 用於下載和解壓縮 ChromeDriver
# libarchive-tools 提供了 bsdtar 工具
# grep 用於解析版本號
# gnupg, libglib2.0-0, etc. 是 Google Chrome 運行的必要依賴
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libarchive-tools \
    grep \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libatspi2.0-0 \
    libxkbcommon0 \
    libxdmcp6 \
    libxcb1 \
    libgraphite2-3 \
    --no-install-recommends

# 下載並安裝 Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable --no-install-recommends

# 下載並安裝對應版本的 ChromeDriver
# 我們不再使用 webdriver-manager，而是在構建時就固定下來
# 使用更穩定的多階段指令，避免 "Argument list too long" 錯誤
RUN LATEST_STABLE=$(wget -q -O - https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json | grep -oP '"stable": "\K[^"]+') \
    && wget -O /tmp/chromedriver.zip "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${LATEST_STABLE}/linux64/chromedriver-linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /opt/ \
    && mv /opt/chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && rm -rf /opt/chromedriver-linux64 /tmp/chromedriver.zip

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案中的所有其他檔案
COPY . .

# 設定啟動指令
# 使用 gunicorn 來啟動我們的 Flask 應用 (line_bot_server.py 中的 app 物件)
# --bind 0.0.0.0:10000: 讓伺服器監聽 Render 提供的端口
# --timeout 120: 增加超時時間，以應對 Selenium 啟動和運行的耗時
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "line_bot_server:app"]