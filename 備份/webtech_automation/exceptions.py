"""
WebTech 自動化系統自定義異常
"""

class WebTechError(Exception):
    """WebTech系統基礎異常"""
    pass

class BrowserError(WebTechError):
    """瀏覽器相關錯誤"""
    pass

class LoginError(WebTechError):
    """登錄相關錯誤"""
    pass

class CaptchaError(WebTechError):
    """驗證碼相關錯誤"""
    pass

class ElementNotFoundError(WebTechError):
    """元素未找到錯誤"""
    pass

class PublishError(WebTechError):
    """文章發布相關錯誤"""
    pass

class ConfigError(WebTechError):
    """配置相關錯誤"""
    pass

class RetryExhaustedError(WebTechError):
    """重試次數耗盡錯誤"""
    pass