"""
WebTech 自動化系統配置文件
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class WebTechConfig:
    """WebTech 系統配置"""
    
    # 登錄相關配置
    LOGIN_URL: str = "https://www.fq94i.com/webtech"
    USERNAME: str = "jinny0831"
    PASSWORD: str = "uCvMhAK6q"
    
    # OpenAI API 配置
    OPENAI_API_KEY: str = "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"
    OPENAI_MODELS: list = None
    
    # 瀏覽器配置
    HEADLESS: bool = False
    WINDOW_SIZE: tuple = (1920, 1080)
    PAGE_LOAD_TIMEOUT: int = 15
    ELEMENT_WAIT_TIMEOUT: int = 10
    
    # 重試配置
    MAX_LOGIN_RETRIES: int = 5
    RETRY_DELAYS: dict = None
    
    # 截圖配置
    SCREENSHOT_DIR: str = "screenshots"
    CAPTCHA_EXPAND_PIXELS: int = 20
    
    # 文章發布配置
    UPLOAD_TIMEOUT: int = 30
    PUBLISH_TIMEOUT: int = 10
    
    def __post_init__(self):
        """初始化後設置默認值"""
        if self.OPENAI_MODELS is None:
            self.OPENAI_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
        
        if self.RETRY_DELAYS is None:
            self.RETRY_DELAYS = {
                "captcha_error": 2,  # 驗證碼錯誤延遲倍數
                "other_error": 3,    # 其他錯誤延遲倍數
                "max_delay": 15      # 最大延遲秒數
            }
        
        # 創建截圖目錄
        os.makedirs(self.SCREENSHOT_DIR, exist_ok=True)
    
    @classmethod
    def from_env(cls) -> 'WebTechConfig':
        """從環境變量創建配置"""
        return cls(
            LOGIN_URL=os.getenv('WEBTECH_LOGIN_URL', cls.LOGIN_URL),
            USERNAME=os.getenv('WEBTECH_USERNAME', cls.USERNAME),
            PASSWORD=os.getenv('WEBTECH_PASSWORD', cls.PASSWORD),
            OPENAI_API_KEY=os.getenv('OPENAI_API_KEY', cls.OPENAI_API_KEY),
            HEADLESS=os.getenv('WEBTECH_HEADLESS', '').lower() == 'true'
        )
    
    def validate(self) -> bool:
        """驗證配置是否有效"""
        required_fields = ['LOGIN_URL', 'USERNAME', 'PASSWORD']
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"配置項 {field} 不能為空")
        return True

# 全局配置實例
config = WebTechConfig()