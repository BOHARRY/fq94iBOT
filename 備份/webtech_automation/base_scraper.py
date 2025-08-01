"""
基礎爬蟲類 - 提供瀏覽器管理、截圖、等待等基礎功能
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from PIL import Image
from typing import Optional, Union
from .config import config
from .exceptions import WebTechError, BrowserError, ElementNotFoundError

class BaseScraper:
    """基礎爬蟲類 - 提供瀏覽器管理和基礎操作功能"""
    
    def __init__(self, headless: bool = None):
        """
        初始化基礎爬蟲
        
        Args:
            headless: 是否無頭模式，None則使用配置文件設置
        """
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.headless = headless if headless is not None else config.HEADLESS
        self._setup_driver()
    
    def _setup_driver(self):
        """設置 Chrome WebDriver"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # 基礎選項
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument(f'--window-size={config.WINDOW_SIZE[0]},{config.WINDOW_SIZE[1]}')
            
            # 設置 User-Agent
            chrome_options.add_argument(
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            
            # 自動下載 ChromeDriver
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except ImportError:
                # 備用方案：使用系統路徑中的 chromedriver
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # 設置等待
            self.wait = WebDriverWait(self.driver, config.ELEMENT_WAIT_TIMEOUT)
            
            # 設置頁面加載超時
            self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
            
        except Exception as e:
            raise BrowserError(f"瀏覽器初始化失敗: {e}")
    
    def navigate_to(self, url: str, wait_complete: bool = True) -> bool:
        """
        導航到指定URL
        
        Args:
            url: 目標URL
            wait_complete: 是否等待頁面完全加載
            
        Returns:
            bool: 導航是否成功
        """
        try:
            print(f"🌐 導航到: {url}")
            self.driver.get(url)
            
            if wait_complete:
                # 等待頁面加載完成
                self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                print("✅ 頁面加載完成")
            
            return True
            
        except Exception as e:
            print(f"❌ 頁面導航失敗: {e}")
            return False
    
    def refresh_page(self) -> bool:
        """刷新當前頁面"""
        try:
            print("🔄 刷新頁面...")
            self.driver.refresh()
            time.sleep(2)
            print("✅ 頁面刷新完成")
            return True
        except Exception as e:
            print(f"❌ 頁面刷新失敗: {e}")
            return False
    
    def wait_for_element(self, by: By, value: str, timeout: int = None) -> Optional[object]:
        """
        等待元素出現
        
        Args:
            by: 定位方式
            value: 定位值
            timeout: 超時時間
            
        Returns:
            WebElement或None
        """
        try:
            if timeout:
                wait = WebDriverWait(self.driver, timeout)
            else:
                wait = self.wait
            
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
            
        except Exception as e:
            print(f"⚠️ 等待元素失敗 {by}='{value}': {e}")
            return None
    
    def find_element_safe(self, by: By, value: str, timeout: int = 5) -> Optional[object]:
        """
        安全查找元素（不拋出異常）
        
        Args:
            by: 定位方式
            value: 定位值
            timeout: 查找超時時間
            
        Returns:
            WebElement或None
        """
        try:
            old_timeout = self.driver.implicitly_wait(0)  # 暫時設置為0
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
        except:
            return None
        finally:
            self.driver.implicitly_wait(old_timeout)  # 恢復原設置
    
    def find_elements_safe(self, by: By, value: str) -> list:
        """
        安全查找多個元素
        
        Args:
            by: 定位方式
            value: 定位值
            
        Returns:
            WebElement列表
        """
        try:
            return self.driver.find_elements(by, value)
        except:
            return []
    
    def screenshot_full_page(self, filename: str) -> bool:
        """
        截圖整個頁面
        
        Args:
            filename: 保存文件名
            
        Returns:
            bool: 截圖是否成功
        """
        try:
            filepath = os.path.join(config.SCREENSHOT_DIR, filename)
            self.driver.save_screenshot(filepath)
            print(f"📸 頁面截圖已保存: {filepath}")
            return True
        except Exception as e:
            print(f"❌ 頁面截圖失敗: {e}")
            return False
    
    def screenshot_element(self, element, filename: str) -> bool:
        """
        截圖特定元素
        
        Args:
            element: 要截圖的元素
            filename: 保存文件名
            
        Returns:
            bool: 截圖是否成功
        """
        try:
            filepath = os.path.join(config.SCREENSHOT_DIR, filename)
            element.screenshot(filepath)
            print(f"📸 元素截圖已保存: {filepath}")
            return True
        except Exception as e:
            print(f"❌ 元素截圖失敗: {e}")
            return False
    
    def screenshot_area(self, element, filename: str, expand_pixels: int = None) -> bool:
        """
        截圖元素周圍區域
        
        Args:
            element: 中心元素
            filename: 保存文件名
            expand_pixels: 擴展像素數
            
        Returns:
            bool: 截圖是否成功
        """
        try:
            expand = expand_pixels or config.CAPTCHA_EXPAND_PIXELS
            
            location = element.location
            size = element.size
            
            # 計算裁剪區域
            left = max(0, location['x'] - expand)
            top = max(0, location['y'] - expand)
            right = location['x'] + size['width'] + expand
            bottom = location['y'] + size['height'] + expand
            
            # 截圖整個頁面
            temp_file = os.path.join(config.SCREENSHOT_DIR, "temp_full.png")
            self.driver.save_screenshot(temp_file)
            
            # 裁剪指定區域
            filepath = os.path.join(config.SCREENSHOT_DIR, filename)
            with Image.open(temp_file) as img:
                cropped = img.crop((left, top, right, bottom))
                cropped.save(filepath)
            
            # 清理臨時文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            print(f"📸 區域截圖已保存: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ 區域截圖失敗: {e}")
            return False
    
    def get_page_info(self) -> dict:
        """獲取當前頁面信息"""
        try:
            return {
                "title": self.driver.title,
                "url": self.driver.current_url,
                "ready_state": self.driver.execute_script("return document.readyState")
            }
        except Exception as e:
            print(f"⚠️ 獲取頁面信息失敗: {e}")
            return {}
    
    def execute_script(self, script: str) -> any:
        """執行JavaScript腳本"""
        try:
            return self.driver.execute_script(script)
        except Exception as e:
            print(f"⚠️ 執行腳本失敗: {e}")
            return None
    
    def close(self):
        """關閉瀏覽器"""
        try:
            if self.driver:
                self.driver.quit()
                print("🔒 瀏覽器已關閉")
        except Exception as e:
            print(f"⚠️ 關閉瀏覽器時出錯: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()