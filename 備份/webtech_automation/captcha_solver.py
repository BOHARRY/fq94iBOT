"""
驗證碼識別處理器 - 使用OpenAI API進行驗證碼識別
"""
import os
import re
import base64
from selenium.webdriver.common.by import By
from typing import Optional
from .config import config
from .exceptions import CaptchaError

class CaptchaSolver:
    """驗證碼識別處理器"""
    
    def __init__(self, openai_api_key: str = None):
        """
        初始化驗證碼處理器
        
        Args:
            openai_api_key: OpenAI API密鑰
        """
        self.api_key = openai_api_key or config.OPENAI_API_KEY
        self.models_to_try = config.OPENAI_MODELS
        
        if not self.api_key:
            print("⚠️ 未設置OpenAI API Key，無法使用自動驗證碼識別")
    
    def find_captcha_image(self, driver) -> Optional[object]:
        """
        在頁面中尋找驗證碼圖片元素
        
        Args:
            driver: Selenium WebDriver實例
            
        Returns:
            WebElement或None
        """
        # 可能的驗證碼選擇器
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
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ 找到驗證碼圖片: {selector}")
                    return elements[0]
            except:
                continue
        
        # 如果沒找到明顯的驗證碼，檢查所有圖片
        try:
            images = driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                src = img.get_attribute("src") or ""
                alt = img.get_attribute("alt") or ""
                
                # 檢查是否包含驗證碼相關關鍵字
                if any(keyword in src.lower() for keyword in ['img.php', 'captcha', 'verify', 'code']) or \
                   any(keyword in alt.lower() for keyword in ['驗證碼', 'captcha', 'verify']):
                    print(f"✅ 找到可能的驗證碼圖片: {src}")
                    return img
        except:
            pass
        
        print("❌ 未找到驗證碼圖片")
        return None
    
    def encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """
        將圖片編碼為base64
        
        Args:
            image_path: 圖片文件路徑
            
        Returns:
            base64編碼字符串或None
        """
        try:
            if not os.path.exists(image_path):
                print(f"❌ 圖片文件不存在: {image_path}")
                return None
                
            with open(image_path, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode('utf-8')
                return encoded
        except Exception as e:
            print(f"❌ 編碼圖片失敗: {e}")
            return None
    
    def recognize_captcha(self, image_path: str, attempt: int = 1) -> Optional[str]:
        """
        使用OpenAI API識別驗證碼
        
        Args:
            image_path: 驗證碼圖片路徑
            attempt: 嘗試次數（用於日志）
            
        Returns:
            識別出的驗證碼字符串或None
        """
        if not self.api_key:
            print("❌ 未設置OpenAI API Key")
            return None
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            # 編碼圖片
            base64_image = self.encode_image_to_base64(image_path)
            if not base64_image:
                return None
            
            print(f"🤖 正在使用OpenAI API識別驗證碼 (嘗試 #{attempt})...")
            
            # 嘗試不同的模型
            for model in self.models_to_try:
                try:
                    print(f"🔄 嘗試使用模型: {model}")
                    
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": (
                                            "請識別這個驗證碼圖片中的字母和數字。"
                                            "只回答驗證碼內容，不要其他解釋。"
                                            "驗證碼通常是4-6位的字母數字組合，請注意區分字母的大小寫。"
                                            "如果圖片不清楚，請盡最大努力識別。"
                                        )
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
                    
                    # 清理識別結果，只保留字母數字
                    clean_text = re.sub(r'[^a-zA-Z0-9]', '', captcha_text)
                    
                    if clean_text and 3 <= len(clean_text) <= 8:
                        print(f"✅ OpenAI 識別結果: {clean_text} (使用模型: {model})")
                        return clean_text
                    else:
                        print(f"❌ 模型 {model} 識別結果無效: {captcha_text}")
                        continue
                        
                except Exception as model_error:
                    print(f"❌ 模型 {model} 調用失敗: {model_error}")
                    continue
            
            print("❌ 所有模型都無法識別驗證碼")
            return None
                    
        except Exception as e:
            print(f"❌ OpenAI API 調用失敗: {e}")
            return None
    
    def capture_and_recognize(self, base_scraper, attempt: int = 1) -> Optional[str]:
        """
        捕獲並識別驗證碼的完整流程
        
        Args:
            base_scraper: BaseScraper實例
            attempt: 嘗試次數
            
        Returns:
            識別出的驗證碼字符串或None
        """
        # 尋找驗證碼圖片
        captcha_img = self.find_captcha_image(base_scraper.driver)
        if not captcha_img:
            return None
        
        print("📸 找到驗證碼圖片，正在截圖...")
        
        # 截圖驗證碼元素
        captcha_filename = f"captcha_attempt_{attempt}.png"
        if not base_scraper.screenshot_element(captcha_img, captcha_filename):
            return None
        
        # 截圖驗證碼區域（擴大範圍）
        area_filename = f"captcha_area_attempt_{attempt}.png"
        base_scraper.screenshot_area(captcha_img, area_filename)
        
        # 嘗試識別（優先使用區域截圖）
        captcha_code = None
        
        # 首先嘗試區域截圖
        area_path = os.path.join(config.SCREENSHOT_DIR, area_filename)
        if os.path.exists(area_path):
            print(f"🔍 嘗試識別區域截圖: {area_filename}")
            captcha_code = self.recognize_captcha(area_path, attempt)
        
        # 如果區域截圖識別失敗，嘗試元素截圖
        if not captcha_code:
            element_path = os.path.join(config.SCREENSHOT_DIR, captcha_filename)
            if os.path.exists(element_path):
                print(f"🔍 嘗試識別元素截圖: {captcha_filename}")
                captcha_code = self.recognize_captcha(element_path, attempt)
        
        return captcha_code
    
    def validate_captcha_format(self, captcha: str) -> bool:
        """
        驗證驗證碼格式是否合理
        
        Args:
            captcha: 驗證碼字符串
            
        Returns:
            bool: 格式是否合理
        """
        if not captcha:
            return False
        
        # 只包含字母和數字
        if not re.match(r'^[a-zA-Z0-9]+$', captcha):
            return False
        
        # 長度在合理範圍內
        if not (3 <= len(captcha) <= 8):
            return False
        
        return True