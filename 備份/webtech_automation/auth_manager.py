"""
登錄管理器 - 處理登錄流程和重試機制
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from typing import Optional, Dict, Tuple
from .base_scraper import BaseScraper
from .captcha_solver import CaptchaSolver
from .config import config
from .exceptions import LoginError, RetryExhaustedError

class AuthManager(BaseScraper):
    """登錄管理器 - 處理登錄流程和重試機制"""
    
    def __init__(self, headless: bool = None, openai_api_key: str = None):
        """
        初始化登錄管理器
        
        Args:
            headless: 是否無頭模式
            openai_api_key: OpenAI API密鑰
        """
        super().__init__(headless)
        self.captcha_solver = CaptchaSolver(openai_api_key)
        self.login_attempts = 0
    
    def login_with_retry(self, 
                        url: str = None, 
                        username: str = None, 
                        password: str = None,
                        max_retries: int = None) -> bool:
        """
        帶重試機制的登錄流程
        
        Args:
            url: 登錄URL
            username: 用戶名
            password: 密碼
            max_retries: 最大重試次數
            
        Returns:
            bool: 登錄是否成功
        """
        # 使用配置文件的默認值
        url = url or config.LOGIN_URL
        username = username or config.USERNAME
        password = password or config.PASSWORD
        max_retries = max_retries or config.MAX_LOGIN_RETRIES
        
        print(f"🚀 開始登錄流程")
        print(f"🎯 目標URL: {url}")
        print(f"👤 用戶名: {username}")
        print(f"🔄 最大重試次數: {max_retries}")
        
        for attempt in range(1, max_retries + 1):
            try:
                result = self._single_login_attempt(url, username, password, attempt, max_retries)
                
                if result == "success":
                    print(f"🎉 登錄成功！(嘗試 #{attempt}/{max_retries})")
                    return True
                elif result == "captcha_error":
                    if attempt < max_retries:
                        delay = self._calculate_retry_delay("captcha_error", attempt)
                        print(f"❌ 驗證碼錯誤，{delay}秒後重試...")
                        time.sleep(delay)
                        continue
                elif result == "other_error":
                    if attempt < max_retries:
                        delay = self._calculate_retry_delay("other_error", attempt)
                        print(f"❌ 登錄錯誤，{delay}秒後重試...")
                        time.sleep(delay)
                        continue
                else:  # unknown or failed
                    if attempt < max_retries:
                        delay = 3
                        print(f"❓ 狀態不確定，{delay}秒後重試...")
                        time.sleep(delay)
                        continue
                
                # 最後一次嘗試失敗
                if attempt == max_retries:
                    print("💥 已達到最大重試次數，登錄失敗")
                    return False
                    
            except Exception as e:
                print(f"❌ 登錄過程出錯 (嘗試 #{attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    delay = 5
                    print(f"⏳ 等待 {delay} 秒後重試...")
                    time.sleep(delay)
                    continue
                else:
                    return False
        
        return False
    
    def _single_login_attempt(self, url: str, username: str, password: str, 
                             attempt: int, max_retries: int) -> str:
        """
        單次登錄嘗試
        
        Args:
            url: 登錄URL
            username: 用戶名  
            password: 密碼
            attempt: 當前嘗試次數
            max_retries: 最大重試次數
            
        Returns:
            str: 登錄結果 ("success", "captcha_error", "other_error", "failed")
        """
        print(f"\n{'='*50}")
        print(f"🚀 登錄嘗試 #{attempt}/{max_retries}")
        print(f"{'='*50}")
        
        # 導航到登錄頁面
        if attempt == 1:
            if not self.navigate_to(url):
                return "failed"
        else:
            if not self.refresh_page():
                return "failed"
        
        # 截圖登錄頁面
        self.screenshot_full_page(f"login_page_attempt_{attempt}.png")
        
        # 顯示頁面信息
        page_info = self.get_page_info()
        print(f"📄 頁面標題: {page_info.get('title', 'Unknown')}")
        print(f"🔗 當前URL: {page_info.get('url', 'Unknown')}")
        
        # 查找表單字段
        form_fields = self._find_login_form_fields()
        if not form_fields:
            print("❌ 未找到登錄表單字段")
            return "failed"
        
        username_field, password_field, captcha_field = form_fields
        
        # 檢查並填寫表單
        self._fill_login_form(username_field, password_field, username, password)
        
        # 處理驗證碼
        captcha_code = self._handle_captcha(attempt)
        if not captcha_code:
            if attempt == 1:
                # 第一次嘗試允許手動輸入
                captcha_code = input(f"\n[嘗試 #{attempt}] 請輸入驗證碼: ").strip()
            else:
                print(f"❌ 第 {attempt} 次嘗試驗證碼識別失敗")
                return "captcha_error"
        
        if not captcha_code:
            return "failed"
        
        # 填入驗證碼
        captcha_field.clear()
        captcha_field.send_keys(captcha_code)
        print(f"✅ 驗證碼已填入: {captcha_code}")
        
        # 提交表單
        if not self._submit_login_form():
            return "failed"
        
        # 等待響應
        time.sleep(3)
        
        # 檢查登錄結果
        return self._check_login_result(url, attempt)
    
    def _find_login_form_fields(self) -> Optional[Tuple]:
        """
        查找登錄表單字段
        
        Returns:
            Tuple: (用戶名字段, 密碼字段, 驗證碼字段) 或 None
        """
        try:
            print("🔍 查找登錄表單字段...")
            
            username_field = self.wait_for_element(By.NAME, "username")
            if not username_field:
                print("❌ 未找到用戶名字段")
                return None
            
            password_field = self.find_element_safe(By.NAME, "userpwd")
            if not password_field:
                print("❌ 未找到密碼字段")
                return None
            
            captcha_field = self.find_element_safe(By.NAME, "checknum")
            if not captcha_field:
                print("❌ 未找到驗證碼字段")
                return None
            
            print("✅ 找到所有表單字段")
            return username_field, password_field, captcha_field
            
        except Exception as e:
            print(f"❌ 查找表單字段失敗: {e}")
            return None
    
    def _fill_login_form(self, username_field, password_field, username: str, password: str):
        """
        填寫登錄表單
        
        Args:
            username_field: 用戶名字段元素
            password_field: 密碼字段元素
            username: 用戶名
            password: 密碼
        """
        try:
            # 檢查字段當前值
            current_username = username_field.get_attribute("value") or ""
            current_password = password_field.get_attribute("value") or ""
            
            print(f"📋 表單當前狀態:")
            print(f"  用戶名: {'✅' if current_username else '❌'} ({current_username})")
            print(f"  密碼: {'✅' if current_password else '❌'} ({'*' * len(current_password)})")
            
            # 清空並重新填入
            print("🔄 重新填寫用戶名和密碼...")
            username_field.clear()
            username_field.send_keys(username)
            
            password_field.clear()
            password_field.send_keys(password)
            
            print("✅ 已填入用戶名和密碼")
            
        except Exception as e:
            print(f"❌ 填寫表單失敗: {e}")
            raise LoginError(f"填寫表單失敗: {e}")
    
    def _handle_captcha(self, attempt: int) -> Optional[str]:
        """
        處理驗證碼識別
        
        Args:
            attempt: 當前嘗試次數
            
        Returns:
            識別出的驗證碼或None
        """
        if not self.captcha_solver.api_key:
            print("⚠️ 未配置OpenAI API，無法自動識別驗證碼")
            return None
        
        print(f"🤖 正在自動識別驗證碼 (嘗試 #{attempt})...")
        captcha_code = self.captcha_solver.capture_and_recognize(self, attempt)
        
        if captcha_code and self.captcha_solver.validate_captcha_format(captcha_code):
            print(f"✅ 自動識別成功: {captcha_code}")
            return captcha_code
        else:
            print("❌ 自動識別失敗")
            return None
    
    def _submit_login_form(self) -> bool:
        """
        提交登錄表單
        
        Returns:
            bool: 提交是否成功
        """
        try:
            print("🚀 正在提交登錄表單...")
            
            # 方式1: 查找提交按鈕
            submit_buttons = self._find_submit_buttons()
            
            if submit_buttons:
                try:
                    print("✅ 找到提交按鈕，正在點擊...")
                    submit_buttons[0].click()
                    return True
                except Exception as e:
                    print(f"❌ 點擊提交按鈕失敗: {e}")
            
            # 方式2: 直接提交表單
            try:
                print("🔄 嘗試直接提交表單...")
                form_element = self.find_element_safe(By.TAG_NAME, "form")
                if form_element:
                    form_element.submit()
                    print("✅ 表單提交成功")
                    return True
            except Exception as e:
                print(f"❌ 直接提交表單失敗: {e}")
            
            # 方式3: 按回車鍵
            try:
                print("⌨️ 嘗試按Enter鍵...")
                captcha_field = self.find_element_safe(By.NAME, "checknum")
                if captcha_field:
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
    
    def _find_submit_buttons(self) -> list:
        """
        查找提交按鈕
        
        Returns:
            WebElement列表
        """
        submit_buttons = []
        
        # 標準提交按鈕
        submit_buttons = self.find_elements_safe(By.CSS_SELECTOR, 
            "input[type='submit'], button[type='submit']")
        
        if submit_buttons:
            print(f"✅ 找到 {len(submit_buttons)} 個標準提交按鈕")
            return submit_buttons
        
        # XPath查找包含關鍵字的按鈕
        submit_buttons = self.find_elements_safe(By.XPATH, 
            "//input[contains(@value, '登')] | //button[contains(text(), '登')] | "
            "//input[contains(@value, 'login')] | //button[contains(text(), 'login')] | "
            "//input[contains(@value, '提交')] | //button[contains(text(), '提交')]")
        
        if submit_buttons:
            print(f"✅ 通過關鍵字找到 {len(submit_buttons)} 個提交按鈕")
            return submit_buttons
        
        # 智能匹配所有按鈕
        all_buttons = self.find_elements_safe(By.CSS_SELECTOR, "button, input[type='button']")
        
        for btn in all_buttons:
            btn_text = (btn.text or "").lower()
            btn_value = (btn.get_attribute("value") or "").lower()
            btn_class = (btn.get_attribute("class") or "").lower()
            btn_id = (btn.get_attribute("id") or "").lower()
            
            # 排除驗證碼刷新按鈕
            if "change_code" in btn_class or "change_code" in btn_id:
                continue
            
            # 匹配提交相關關鍵字
            if any(keyword in btn_text or keyword in btn_value or keyword in btn_class or keyword in btn_id
                  for keyword in ['登', 'login', 'submit', '提交', '確認', 'ok']):
                print(f"✅ 找到疑似提交按鈕: {btn_text or btn_value}")
                return [btn]
        
        return []
    
    def _check_login_result(self, original_url: str, attempt: int) -> str:
        """
        檢查登錄結果
        
        Args:
            original_url: 原始登錄URL
            attempt: 嘗試次數
            
        Returns:
            str: 登錄結果 ("success", "captcha_error", "other_error", "unknown")
        """
        try:
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            print(f"📍 提交後的URL: {current_url}")
            
            # 截圖結果頁面
            self.screenshot_full_page(f"login_result_attempt_{attempt}.png")
            
            # 檢查是否還在登錄頁面且表單字段為空（表示驗證碼錯誤）
            if current_url == original_url or "webtech" in current_url:
                if self._check_form_fields_cleared():
                    print("🔴 表單字段被清空，可能是驗證碼錯誤")
                    return "captcha_error"
            
            # 檢查頁面內容中的錯誤提示
            error_type = self._analyze_error_messages(page_source)
            if error_type:
                return error_type
            
            # 檢查是否登錄成功
            if self._check_login_success(current_url, original_url, page_source):
                print("🟢 登錄成功")
                return "success"
            
            print("🟡 登錄狀態不確定")
            return "unknown"
            
        except Exception as e:
            print(f"❌ 檢查登錄結果時發生錯誤: {e}")
            return "unknown"
    
    def _check_form_fields_cleared(self) -> bool:
        """檢查表單字段是否被清空"""
        try:
            username_field = self.find_element_safe(By.NAME, "username")
            password_field = self.find_element_safe(By.NAME, "userpwd")
            captcha_field = self.find_element_safe(By.NAME, "checknum")
            
            if not all([username_field, password_field, captcha_field]):
                return False
            
            username_value = username_field.get_attribute("value") or ""
            password_value = password_field.get_attribute("value") or ""
            captcha_value = captcha_field.get_attribute("value") or ""
            
            print(f"🔍 檢查表單字段狀態:")
            print(f"  用戶名: {'空' if not username_value else '有值'}")
            print(f"  密碼: {'空' if not password_value else '有值'}")
            print(f"  驗證碼: {'空' if not captcha_value else '有值'}")
            
            return not username_value or not password_value or not captcha_value
            
        except Exception:
            return False
    
    def _analyze_error_messages(self, page_source: str) -> Optional[str]:
        """分析頁面中的錯誤信息"""
        error_keywords = {
            "captcha_error": ["驗證碼錯誤", "verification code", "captcha", "驗證失敗"],
            "other_error": ["登錄失敗", "login failed", "用戶名或密碼錯誤", "帳號或密碼錯誤"]
        }
        
        page_lower = page_source.lower()
        
        for error_type, keywords in error_keywords.items():
            for keyword in keywords:
                if keyword in page_lower:
                    print(f"🔴 發現錯誤關鍵字: {keyword}")
                    return error_type
        
        return None
    
    def _check_login_success(self, current_url: str, original_url: str, page_source: str) -> bool:
        """檢查是否登錄成功"""
        success_indicators = [
            current_url != original_url,
            "成功" in page_source,
            "歡迎" in page_source,
            "welcome" in page_source.lower(),
            "dashboard" in current_url.lower(),
            "admin" in current_url.lower(),
            "system" in current_url.lower()
        ]
        
        return any(success_indicators)
    
    def _calculate_retry_delay(self, error_type: str, attempt: int) -> int:
        """
        計算重試延遲時間
        
        Args:
            error_type: 錯誤類型
            attempt: 嘗試次數
            
        Returns:
            延遲秒數
        """
        base_delay = config.RETRY_DELAYS.get(error_type, 3)
        max_delay = config.RETRY_DELAYS.get("max_delay", 15)
        
        delay = min(base_delay * attempt, max_delay)
        return delay
    
    def is_logged_in(self) -> bool:
        """檢查當前是否已登錄"""
        try:
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            # 如果在登錄頁面，說明未登錄
            if "webtech" in current_url and any(field in page_source for field in ["username", "password"]):
                return False
            
            # 如果URL包含system或admin，可能已登錄
            if any(indicator in current_url.lower() for indicator in ["system", "admin", "dashboard"]):
                return True
            
            return False
            
        except Exception:
            return False