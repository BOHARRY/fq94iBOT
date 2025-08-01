# scraper.py

import base64
import os
import re
import time
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# 導入我們的設定
import config


class SeleniumScraper:
    """
    一個專門用於處理網站登錄和發文的 Selenium 爬蟲類別。
    它封裝了瀏覽器操作、表單填寫、驗證碼識別和智能重試的所有邏輯。
    """
    def __init__(self, headless=config.BROWSER_HEADLESS, api_key=config.OPENAI_API_KEY):
        """初始化 Selenium WebDriver"""
        logging.info("🔧 初始化爬蟲...")
        self.screenshot_dir = "img"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        logging.info(f"  - 截圖將儲存至 '{self.screenshot_dir}/' 目錄。")
        self.openai_api_key = api_key
        if self.openai_api_key:
            logging.info("  - OpenAI API 已配置，將啟用 AI 驗證碼識別。")
        self.driver = self.setup_driver(headless)
        self.wait = WebDriverWait(self.driver, config.DEFAULT_WAIT_TIMEOUT)

    def setup_driver(self, headless):
        """設置 Chrome WebDriver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f'--user-agent={config.USER_AGENT}')
        
        try:
            # 在 Docker 環境中，我們已經將 chromedriver 放置在固定路徑，不再需要 webdriver-manager
            service = Service(executable_path="/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception:
            logging.warning("   在雲端模式下初始化 WebDriver 失敗，嘗試本地模式...")
            from webdriver_manager.chrome import ChromeDriverManager
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except ImportError:
                logging.error("⚠️ 錯誤: 未安裝 webdriver-manager 且在系統路徑中找不到 chromedriver。")
                logging.error("   請執行 'pip install webdriver-manager'。")
                raise
        
        logging.info("  - WebDriver 設置完成。")
        return driver

    def login_process(self):
        """
        執行完整的登錄流程，包含智能重試機制。
        不再需要傳入參數，因為所有設定都來自 config 模組。
        """
        for attempt in range(1, config.MAX_LOGIN_RETRIES + 1):
            logging.info(f"🚀 登錄嘗試 #{attempt}/{config.MAX_LOGIN_RETRIES}")
            
            try:
                # 導航至頁面或刷新
                if attempt == 1:
                    self._navigate_to_login_page()
                else:
                    self._refresh_page()
                
                self.screenshot_full_page(f"login_page_attempt_{attempt}.png")

                # 查找並處理驗證碼
                captcha_img = self._find_captcha_image()
                if not captcha_img:
                    logging.warning("⚠️ 未找到驗證碼圖片，流程可能出錯。")
                
                # 填寫表單
                username_field = self.wait.until(EC.presence_of_element_located(config.USERNAME_FIELD))
                password_field = self.driver.find_element(*config.PASSWORD_FIELD)
                captcha_field = self.driver.find_element(*config.CAPTCHA_FIELD)

                username_field.clear()
                username_field.send_keys(config.USERNAME)
                password_field.clear()
                password_field.send_keys(config.PASSWORD)
                logging.info("✅ 已填入用戶名和密碼。")

                # 獲取驗證碼
                captcha_code = self._get_captcha_code(attempt, captcha_img)
                if not captcha_code:
                    if attempt < config.MAX_LOGIN_RETRIES:
                        logging.error("❌ 未能獲取驗證碼，準備重試...")
                        time.sleep(config.RETRY_DELAY_BASE)
                        continue
                    else:
                        logging.error("💥 未能獲取驗證碼，且已達最大重試次數。")
                        return False

                captcha_field.clear()
                captcha_field.send_keys(captcha_code)
                logging.info(f"✅ 驗證碼已填入: {captcha_code}")
                
                # 提交並檢查結果
                if self._submit_and_check(attempt):
                    return True # 登錄成功

            except Exception as e:
                logging.error(f"❌ 登錄嘗試 #{attempt} 發生嚴重錯誤: {e}", exc_info=True)
                self.screenshot_full_page(f"error_attempt_{attempt}.png")

            # 如果未成功，且不是最後一次嘗試，則等待後重試
            if attempt < config.MAX_LOGIN_RETRIES:
                delay = config.RETRY_DELAY_BASE * attempt
                logging.info(f"⏳ 等待 {delay} 秒後重試...")
                time.sleep(delay)
        
        logging.error("💥 所有登錄嘗試均失敗。")
        return False

    def post_new_article(self, title: str, content: str):
        """
        執行自動發布新文章的完整流程。
        
        :param title: 要發布的文章標題
        :param content: 要發布的文章內容
        """
        try:
            logging.info("✍️ 開始執行自動發文流程")

            # 步驟 1: 點擊 "最新消息" 導航連結
            logging.info("1. 導航至 '最新消息' 頁面...")
            news_link = self.wait.until(
                EC.element_to_be_clickable(config.NAV_MENU_NEWS_LINK)
            )
            news_link.click()
            logging.info("   ✅ 已點擊 '最新消息'。")

            # 新增步驟 1.5: 等待文章列表完全加載 (包含重試機制)
            logging.info("1.5. 等待文章列表加載完成...")
            list_loaded = False
            for i in range(3): # 最多重試 3 次
                try:
                    self.wait.until(
                        EC.presence_of_element_located(config.ARTICLE_LIST_TABLE_ROW)
                    )
                    logging.info(f"   ✅ 文章列表已加載 (嘗試 #{i+1})。")
                    list_loaded = True
                    break # 成功後跳出迴圈
                except TimeoutException:
                    logging.warning(f"   ⚠️ 警告：未檢測到文章列表 (嘗試 #{i+1}/3)，正在刷新頁面重試...")
                    self.driver.refresh()
                    time.sleep(3) # 刷新後等待
            
            if not list_loaded:
                logging.error("   ❌ 錯誤：刷新重試多次後，仍無法加載文章列表。")
                self.screenshot_full_page("list_load_error.png")
                return False

            logging.info("   ⏳ 強制等待 5 秒以確保所有組件穩定...")
            time.sleep(5)

            # 步驟 2: 直接導航至文章編輯頁面
            logging.info("2. 正在獲取目標 URL 並直接導航至文章編輯頁面...")
            add_button = self.wait.until(
                EC.presence_of_element_located(config.ADD_NEW_POST_BUTTON)
            )
            target_url = add_button.get_attribute('href')
            if target_url:
                logging.info(f"   - 獲取到目標 URL: {target_url}")
                self.driver.get(target_url)
                logging.info("   ✅ 已導航至文章編輯頁面。")
            else:
                logging.error("   ❌ 錯誤：未能從 '新增文章' 按鈕獲取有效的 URL。")
                self.screenshot_full_page("post_error_page.png")
                return False
            
            # 等待編輯器頁面加載完成
            time.sleep(2) # 這裡可以保留一個短暫的sleep，因為頁面跳轉後組件可能需要時間初始化

            # 步驟 3: 輸入文章標題
            logging.info(f"3. 輸入文章標題: '{title}'")
            title_input = self.wait.until(
                EC.visibility_of_element_located(config.POST_TITLE_INPUT)
            )
            # 模擬更真實的用戶輸入，以觸發 JavaScript 事件
            title_input.click()
            title_input.clear()
            title_input.send_keys(title)
            # 點擊頁面 body 來觸發 onblur 事件，這比按 TAB 更安全，可避免焦點跳轉到非預期元素
            self.driver.find_element(By.TAG_NAME, "body").click()
            logging.info("   ✅ 標題輸入完成。")

            # 新增步驟: 點擊 "新增" 按鈕來顯示主文編輯器
            logging.info("3.5. 點擊 '新增' 按鈕以載入主文編輯器...")
            add_content_button = self.wait.until(
                EC.element_to_be_clickable(config.ADD_CONTENT_BLOCK_BUTTON)
            )
            add_content_button.click()
            logging.info("   ✅ 已點擊 '新增' 按鈕。")
            time.sleep(1) # 等待一下讓編輯器 iframe 載入

            # 步驟 4: 處理富文本編輯器 (CKEditor)
            logging.info(f"4. 在編輯器中輸入內容: '{content}'")
            self.wait.until(
                EC.frame_to_be_available_and_switch_to_it(config.CKEDITOR_IFRAME)
            )
            editor_body = self.wait.until(
                EC.element_to_be_clickable(config.CKEDITOR_BODY)
            )
            editor_body.send_keys(content)
            self.driver.switch_to.default_content()
            logging.info("   ✅ 內容輸入完成。")

            # 新增步驟: 強制同步 CKEditor 內容到其對應的 textarea
            try:
                logging.info("4.5. 同步編輯器內容...")
                self.driver.execute_script("for(var instance in CKEDITOR.instances) { CKEDITOR.instances[instance].updateElement(); }")
                logging.info("   ✅ 編輯器內容已同步。")
                time.sleep(0.5) # 同步後短暫等待
            except Exception as js_error:
                logging.warning(f"  - 警告：同步 CKEditor 內容時發生錯誤: {js_error}")
            
            self.screenshot_full_page("before_saving_post.png")

            # 步驟 5: 點擊 "儲存" 按鈕
            logging.info("5. 點擊 '儲存' 按鈕...")
            attempts = 0
            while attempts < 3:
                try:
                    # 使用精準定位器找到儲存按鈕
                    save_button = self.wait.until(
                        EC.presence_of_element_located(config.SAVE_POST_BUTTON)
                    )
                    # 使用 JavaScript 點擊，這是最穩定的方法，可以繞過大部分的遮擋問題
                    self.driver.execute_script("arguments[0].click();", save_button)
                    logging.info("   ✅ 已透過 JavaScript 點擊儲存。")
                    break  # 成功後跳出循環
                except (StaleElementReferenceException, ElementClickInterceptedException) as e:
                    attempts += 1
                    logging.warning(f"  - 警告：點擊儲存按鈕時發生錯誤 ({type(e).__name__})，正在重試 ({attempts}/3)...")
                    time.sleep(1)  # 等待 DOM 穩定
                    if attempts == 3:
                        logging.error("  - ❌ 錯誤：重試多次後，儲存按鈕仍然無法點擊。")
                        raise  # 重新引發最後的異常

            # 步驟 6: 驗證發文是否成功
            logging.info("6. 驗證發文結果...")
            try:
                # 等待成功訊息出現
                self.wait.until(
                    EC.visibility_of_element_located(config.POST_SUCCESS_MESSAGE)
                )
                logging.info("   ✅ 偵測到成功訊息！發文確認成功。")
                self.screenshot_full_page("after_saving_post.png")
                return True
            except TimeoutException:
                # 如果在等待時間內沒有出現成功訊息，則判定為失敗
                logging.error("   ❌ 未能偵測到成功訊息，發文可能失敗。")
                self.screenshot_full_page("post_error_page.png")
                return False

        except TimeoutException as e:
            # 這個 Timeout 是指在操作過程中（點擊按鈕前）找不到元素
            logging.error(f"❌ 發文流程超時失敗：在執行操作前找不到指定元素。")
            logging.error(f"   當前 URL: {self.driver.current_url}")
            logging.error(f"   錯誤詳情: {e}", exc_info=True)
            self.screenshot_full_page("post_error_page.png")
            return False
        except Exception as e:
            logging.error(f"❌ 發文流程發生未知錯誤: {e}", exc_info=True)
            self.screenshot_full_page("post_error_page.png")
            return False

    def _navigate_to_login_page(self):
        logging.info(f"🌐 正在打開頁面: {config.LOGIN_URL}")
        self.driver.get(config.LOGIN_URL)
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(3) # 額外等待以確保JS渲染完成
        logging.info(f"✅ 頁面加載完成: {self.driver.title}")

    def _refresh_page(self):
        logging.info("🔄 刷新頁面以獲取新驗證碼...")
        self.driver.refresh()
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(3)
        logging.info("✅ 頁面刷新完成。")

    def _find_captcha_image(self):
        """使用 config 中的選擇器列表尋找驗證碼圖片。"""
        logging.info("🔍 正在查找驗證碼圖片...")
        for selector in config.CAPTCHA_IMAGE_SELECTORS:
            try:
                # 使用 CSS_SELECTOR，因為列表中的大部分都是 CSS 選擇器
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logging.info(f"  - 找到驗證碼圖片 (使用選擇器: {selector})")
                    return elements[0]
            except:
                continue
        return None

    def _get_captcha_code(self, attempt, captcha_img_element):
        """獲取驗證碼，優先使用AI識別，失敗則提示手動輸入。"""
        if not self.openai_api_key or not captcha_img_element:
            return input(f"\n[手動模式] 請查看截圖 img/login_page_attempt_{attempt}.png 並輸入驗證碼: ").strip()

        logging.info("🤖 正在使用 AI 識別驗證碼...")
        captcha_filename = f"captcha_attempt_{attempt}.png"
        captcha_path = os.path.join(self.screenshot_dir, captcha_filename)
        self.screenshot_element(captcha_img_element, captcha_filename)
        
        captcha_code = self._recognize_captcha_with_openai(captcha_path)
        if captcha_code and 3 <= len(captcha_code) <= 8:
            logging.info(f"  - AI 識別成功: {captcha_code}")
            return captcha_code
        
        logging.error("  - ❌ AI 識別失敗或結果不佳。")
        if attempt == 1: # 只在第一次嘗試時要求手動輸入
            return input(f"\n[手動備用] AI識別失敗，請查看截圖 {captcha_path} 並手動輸入驗證碼: ").strip()
        
        return None

    def _recognize_captcha_with_openai(self, image_path):
        """使用最新版 OpenAI API 識別驗證碼。"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            base64_image = self._encode_image_to_base64(image_path)
            if not base64_image: return None

            for model in config.OPENAI_MODELS_TO_TRY:
                try:
                    logging.info(f"  - 嘗試模型: {model}...")
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "user", "content": [
                                {"type": "text", "text": "What's in this image? Identify the letters and numbers. Respond only with the identified text."},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                            ]}
                        ],
                        max_tokens=50, temperature=0.1
                    )
                    content = response.choices[0].message.content
                    if content is None:
                        continue
                    captcha_text = content.strip()
                    clean_text = re.sub(r'[^a-zA-Z0-9]', '', captcha_text)
                    if clean_text:
                        return clean_text
                except Exception as model_error:
                    logging.warning(f"    - 模型 {model} 調用失敗: {model_error}")
            return None
        except Exception as e:
            logging.error(f"  - ❌ OpenAI API 調用失敗: {e}", exc_info=True)
            return None

    def _submit_and_check(self, attempt):
        """提交表單並檢查登錄結果，返回 True 表示成功。"""
        logging.info("🚀 正在提交表單...")
        if not self._try_submit_form():
            logging.error("❌ 表單提交失敗。")
            return False
        
        time.sleep(3) # 等待頁面響應
        self.screenshot_full_page(f"login_result_attempt_{attempt}.png")

        result_status = self._check_login_result()
        if result_status == "success":
            logging.info(f"🎉 登錄成功！(嘗試 #{attempt})")
            return True
        elif result_status == "captcha_error":
            logging.warning(f"❌ 驗證碼錯誤 (嘗試 #{attempt})。")
        else:
            logging.warning(f"❌ 登錄失敗，原因未知或為其他錯誤 (嘗試 #{attempt})。")
        return False

    def _try_submit_form(self):
        """嘗試多種方式提交表單，提高成功率。"""
        # 策略組合：CSS 選擇器和 XPath
        strategies = {
            By.CSS_SELECTOR: ["input[type='submit']", "button[type='submit']"],
            By.XPATH: [f"//button[contains(text(), '{kw}')] | //input[contains(@value, '{kw}')]" for kw in config.SUBMIT_BUTTON_KEYWORDS]
        }

        for by_method, selectors in strategies.items():
            for selector in selectors:
                try:
                    buttons = self.driver.find_elements(by_method, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            logging.info(f"  - 找到提交按鈕，正在點擊... (策略: {by_method}, {selector})")
                            button.click()
                            return True
                except:
                    continue

        # 方式2: 直接提交表單
        try:
            logging.info("  - 未找到明確按鈕，嘗試直接提交 form 標籤...")
            form = self.driver.find_element(By.TAG_NAME, "form")
            form.submit()
            return True
        except:
            pass

        # 方式3: 在驗證碼欄位按 Enter
        try:
            logging.info("  - 最後嘗試，在驗證碼欄位按 Enter...")
            captcha_field = self.driver.find_element(*config.CAPTCHA_FIELD)
            captcha_field.send_keys(Keys.RETURN)
            return True
        except Exception as e:
            logging.error(f"  - 所有提交方式均失敗: {e}", exc_info=True)
            return False

    def _check_login_result(self):
        """檢查登錄結果。"""
        current_url = self.driver.current_url
        page_source = self.driver.page_source.lower()
        logging.info(f"📍 檢查結果: 當前 URL: {current_url}")

        # 檢查是否有明確的錯誤信息
        for keyword in config.LOGIN_ERROR_KEYWORDS:
            if keyword in page_source:
                logging.warning(f"  - 發現錯誤關鍵字: '{keyword}'")
                return "captcha_error" if "驗證" in keyword or "captcha" in keyword else "other_error"

        # 檢查是否有成功的跡象
        if config.LOGIN_URL not in current_url:
            logging.info("  - URL已改變，判定為登錄成功。")
            return "success"
        for keyword in config.LOGIN_SUCCESS_KEYWORDS:
            if keyword in page_source:
                logging.info(f"  - 發現成功關鍵字: '{keyword}'")
                return "success"

        logging.warning("  - 未能明確判斷登錄狀態，可能失敗。")
        return "unknown"

    def _encode_image_to_base64(self, image_path):
        """將圖片編碼為 base64。"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logging.error(f"❌ 編碼圖片失敗: {e}", exc_info=True)
            return None

    def screenshot_element(self, element, filename):
        """截圖特定元素。"""
        try:
            filepath = os.path.join(self.screenshot_dir, filename)
            element.screenshot(filepath)
            logging.info(f"  - 元素截圖已保存: {filepath}")
        except Exception as e:
            logging.error(f"  - ❌ 元素截圖失敗: {e}", exc_info=True)

    def screenshot_full_page(self, filename):
        """截圖整個頁面。"""
        try:
            filepath = os.path.join(self.screenshot_dir, filename)
            self.driver.save_screenshot(filepath)
            logging.info(f"📸 頁面截圖已保存: {filepath}")
        except Exception as e:
            logging.error(f"  - ❌ 頁面截圖失敗: {e}", exc_info=True)

    def close(self):
        """安全地關閉瀏覽器。"""
        logging.info("🔒 正在關閉瀏覽器...")
        self.driver.quit()