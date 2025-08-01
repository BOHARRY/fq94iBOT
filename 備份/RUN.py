from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import os
import base64
from PIL import Image

class SeleniumScraper:
    def __init__(self, headless=False, openai_api_key=None):
        """初始化 Selenium WebDriver"""
        self.driver = None
        self.openai_api_key = openai_api_key
        if openai_api_key:
            print("OpenAI API 已配置，將自動識別驗證碼")
        self.setup_driver(headless)
    
    def setup_driver(self, headless=False):
        """設置 Chrome WebDriver"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
        
        # 常用選項
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 設置 User-Agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            # 自動下載 ChromeDriver（需要安裝 webdriver-manager）
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except ImportError:
            print("請安裝 webdriver-manager: pip install webdriver-manager")
            print("或者手動下載 ChromeDriver 並設置路徑")
            # 備用方案：使用系統路徑中的 chromedriver
            self.driver = webdriver.Chrome(options=chrome_options)
        
        self.wait = WebDriverWait(self.driver, 10)
    
    def encode_image_to_base64(self, image_path):
        """將圖片編碼為 base64"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"編碼圖片失敗: {e}")
            return None
    
    def submit_form(self):
        """提交表單的多種方式"""
        try:
            print("🔄 正在查找提交方式...")
            
            # 打印表單結構用於調試
            try:
                form_element = self.driver.find_element(By.TAG_NAME, "form")
                print("✅ 找到表單元素")
                
                # 打印表單內所有按鈕和輸入元素
                all_inputs = form_element.find_elements(By.CSS_SELECTOR, "input, button")
                print(f"📋 表單內共有 {len(all_inputs)} 個輸入元素:")
                
                for i, elem in enumerate(all_inputs):
                    elem_type = elem.get_attribute("type") or "unknown"
                    elem_value = elem.get_attribute("value") or ""
                    elem_text = elem.text or ""
                    elem_class = elem.get_attribute("class") or ""
                    elem_id = elem.get_attribute("id") or ""
                    print(f"  {i+1}. 類型:{elem_type}, 值:{elem_value}, 文本:{elem_text}, class:{elem_class}, id:{elem_id}")
            except Exception as e:
                print(f"⚠️ 無法分析表單結構: {e}")
            
            # 方式1: 嘗試找到提交按鈕
            submit_buttons = []
            
            # 1.1 標準提交按鈕
            try:
                submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                    "input[type='submit'], button[type='submit']")
                if submit_buttons:
                    print(f"✅ 找到 {len(submit_buttons)} 個標準提交按鈕")
            except Exception as e:
                print(f"❌ 查找標準提交按鈕失敗: {e}")
            
            # 1.2 使用XPath查找包含關鍵字的按鈕
            if not submit_buttons:
                try:
                    submit_buttons = self.driver.find_elements(By.XPATH, 
                        "//input[contains(@value, '登')] | //button[contains(text(), '登')] | //input[contains(@value, 'login')] | //button[contains(text(), 'login')] | //input[contains(@value, '提交')] | //button[contains(text(), '提交')]")
                    if submit_buttons:
                        print(f"✅ 通過關鍵字找到 {len(submit_buttons)} 個提交按鈕")
                except Exception as e:
                    print(f"❌ XPath查找提交按鈕失敗: {e}")
            
            # 1.3 查找所有可能的按鈕並智能匹配
            if not submit_buttons:
                try:
                    all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, input[type='button']")
                    print(f"🔍 找到 {len(all_buttons)} 個按鈕元素")
                    
                    for i, btn in enumerate(all_buttons):
                        btn_text = btn.text.lower() if btn.text else ""
                        btn_value = (btn.get_attribute("value") or "").lower()
                        btn_class = (btn.get_attribute("class") or "").lower()
                        btn_id = (btn.get_attribute("id") or "").lower()
                        
                        print(f"  按鈕{i+1}: 文本='{btn_text}', 值='{btn_value}', class='{btn_class}', id='{btn_id}'")
                        
                        # 排除驗證碼刷新按鈕
                        if "change_code" in btn_class or "change_code" in btn_id:
                            print(f"  -> ⏭️ 跳過驗證碼刷新按鈕")
                            continue
                        
                        # 匹配提交相關關鍵字
                        if any(keyword in btn_text or keyword in btn_value or keyword in btn_class or keyword in btn_id
                              for keyword in ['登', 'login', 'submit', '提交', '確認', 'ok']):
                            submit_buttons = [btn]
                            print(f"  -> ✅ 找到疑似提交按鈕: {btn_text or btn_value}")
                            break
                except Exception as e:
                    print(f"❌ 智能查找按鈕失敗: {e}")
            
            # 方式2: 如果找到了提交按鈕，點擊它
            if submit_buttons:
                try:
                    print("🚀 找到提交按鈕，正在提交...")
                    submit_buttons[0].click()
                    return True
                except Exception as e:
                    print(f"❌ 點擊提交按鈕失敗: {e}")
            
            # 方式3: 嘗試直接提交表單
            try:
                print("🔄 嘗試直接提交表單...")
                form_element = self.driver.find_element(By.TAG_NAME, "form")
                form_element.submit()
                print("✅ 表單提交成功")
                return True
            except Exception as e:
                print(f"❌ 直接提交表單失敗: {e}")
            
            # 方式4: 最後嘗試按回車鍵
            try:
                print("⌨️ 嘗試按Enter鍵...")
                captcha_field = self.driver.find_element(By.NAME, "checknum")
                from selenium.webdriver.common.keys import Keys
                captcha_field.send_keys(Keys.RETURN)
                print("✅ 已按Enter鍵")
                return True
            except Exception as e:
                print(f"❌ 按Enter鍵失敗: {e}")
            
            print("💥 所有提交方式都失敗了")
            return False
            
        except Exception as e:
            print(f"❌ 提交表單時發生錯誤: {e}")
            return False
    
    def check_login_result(self, original_url, attempt):
        """檢查登錄結果"""
        try:
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            print(f"📍 提交後的URL: {current_url}")
            
            # 截圖結果頁面
            self.screenshot_full_page(f"login_result_attempt_{attempt}.png")
            
            # 檢查是否還在登錄頁面且表單字段為空（表示驗證碼錯誤）
            if current_url == original_url or "webtech" in current_url:
                try:
                    # 檢查表單字段是否被清空
                    username_field = self.driver.find_element(By.NAME, "username")
                    password_field = self.driver.find_element(By.NAME, "userpwd")
                    captcha_field = self.driver.find_element(By.NAME, "checknum")
                    
                    username_value = username_field.get_attribute("value") or ""
                    password_value = password_field.get_attribute("value") or ""
                    captcha_value = captcha_field.get_attribute("value") or ""
                    
                    print(f"🔍 檢查表單字段狀態:")
                    print(f"  用戶名: {'空' if not username_value else '有值'}")
                    print(f"  密碼: {'空' if not password_value else '有值'}")
                    print(f"  驗證碼: {'空' if not captcha_value else '有值'}")
                    
                    # 如果字段被清空，通常表示驗證碼錯誤
                    if not username_value or not password_value or not captcha_value:
                        print("🔴 表單字段被清空，可能是驗證碼錯誤")
                        return "captcha_error"
                        
                except Exception as e:
                    print(f"⚠️ 無法檢查表單字段: {e}")
            
            # 檢查頁面內容中的錯誤提示
            error_keywords = [
                "驗證碼錯誤", "verification code", "captcha", "驗證失敗",
                "登錄失敗", "login failed", "用戶名或密碼錯誤", "帳號或密碼錯誤"
            ]
            
            for keyword in error_keywords:
                if keyword in page_source.lower():
                    print(f"🔴 發現錯誤關鍵字: {keyword}")
                    if "驗證" in keyword or "captcha" in keyword or "verification" in keyword:
                        return "captcha_error"
                    else:
                        return "other_error"
            
            # 檢查是否登錄成功（URL改變或包含成功相關內容）
            success_indicators = [
                current_url != original_url,
                "成功" in page_source,
                "歡迎" in page_source,
                "welcome" in page_source.lower(),
                "dashboard" in current_url.lower(),
                "admin" in current_url.lower(),
                "system" in current_url.lower()
            ]
            
            if any(success_indicators):
                print("🟢 登錄可能成功")
                return "success"
            
            print("🟡 登錄狀態不確定")
            return "unknown"
            
        except Exception as e:
            print(f"❌ 檢查登錄結果時發生錯誤: {e}")
            return "error"
    
    def recognize_captcha_with_openai_new(self, image_path):
        """使用最新版 OpenAI API 識別驗證碼"""
        if not self.openai_api_key:
            print("未設置 OpenAI API Key")
            return None
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            # 編碼圖片
            base64_image = self.encode_image_to_base64(image_path)
            if not base64_image:
                return None
            
            print("正在使用 OpenAI API 識別驗證碼...")
            
            # 嘗試使用最新的視覺模型
            models_to_try = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
            
            for model in models_to_try:
                try:
                    print(f"嘗試使用模型: {model}")
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "請識別這個驗證碼圖片中的字母和數字。只回答驗證碼內容，不要其他解釋。驗證碼通常是4-6位的字母數字組合，請注意區分字母的大小寫。如果圖片不清楚，請盡最大努力識別。"
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{base64_image}",
                                            "detail": "high"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=50,
                        temperature=0.1  # 降低隨機性，提高準確性
                    )
                    
                    captcha_text = response.choices[0].message.content.strip()
                    
                    # 清理識別結果，移除可能的解釋文字
                    import re
                    # 只保留字母數字
                    clean_text = re.sub(r'[^a-zA-Z0-9]', '', captcha_text)
                    
                    if clean_text:
                        print(f"OpenAI 識別結果: {clean_text} (使用模型: {model})")
                        return clean_text
                    else:
                        print(f"模型 {model} 識別結果無效: {captcha_text}")
                        continue
                        
                except Exception as model_error:
                    print(f"模型 {model} 調用失敗: {model_error}")
                    continue
            
            print("所有模型都無法識別驗證碼")
            return None
                    
        except Exception as e:
            print(f"OpenAI API 調用失敗: {e}")
            return None
    
    def recognize_captcha_with_openai(self, image_path):
        """舊版 API (已棄用，僅作備用)"""
        print("舊版 OpenAI API 已不支持，請升級到新版")
        return None
    
    def setup_driver(self, headless=False):
        """設置 Chrome WebDriver"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
        
        # 常用選項
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 設置 User-Agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            # 自動下載 ChromeDriver（需要安裝 webdriver-manager）
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except ImportError:
            print("請安裝 webdriver-manager: pip install webdriver-manager")
            print("或者手動下載 ChromeDriver 並設置路徑")
            # 備用方案：使用系統路徑中的 chromedriver
            self.driver = webdriver.Chrome(options=chrome_options)
        
        self.wait = WebDriverWait(self.driver, 10)
    
    def screenshot_full_page(self, filename="full_page.png"):
        """截圖整個頁面"""
        try:
            self.driver.save_screenshot(filename)
            print(f"頁面截圖已保存: {filename}")
            return True
        except Exception as e:
            print(f"截圖失敗: {e}")
            return False
    
    def screenshot_element(self, element, filename="element.png"):
        """截圖特定元素"""
        try:
            element.screenshot(filename)
            print(f"元素截圖已保存: {filename}")
            return True
        except Exception as e:
            print(f"元素截圖失敗: {e}")
            return False
    
    def find_captcha_image(self):
        """尋找驗證碼圖片元素"""
        possible_selectors = [
            "img[src*='img.php']",
            "img[src*='captcha']",
            "img[src*='verify']",
            "img[src*='code']",
            "img[alt*='驗證碼']",
            "img[alt*='captcha']",
            ".captcha img",
            "#captcha img"
        ]
        
        for selector in possible_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"找到驗證碼圖片: {selector}")
                    return elements[0]
            except:
                continue
        
        # 如果沒找到，嘗試找所有圖片
        try:
            images = self.driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                src = img.get_attribute("src") or ""
                alt = img.get_attribute("alt") or ""
                
                if any(keyword in src.lower() for keyword in ['img.php', 'captcha', 'verify', 'code']) or \
                   any(keyword in alt.lower() for keyword in ['驗證碼', 'captcha', 'verify']):
                    print(f"找到可能的驗證碼圖片: {src}")
                    return img
        except:
            pass
        
        return None
    
    def login_process(self, url, username, password, max_retries=5):
        """完整的登錄流程 - 帶智能重試機制"""
        for attempt in range(1, max_retries + 1):
            try:
                print(f"\n{'='*50}")
                print(f"🚀 登錄嘗試 #{attempt}/{max_retries}")
                print(f"{'='*50}")
                
                if attempt == 1:
                    print(f"🌐 正在打開頁面: {url}")
                    try:
                        self.driver.get(url)
                        print("⏳ 等待頁面加載...")
                        # 等待頁面加載完成，最多等待15秒
                        self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                        print("✅ 頁面加載完成")
                    except Exception as e:
                        print(f"⚠️ 頁面加載警告: {e}")
                        print("🔄 繼續嘗試...")
                    
                    # 額外等待確保JavaScript執行完成
                    time.sleep(3)
                    
                    # 檢查頁面標題和URL
                    current_title = self.driver.title
                    current_url_check = self.driver.current_url
                    print(f"📄 頁面標題: {current_title}")
                    print(f"🔗 當前URL: {current_url_check}")
                    
                else:
                    print("🔄 刷新頁面重新開始...")
                    try:
                        self.driver.refresh()
                        print("⏳ 等待頁面刷新...")
                        time.sleep(3)
                        print("✅ 頁面刷新完成")
                    except Exception as e:
                        print(f"⚠️ 頁面刷新警告: {e}")
                        # 如果刷新失敗，嘗試重新訪問
                        try:
                            self.driver.get(url)
                            time.sleep(3)
                        except Exception as e2:
                            print(f"❌ 重新訪問也失敗: {e2}")
                            continue
                
                # 截圖整個登錄頁面
                self.screenshot_full_page(f"login_page_attempt_{attempt}.png")
                
                # 尋找並截圖驗證碼
                captcha_img = self.find_captcha_image()
                if captcha_img:
                    print("找到驗證碼圖片，正在截圖...")
                    self.screenshot_element(captcha_img, f"captcha_attempt_{attempt}.png")
                    
                    # 截圖驗證碼區域
                    try:
                        location = captcha_img.location
                        size = captcha_img.size
                        
                        # 擴大截圖範圍
                        left = max(0, location['x'] - 20)
                        top = max(0, location['y'] - 20)
                        right = location['x'] + size['width'] + 20
                        bottom = location['y'] + size['height'] + 20
                        
                        # 截圖整個頁面，然後裁剪
                        self.driver.save_screenshot("temp_full.png")
                        
                        # 使用 PIL 裁剪
                        with Image.open("temp_full.png") as img:
                            cropped = img.crop((left, top, right, bottom))
                            cropped.save(f"captcha_area_attempt_{attempt}.png")
                            print(f"驗證碼區域截圖已保存: captcha_area_attempt_{attempt}.png")
                        
                        # 清理臨時文件
                        if os.path.exists("temp_full.png"):
                            os.remove("temp_full.png")
                            
                    except Exception as e:
                        print(f"裁剪驗證碼區域失敗: {e}")
                else:
                    print("⚠️ 未找到驗證碼圖片")
                
                # 尋找表單元素
                try:
                    username_field = self.wait.until(
                        EC.presence_of_element_located((By.NAME, "username"))
                    )
                    password_field = self.driver.find_element(By.NAME, "userpwd")
                    captcha_field = self.driver.find_element(By.NAME, "checknum")
                    
                    print("✅ 找到所有表單字段")
                    
                    # 檢查字段當前值
                    current_username = username_field.get_attribute("value") or ""
                    current_password = password_field.get_attribute("value") or ""
                    current_captcha = captcha_field.get_attribute("value") or ""
                    
                    print(f"表單當前狀態:")
                    print(f"  用戶名: {'✅' if current_username else '❌'} ({current_username})")
                    print(f"  密碼: {'✅' if current_password else '❌'} ({'*' * len(current_password)})")
                    print(f"  驗證碼: {'✅' if current_captcha else '❌'} ({current_captcha})")
                    
                    # 清空並重新填入用戶名和密碼
                    print("🔄 重新填寫用戶名和密碼...")
                    username_field.clear()
                    username_field.send_keys(username)
                    
                    password_field.clear()
                    password_field.send_keys(password)
                    
                    print("✅ 已填入用戶名和密碼")
                    
                    # 自動識別驗證碼
                    captcha_code = None
                    if self.openai_api_key and captcha_img:
                        print(f"🤖 正在自動識別驗證碼 (嘗試 #{attempt})...")
                        
                        # 嘗試多個截圖文件，優先使用最清晰的
                        captcha_files = [f"captcha_area_attempt_{attempt}.png", f"captcha_attempt_{attempt}.png"]
                        
                        for i, captcha_file in enumerate(captcha_files):
                            if os.path.exists(captcha_file):
                                print(f"🔍 嘗試識別 {captcha_file}...")
                                captcha_code = self.recognize_captcha_with_openai_new(captcha_file)
                                
                                # 如果識別結果看起來合理，就使用它
                                if captcha_code and 3 <= len(captcha_code) <= 8:
                                    print(f"✅ 識別成功: {captcha_code}")
                                    break
                                else:
                                    print(f"❌ 識別結果不理想: {captcha_code}，嘗試下一個文件...")
                                    captcha_code = None
                        
                        if captcha_code:
                            print(f"🎯 自動識別的驗證碼: {captcha_code}")
                        else:
                            print("❌ 自動識別失敗，需要手動輸入")
                    
                    # 如果自動識別失敗，手動輸入（僅在第一次嘗試時）
                    if not captcha_code:
                        if attempt == 1:
                            print("\n請查看以下文件中的驗證碼:")
                            for f in [f"login_page_attempt_{attempt}.png", f"captcha_area_attempt_{attempt}.png", f"captcha_attempt_{attempt}.png"]:
                                if os.path.exists(f):
                                    print(f"- {f}")
                            captcha_code = input(f"\n[嘗試 #{attempt}] 請輸入驗證碼: ").strip()
                        else:
                            print(f"❌ 第 {attempt} 次嘗試自動識別失敗，將重試...")
                            if attempt < max_retries:
                                retry_delay = 2
                                print(f"⏳ 等待 {retry_delay} 秒後重試...")
                                time.sleep(retry_delay)
                            continue
                    
                    if captcha_code:
                        # 填入驗證碼並提交
                        captcha_field.clear()
                        captcha_field.send_keys(captcha_code)
                        print(f"✅ 驗證碼已填入: {captcha_code}")
                        
                        # 提交表單
                        success = self.submit_form()
                        
                        if success:
                            # 等待響應
                            time.sleep(3)
                            
                            # 檢查登錄結果
                            login_result = self.check_login_result(url, attempt)
                            
                            if login_result == "success":
                                print(f"🎉 登錄成功！(嘗試 #{attempt}/{max_retries})")
                                return True
                            elif login_result == "captcha_error":
                                print(f"❌ 驗證碼錯誤 (嘗試 #{attempt}/{max_retries})")
                                if attempt < max_retries:
                                    retry_delay = min(2 * attempt, 10)  # 遞增延遲，最大10秒
                                    print(f"⏳ 等待 {retry_delay} 秒後重試...")
                                    time.sleep(retry_delay)
                                    continue
                                else:
                                    print("💥 已達到最大重試次數，放棄登錄")
                                    return False
                            elif login_result == "other_error":
                                print(f"❌ 其他登錄錯誤 (嘗試 #{attempt}/{max_retries})")
                                if attempt < max_retries:
                                    retry_delay = min(3 * attempt, 15)  # 其他錯誤延遲更長
                                    print(f"⏳ 等待 {retry_delay} 秒後重試...")
                                    time.sleep(retry_delay)
                                    continue
                                else:
                                    print("💥 已達到最大重試次數，放棄登錄")
                                    return False
                            else:
                                print(f"❓ 登錄狀態不確定 (嘗試 #{attempt}/{max_retries})")
                                if attempt < max_retries:
                                    retry_delay = 3
                                    print(f"⏳ 等待 {retry_delay} 秒後重試...")
                                    time.sleep(retry_delay)
                                    continue
                                else:
                                    return None
                        else:
                            print(f"❌ 表單提交失敗 (嘗試 #{attempt}/{max_retries})")
                            if attempt < max_retries:
                                retry_delay = 3
                                print(f"⏳ 等待 {retry_delay} 秒後重試...")
                                time.sleep(retry_delay)
                                continue
                            else:
                                return False
                    else:
                        print(f"❌ 未獲得驗證碼 (嘗試 #{attempt}/{max_retries})")
                        if attempt < max_retries:
                            retry_delay = 2
                            print(f"⏳ 等待 {retry_delay} 秒後重試...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            return False
                        
                except Exception as e:
                    print(f"❌ 操作表單時出錯 (嘗試 #{attempt}/{max_retries}): {e}")
                    if attempt < max_retries:
                        retry_delay = 3
                        print(f"⏳ 等待 {retry_delay} 秒後重試...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        return False
                        
            except Exception as e:
                print(f"❌ 登錄過程出錯 (嘗試 #{attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    retry_delay = 5
                    print(f"⏳ 等待 {retry_delay} 秒後重試...")
                    time.sleep(retry_delay)
                    continue
                else:
                    return False
        
        print("💥 所有重試嘗試都失敗了")
        return False
    
    def close(self):
        """關閉瀏覽器"""
        if self.driver:
            self.driver.quit()

# 使用示例
def main():
    # OpenAI API Key
    api_key = "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"  # 請替換為您的實際 API Key
 
    
    # 創建爬蟲實例（設置 headless=False 可以看到瀏覽器操作過程）
    scraper = SeleniumScraper(headless=False, openai_api_key=api_key)
    
    try:
        # 登錄信息
        login_url = "https://www.fq94i.com/webtech"
        username = "jinny0831"
        password = "uCvMhAK6q"
        max_retries = 5  # 最大重試次數
        
        print("🤖 啟動智能自動登錄爬蟲")
        print(f"🎯 目標網址: {login_url}")
        print(f"👤 用戶名: {username}")
        print(f"🔄 最大重試次數: {max_retries}")
        print(f"🧠 AI驗證碼識別: {'✅ 已啟用' if api_key else '❌ 未配置'}")
        
        # 執行帶重試機制的登錄流程
        result = scraper.login_process(login_url, username, password, max_retries)
        
        if result:
            print("\n" + "="*60)
            print("🎉 登錄成功！可以繼續後續操作...")
            print("="*60)
            
            # 在這裡添加登錄後的爬蟲邏輯
            # 例如：訪問其他頁面、抓取數據等
            
            # 示例：抓取登錄後的頁面內容
            print("📥 正在抓取登錄後的頁面內容...")
            page_content = scraper.driver.page_source
            print(f"📄 頁面內容長度: {len(page_content)} 字符")
            
            # 保存頁面內容到文件
            with open("logged_in_content.html", "w", encoding="utf-8") as f:
                f.write(page_content)
            print("✅ 頁面內容已保存到 logged_in_content.html")
            
            # 獲取最終登錄後的URL
            final_url = scraper.driver.current_url
            print(f"🌐 最終頁面URL: {final_url}")
            
            # 自動化選項：可以在這裡添加更多操作
            print("\n🤖 全自動登錄完成！")
            print("💡 如需進行更多操作，請在代碼中添加...")
            
            # 可選：保持瀏覽器開啟以便手動操作
            keep_open = input("\n❓ 是否保持瀏覽器開啟以便手動操作？(y/n，默認5秒後自動關閉): ").strip().lower()
            
            if keep_open in ['y', 'yes']:
                print("🖥️ 瀏覽器將保持開啟，按 Enter 鍵關閉...")
                input()
            else:
                print("⏰ 5秒後自動關閉瀏覽器...")
                for i in range(5, 0, -1):
                    print(f"   {i}...", end="", flush=True)
                    time.sleep(1)
                print("\n👋 關閉瀏覽器")
                
        elif result is False:
            print("\n" + "="*60)
            print("❌ 登錄失敗！所有重試嘗試都已用盡")
            print("="*60)
            print("🔍 可能的原因:")
            print("  1. 帳號或密碼錯誤")
            print("  2. 驗證碼識別持續失敗")
            print("  3. 網站結構發生變化")
            print("  4. 網絡連接問題")
            print("\n💡 建議:")
            print("  - 檢查帳號密碼是否正確")
            print("  - 查看生成的截圖文件")
            print("  - 手動訪問網站確認是否可以正常登錄")
            
        else:
            print("\n" + "="*60)
            print("❓ 登錄狀態不確定")
            print("="*60)
            print("🔍 請查看生成的截圖文件以確認狀態")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 用戶中斷操作")
    except Exception as e:
        print(f"\n\n❌ 程序執行出錯: {e}")
    finally:
        try:
            scraper.close()
            print("🔒 瀏覽器已關閉")
        except:
            pass

if __name__ == "__main__":
    main()