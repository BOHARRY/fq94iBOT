"""
WebTech 自動化系統

一個完整的網站自動登錄和文章發布自動化解決方案
"""

__version__ = "1.0.0"
__author__ = "WebTech Automation Team"
__description__ = "WebTech網站自動化系統 - 支持自動登錄、驗證碼識別、文章發布"

# 導出主要類和函數
from .main import WebTechAutomation
from .auth_manager import AuthManager
from .article_publisher import ArticlePublisher
from .captcha_solver import CaptchaSolver
from .base_scraper import BaseScraper
from .config import config, WebTechConfig
from .exceptions import (
    WebTechError,
    LoginError,
    CaptchaError,
    PublishError,
    BrowserError,
    ElementNotFoundError,
    RetryExhaustedError,
    ConfigError
)

# 導出工具函數
from .utils import (
    validate_image_file,
    resize_image,
    clean_filename,
    extract_title_and_content,
    parse_line_message,
    log_operation
)

# 便捷函數
def quick_login(username: str = None, password: str = None, headless: bool = False) -> WebTechAutomation:
    """
    快速登錄函數
    
    Args:
        username: 用戶名
        password: 密碼  
        headless: 是否無頭模式
        
    Returns:
        WebTechAutomation實例
    """
    automation = WebTechAutomation(headless=headless)
    
    if automation.login(username=username, password=password):
        return automation
    else:
        automation.close()
        raise LoginError("快速登錄失敗")

def quick_publish(title: str, content: str, images: list = None, auto_login: bool = True) -> bool:
    """
    快速發布文章函數
    
    Args:
        title: 文章標題
        content: 文章內容
        images: 圖片列表
        auto_login: 是否自動登錄
        
    Returns:
        bool: 發布是否成功
    """
    with WebTechAutomation() as automation:
        if auto_login:
            if not automation.login():
                return False
        
        return automation.publish_article(title, content, images)

# 版本信息
def get_version() -> str:
    """獲取版本信息"""
    return __version__

def get_info() -> dict:
    """獲取系統信息"""
    return {
        "name": "WebTech Automation",
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "features": [
            "自動登錄系統",
            "AI驗證碼識別",
            "智能重試機制", 
            "文章自動發布",
            "圖片自動上傳",
            "錯誤處理和日志"
        ]
    }

# 模塊級別的快捷方式
__all__ = [
    # 主要類
    'WebTechAutomation',
    'AuthManager', 
    'ArticlePublisher',
    'CaptchaSolver',
    'BaseScraper',
    
    # 配置
    'config',
    'WebTechConfig',
    
    # 異常
    'WebTechError',
    'LoginError',
    'CaptchaError', 
    'PublishError',
    'BrowserError',
    'ElementNotFoundError',
    'RetryExhaustedError',
    'ConfigError',
    
    # 工具函數
    'validate_image_file',
    'resize_image',
    'clean_filename',
    'extract_title_and_content',
    'parse_line_message',
    'log_operation',
    
    # 便捷函數
    'quick_login',
    'quick_publish',
    'get_version',
    'get_info'
]

# 打印歡迎信息（僅在直接導入時）
if __name__ != "__main__":
    print(f"🤖 WebTech Automation v{__version__} 已加載")