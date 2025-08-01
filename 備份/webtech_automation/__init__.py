"""
WebTech 自動化系統

一個完整的網站自動登錄和文章發布自動化解決方案
"""

__version__ = "1.0.0"
__author__ = "WebTech Automation Team"
__description__ = "WebTech網站自動化系統 - 支持自動登錄、驗證碼識別、文章發布"

# 修復導入問題 - 使用 try-except 來處理導入錯誤
try:
    from .main import WebTechAutomation
except ImportError:
    # 如果相對導入失敗，嘗試絕對導入
    try:
        from webtech_automation.main import WebTechAutomation
    except ImportError:
        WebTechAutomation = None
        print("⚠️ WebTechAutomation 導入失敗")

try:
    from .auth_manager import AuthManager
except ImportError:
    try:
        from webtech_automation.auth_manager import AuthManager
    except ImportError:
        AuthManager = None

try:
    from .article_publisher import ArticlePublisher
except ImportError:
    try:
        from webtech_automation.article_publisher import ArticlePublisher
    except ImportError:
        ArticlePublisher = None

try:
    from .captcha_solver import CaptchaSolver
except ImportError:
    try:
        from webtech_automation.captcha_solver import CaptchaSolver
    except ImportError:
        CaptchaSolver = None

try:
    from .base_scraper import BaseScraper
except ImportError:
    try:
        from webtech_automation.base_scraper import BaseScraper
    except ImportError:
        BaseScraper = None

try:
    from .config import config, WebTechConfig
except ImportError:
    try:
        from webtech_automation.config import config, WebTechConfig
    except ImportError:
        config = None
        WebTechConfig = None

# 導出異常類
try:
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
except ImportError:
    # 如果無法導入異常類，創建基本的異常類
    class WebTechError(Exception):
        pass
    
    class LoginError(WebTechError):
        pass
    
    class CaptchaError(WebTechError):
        pass
    
    class PublishError(WebTechError):
        pass
    
    class BrowserError(WebTechError):
        pass
    
    class ElementNotFoundError(WebTechError):
        pass
    
    class RetryExhaustedError(WebTechError):
        pass
    
    class ConfigError(WebTechError):
        pass

# 導出工具函數
try:
    from .utils import (
        validate_image_file,
        resize_image,
        clean_filename,
        extract_title_and_content,
        parse_line_message,
        log_operation
    )
except ImportError:
    # 如果無法導入工具函數，提供基本實現
    def parse_line_message(message_text):
        """基本的消息解析函數"""
        result = {'title': '', 'content': '', 'category': '', 'tags': []}
        lines = message_text.strip().split('\n')
        if lines:
            result['title'] = lines[0]
            result['content'] = '\n'.join(lines[1:]) if len(lines) > 1 else ""
        return result
    
    def log_operation(operation, success, details=""):
        """基本的日志函數"""
        status = "✅" if success else "❌"
        print(f"{status} {operation}: {details}")
    
    # 其他工具函數設為None
    validate_image_file = None
    resize_image = None
    clean_filename = None
    extract_title_and_content = None

# 便捷函數
def quick_login(username=None, password=None, headless=False):
    """
    快速登錄函數
    
    Args:
        username: 用戶名
        password: 密碼  
        headless: 是否無頭模式
        
    Returns:
        WebTechAutomation實例
    """
    if WebTechAutomation is None:
        raise ImportError("WebTechAutomation 類無法導入")
    
    automation = WebTechAutomation(headless=headless)
    
    if automation.login(username=username, password=password):
        return automation
    else:
        automation.close()
        raise LoginError("快速登錄失敗")

def quick_publish(title, content, images=None, auto_login=True):
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
    if WebTechAutomation is None:
        raise ImportError("WebTechAutomation 類無法導入")
    
    with WebTechAutomation() as automation:
        if auto_login:
            if not automation.login():
                return False
        
        return automation.publish_article(title, content, images)

# 版本信息
def get_version():
    """獲取版本信息"""
    return __version__

def get_info():
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

# 檢查導入狀態
def check_imports():
    """檢查所有模塊導入狀態"""
    modules = {
        'WebTechAutomation': WebTechAutomation,
        'AuthManager': AuthManager,
        'ArticlePublisher': ArticlePublisher,
        'CaptchaSolver': CaptchaSolver,
        'BaseScraper': BaseScraper,
        'config': config
    }
    
    print("📋 模塊導入狀態檢查:")
    for name, module in modules.items():
        status = "✅" if module is not None else "❌"
        print(f"  {status} {name}")
    
    return all(module is not None for module in modules.values())

# 打印歡迎信息（僅在直接導入時）
if __name__ != "__main__":
    print(f"🤖 WebTech Automation v{__version__} 已加載")
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