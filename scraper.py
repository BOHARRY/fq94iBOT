# scraper.py

import base64
import os
import re
import time

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
        print("🔧 初始化爬蟲...")
        self.screenshot_dir = "img"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        print(f"  - 截圖將儲存至 '{self.screenshot_dir}/' 目錄。")
        self.openai_api_key = api_key
        if self.openai_api_key:
            print("  - OpenAI API 已配置，將啟用 AI 驗證碼識別。")
        self.driver = self.setup_driver(headless)
        self.wait = WebDriverWait(self.driver, config.DEFAULT_WAIT_TIMEOUT)

    def setup_driver(self, headless):
        """設置 Chrome WebDriver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent={config.USER_AGENT}')
        
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except ImportError:
            print("⚠️ 警告: 未安裝 webdriver-manager。請執行 'pip install webdriver-manager' 以自動管理 ChromeDriver。")
            print("   正在嘗試使用系統路徑中的 chromedriver...")
            driver = webdriver.Chrome(options=chrome_options)
        
        print("  - WebDriver 設置完成。")
        return driver

    def login_process(self):
        """
        執行完整的登錄流程，包含智能重試機制。
        不再需要傳入參數，因為所有設定都來自 config 模組。
        """
        for attempt in range(1, config.MAX_LOGIN_RETRIES + 1):
            print(f"\n{'='*50}\n🚀 登錄嘗試 #{attempt}/{config.MAX_LOGIN_RETRIES}\n{'='*50}")
            
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
                    print("⚠️ 未找到驗證碼圖片，流程可能出錯。")
                
                # 填寫表單
                username_field = self.wait.until(EC.presence_of_element_located((By.NAME, config.USERNAME_FIELD[1])))
                password_field = self.driver.find_element(By.NAME, config.PASSWORD_FIELD[1])
                captcha_field = self.driver.find_element(By.NAME, config.CAPTCHA_FIELD[1])

                username_field.clear()
                username_field.send_keys(config.USERNAME)
                password_field.clear()
                password_field.send_keys(config.PASSWORD)
                print("✅ 已填入用戶名和密碼。")

                # 獲取驗證碼
                captcha_code = self._get_captcha_code(attempt, captcha_img)
                if not captcha_code:
                    if attempt < config.MAX_LOGIN_RETRIES:
                        print("❌ 未能獲取驗證碼，準備重試...")
                        time.sleep(config.RETRY_DELAY_BASE)
                        continue
                    else:
                        print("💥 未能獲取驗證碼，且已達最大重試次數。")
                        return False

                captcha_field.clear()
                captcha_field.send_keys(captcha_code)
                print(f"✅ 驗證碼已填入: {captcha_code}")
                
                # 提交並檢查結果
                if self._submit_and_check(attempt):
                    return True # 登錄成功

            except Exception as e:
                print(f"❌ 登錄嘗試 #{attempt} 發生嚴重錯誤: {e}")
                self.screenshot_full_page(f"error_attempt_{attempt}.png")

            # 如果未成功，且不是最後一次嘗試，則等待後重試
            if attempt < config.MAX_LOGIN_RETRIES:
                delay = config.RETRY_DELAY_BASE * attempt
                print(f"⏳ 等待 {delay} 秒後重試...")
                time.sleep(delay)
        
        print("\n💥 所有登錄嘗試均失敗。")
        return False

    def post_new_article(self, title: str, content: str):
        """
        執行自動發布新文章的完整流程。
        
        :param title: 要發布的文章標題
        :param content: 要發布的文章內容
        """
        try:
            print(f"\n{'='*50}\n✍️ 開始執行自動發文流程\n{'='*50}")

            # 步驟 1: 點擊 "最新消息" 導航連結
            print("1. 導航至 '最新消息' 頁面...")
            news_link = self.wait.until(
                EC.element_to_be_clickable(config.NAV_MENU_NEWS_LINK)
            )
            news_link.click()
            print("   ✅ 已點擊 '最新消息'。")

            # 新增步驟 1.5: 等待文章列表完全加載
            # 這是為了解決按鈕先出現，但頁面數據流尚未準備好的問題
            print("1.5. 等待文章列表加載完成...")
            try:
                self.wait.until(
                    EC.presence_of_element_located(config.ARTICLE_LIST_TABLE_ROW)
                )
                print("   ✅ 文章列表已加載。")
                print("   ⏳ 根據要求，強制等待 5 秒以確保所有組件穩定...")
                time.sleep(5)
            except TimeoutException:
                print("   ⚠️ 警告：未檢測到文章列表，但仍將繼續嘗試。可能是頁面沒有文章。")

            # 步驟 2: 直接導航至文章編輯頁面
            # 根據用戶反饋，點擊按鈕的過程可能觸發非預期的副作用，
            # 因此改為直接獲取目標 URL 並導航，這是更穩定的方法。
            print("2. 正在獲取目標 URL 並直接導航至文章編輯頁面...")
            add_button = self.wait.until(
                EC.presence_of_element_located(config.ADD_NEW_POST_BUTTON)
            )
            target_url = add_button.get_attribute('href')
            if target_url:
                print(f"   - 獲取到目標 URL: {target_url}")
                self.driver.get(target_url)
                print("   ✅ 已導航至文章編輯頁面。")
            else:
                print("   ❌ 錯誤：未能從 '新增文章' 按鈕獲取有效的 URL。")
                self.screenshot_full_page("post_error_page.png")
                return False
            
            # 等待編輯器頁面加載完成
            time.sleep(2) # 這裡可以保留一個短暫的sleep，因為頁面跳轉後組件可能需要時間初始化

            # 步驟 3: 輸入文章標題
            print(f"3. 輸入文章標題: '{title}'")
            title_input = self.wait.until(
                EC.visibility_of_element_located(config.POST_TITLE_INPUT)
            )
            # 模擬更真實的用戶輸入，以觸發 JavaScript 事件
            title_input.click()
            title_input.clear()
            title_input.send_keys(title)
            # 點擊頁面 body 來觸發 onblur 事件，這比按 TAB 更安全，可避免焦點跳轉到非預期元素
            self.driver.find_element(By.TAG_NAME, "body").click()
            print("   ✅ 標題輸入完成。")

            # 新增步驟: 點擊 "新增" 按鈕來顯示主文編輯器
            print("3.5. 點擊 '新增' 按鈕以載入主文編輯器...")
            add_content_button = self.wait.until(
                EC.element_to_be_clickable(config.ADD_CONTENT_BLOCK_BUTTON)
            )
            add_content_button.click()
            print("   ✅ 已點擊 '新增' 按鈕。")
            time.sleep(1) # 等待一下讓編輯器 iframe 載入

            # 步驟 4: 處理富文本編輯器 (CKEditor)
            print(f"4. 在編輯器中輸入內容: '{content}'")
            self.wait.until(
                EC.frame_to_be_available_and_switch_to_it(config.CKEDITOR_IFRAME)
            )
            editor_body = self.wait.until(
                EC.element_to_be_clickable(config.CKEDITOR_BODY)
            )
            editor_body.send_keys(content)
            self.driver.switch_to.default_content()
            print("   ✅ 內容輸入完成。")

            # 新增步驟: 強制同步 CKEditor 內容到其對應的 textarea
            # 這是為了確保表單提交時能獲取到最新的編輯器內容
            try:
                print("4.5. 同步編輯器內容...")
                self.driver.execute_script("for(var instance in CKEDITOR.instances) { CKEDITOR.instances[instance].updateElement(); }")
                print("   ✅ 編輯器內容已同步。")
                time.sleep(0.5) # 同步後短暫等待
            except Exception as js_error:
                print(f"  - 警告：同步 CKEditor 內容時發生錯誤: {js_error}")
            
            self.screenshot_full_page("before_saving_post.png")

            # 步驟 5: 點擊 "儲存" 按鈕
            print("5. 點擊 '儲存' 按鈕...")
            # 增加重試機制來處理 StaleElementReferenceException 和 ElementClickInterceptedException
            # 這通常發生在 DOM 元素被刷新或被其他元素遮擋（抖動）時
            attempts = 0
            while attempts < 3:
                try:
                    # 使用精準定位器找到儲存按鈕
                    save_button = self.wait.until(
                        EC.presence_of_element_located(config.SAVE_POST_BUTTON)
                    )
                    # 使用 JavaScript 點擊，這是最穩定的方法，可以繞過大部分的遮擋問題
                    self.driver.execute_script("arguments[0].click();", save_button)
                    print("   ✅ 已透過 JavaScript 點擊儲存。")
                    break  # 成功後跳出循環
                except (StaleElementReferenceException, ElementClickInterceptedException) as e:
                    attempts += 1
                    print(f"  - 警告：點擊儲存按鈕時發生錯誤 ({type(e).__name__})，正在重試 ({attempts}/3)...")
                    time.sleep(1)  # 等待 DOM 穩定
                    if attempts == 3:
                        print("  - ❌ 錯誤：重試多次後，儲存按鈕仍然無法點擊。")
                        raise  # 重新引發最後的異常

            # 步驟 6: 驗證發文是否成功
            print("6. 驗證發文結果...")
            try:
                # 等待成功訊息出現
                self.wait.until(
                    EC.visibility_of_element_located(config.POST_SUCCESS_MESSAGE)
                )
                print("   ✅ 偵測到成功訊息！發文確認成功。")
                self.screenshot_full_page("after_saving_post.png")
                return True
            except TimeoutException:
                # 如果在等待時間內沒有出現成功訊息，則判定為失敗
                print("   ❌ 未能偵測到成功訊息，發文可能失敗。")
                self.screenshot_full_page("post_error_page.png")
                return False

        except TimeoutException as e:
            # 這個 Timeout 是指在操作過程中（點擊按鈕前）找不到元素
            print(f"❌ 發文流程超時失敗：在執行操作前找不到指定元素。")
            print(f"   當前 URL: {self.driver.current_url}")
            print(f"   錯誤詳情: {e}")
            self.screenshot_full_page("post_error_page.png")
            return False
        except Exception as e:
            print(f"❌ 發文流程發生未知錯誤: {e}")
            self.screenshot_full_page("post_error_page.png")
            return False

    def _navigate_to_login_page(self):
        print(f"🌐 正在打開頁面: {config.LOGIN_URL}")
        self.driver.get(config.LOGIN_URL)
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(3) # 額外等待以確保JS渲染完成
        print(f"✅ 頁面加載完成: {self.driver.title}")

    def _refresh_page(self):
        print("🔄 刷新頁面以獲取新驗證碼...")
        self.driver.refresh()
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(3)
        print("✅ 頁面刷新完成。")

    def _find_captcha_image(self):
        """使用 config 中的選擇器列表尋找驗證碼圖片。"""
        print("🔍 正在查找驗證碼圖片...")
        for selector in config.CAPTCHA_IMAGE_SELECTORS:
            try:
                # 使用 CSS_SELECTOR，因為列表中的大部分都是 CSS 選擇器
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"  - 找到驗證碼圖片 (使用選擇器: {selector})")
                    return elements[0]
            except:
                continue
        return None

    def _get_captcha_code(self, attempt, captcha_img_element):
        """獲取驗證碼，優先使用AI識別，失敗則提示手動輸入。"""
        if not self.openai_api_key or not captcha_img_element:
            return input(f"\n[手動模式] 請查看截圖 login_page_attempt_{attempt}.png 並輸入驗證碼: ").strip()

        print("🤖 正在使用 AI 識別驗證碼...")
        captcha_filename = f"captcha_attempt_{attempt}.png"
        captcha_path = os.path.join(self.screenshot_dir, captcha_filename)
        self.screenshot_element(captcha_img_element, captcha_filename)
        
        captcha_code = self._recognize_captcha_with_openai(captcha_path)
        if captcha_code and 3 <= len(captcha_code) <= 8:
            print(f"  - AI 識別成功: {captcha_code}")
            return captcha_code
        
        print("  - ❌ AI 識別失敗或結果不佳。")
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
                    print(f"  - 嘗試模型: {model}...")
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
                    print(f"    - 模型 {model} 調用失敗: {model_error}")
            return None
        except Exception as e:
            print(f"  - ❌ OpenAI API 調用失敗: {e}")
            return None

    def _submit_and_check(self, attempt):
        """提交表單並檢查登錄結果，返回 True 表示成功。"""
        print("🚀 正在提交表單...")
        if not self._try_submit_form():
            print("❌ 表單提交失敗。")
            return False
        
        time.sleep(3) # 等待頁面響應
        self.screenshot_full_page(f"login_result_attempt_{attempt}.png")

        result_status = self._check_login_result()
        if result_status == "success":
            print(f"🎉 登錄成功！(嘗試 #{attempt})")
            return True
        elif result_status == "captcha_error":
            print(f"❌ 驗證碼錯誤 (嘗試 #{attempt})。")
        else:
            print(f"❌ 登錄失敗，原因未知或為其他錯誤 (嘗試 #{attempt})。")
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
                            print(f"  - 找到提交按鈕，正在點擊... (策略: {by_method}, {selector})")
                            button.click()
                            return True
                except:
                    continue

        # 方式2: 直接提交表單
        try:
            print("  - 未找到明確按鈕，嘗試直接提交 form 標籤...")
            form = self.driver.find_element(By.TAG_NAME, "form")
            form.submit()
            return True
        except:
            pass

        # 方式3: 在驗證碼欄位按 Enter
        try:
            print("  - 最後嘗試，在驗證碼欄位按 Enter...")
            captcha_field = self.driver.find_element(By.NAME, config.CAPTCHA_FIELD[1])
            captcha_field.send_keys(Keys.RETURN)
            return True
        except Exception as e:
            print(f"  - 所有提交方式均失敗: {e}")
            return False

    def _check_login_result(self):
        """檢查登錄結果。"""
        current_url = self.driver.current_url
        page_source = self.driver.page_source.lower()
        print(f"📍 檢查結果: 當前 URL: {current_url}")

        # 檢查是否有明確的錯誤信息
        for keyword in config.LOGIN_ERROR_KEYWORDS:
            if keyword in page_source:
                print(f"  - 發現錯誤關鍵字: '{keyword}'")
                return "captcha_error" if "驗證" in keyword or "captcha" in keyword else "other_error"

        # 檢查是否有成功的跡象
        if config.LOGIN_URL not in current_url:
            print("  - URL已改變，判定為登錄成功。")
            return "success"
        for keyword in config.LOGIN_SUCCESS_KEYWORDS:
            if keyword in page_source:
                print(f"  - 發現成功關鍵字: '{keyword}'")
                return "success"

        print("  - 未能明確判斷登錄狀態，可能失敗。")
        return "unknown"

    def _encode_image_to_base64(self, image_path):
        """將圖片編碼為 base64。"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"❌ 編碼圖片失敗: {e}")
            return None

    def screenshot_element(self, element, filename):
        """截圖特定元素。"""
        try:
            filepath = os.path.join(self.screenshot_dir, filename)
            element.screenshot(filepath)
            print(f"  - 元素截圖已保存: {filepath}")
        except Exception as e:
            print(f"  - ❌ 元素截圖失敗: {e}")

    def screenshot_full_page(self, filename):
        """截圖整個頁面。"""
        try:
            filepath = os.path.join(self.screenshot_dir, filename)
            self.driver.save_screenshot(filepath)
            print(f"📸 頁面截圖已保存: {filepath}")
        except Exception as e:
            print(f"  - ❌ 頁面截圖失敗: {e}")

    def close(self):
        """安全地關閉瀏覽器。"""
        print("\n🔒 正在關閉瀏覽器...")
        self.driver.quit()