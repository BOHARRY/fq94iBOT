"""
通用工具函數
"""
import os
import re
import time
import base64
from datetime import datetime
from typing import List, Dict, Optional, Union
from PIL import Image

def validate_image_file(file_path: str) -> bool:
    """
    驗證圖片文件是否有效
    
    Args:
        file_path: 圖片文件路徑
        
    Returns:
        bool: 文件是否有效
    """
    if not os.path.exists(file_path):
        return False
    
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False

def resize_image(input_path: str, output_path: str, max_size: tuple = (1920, 1080)) -> bool:
    """
    調整圖片大小
    
    Args:
        input_path: 輸入圖片路徑
        output_path: 輸出圖片路徑
        max_size: 最大尺寸 (width, height)
        
    Returns:
        bool: 是否成功
    """
    try:
        with Image.open(input_path) as img:
            # 計算新尺寸
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 保存
            img.save(output_path, optimize=True, quality=85)
            
        return True
    except Exception as e:
        print(f"❌ 調整圖片大小失敗: {e}")
        return False

def clean_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理後的文件名
    """
    # 移除非法字符
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # 限制長度
    if len(cleaned) > 100:
        name, ext = os.path.splitext(cleaned)
        cleaned = name[:96] + ext
    
    return cleaned

def extract_title_and_content(text: str) -> tuple:
    """
    從文本中提取標題和內容
    
    Args:
        text: 原始文本
        
    Returns:
        tuple: (標題, 內容)
    """
    lines = text.strip().split('\n')
    
    if not lines:
        return "無標題", ""
    
    # 第一行作為標題
    title = lines[0].strip()
    
    # 如果標題太長，截取前50個字符
    if len(title) > 50:
        title = title[:47] + "..."
    
    # 剩餘行作為內容
    content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
    
    return title, content

def format_timestamp(timestamp: float = None) -> str:
    """
    格式化時間戳
    
    Args:
        timestamp: 時間戳，None則使用當前時間
        
    Returns:
        格式化的時間字符串
    """
    if timestamp is None:
        timestamp = time.time()
    
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def create_backup_filename(original_filename: str) -> str:
    """
    創建備份文件名
    
    Args:
        original_filename: 原始文件名
        
    Returns:
        備份文件名
    """
    name, ext = os.path.splitext(original_filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{name}_backup_{timestamp}{ext}"

def ensure_directory(directory: str) -> bool:
    """
    確保目錄存在
    
    Args:
        directory: 目錄路徑
        
    Returns:
        bool: 是否成功
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        print(f"❌ 創建目錄失敗 {directory}: {e}")
        return False

def get_file_size_mb(file_path: str) -> float:
    """
    獲取文件大小（MB）
    
    Args:
        file_path: 文件路徑
        
    Returns:
        文件大小（MB）
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0

def is_image_file(file_path: str) -> bool:
    """
    檢查是否為圖片文件
    
    Args:
        file_path: 文件路徑
        
    Returns:
        bool: 是否為圖片文件
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    
    if not os.path.exists(file_path):
        return False
    
    ext = os.path.splitext(file_path)[1].lower()
    return ext in image_extensions

def compress_image(input_path: str, output_path: str = None, quality: int = 85) -> Optional[str]:
    """
    壓縮圖片
    
    Args:
        input_path: 輸入圖片路徑
        output_path: 輸出路徑，None則覆蓋原文件
        quality: 壓縮質量 (1-100)
        
    Returns:
        壓縮後的文件路徑或None
    """
    try:
        if output_path is None:
            output_path = input_path
        
        with Image.open(input_path) as img:
            # 轉換為RGB（如果是RGBA）
            if img.mode == 'RGBA':
                # 創建白色背景
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[-1])  # 使用alpha通道作為mask
                img = bg
            
            # 壓縮保存
            img.save(output_path, 'JPEG', optimize=True, quality=quality)
        
        return output_path
    except Exception as e:
        print(f"❌ 壓縮圖片失敗: {e}")
        return None

def safe_filename_from_title(title: str, max_length: int = 50) -> str:
    """
    從標題生成安全的文件名
    
    Args:
        title: 文章標題
        max_length: 最大長度
        
    Returns:
        安全的文件名
    """
    # 移除HTML標籤
    clean_title = re.sub(r'<[^>]+>', '', title)
    
    # 移除特殊字符
    clean_title = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', clean_title)
    
    # 替換空格為下劃線
    clean_title = re.sub(r'\s+', '_', clean_title.strip())
    
    # 限制長度
    if len(clean_title) > max_length:
        clean_title = clean_title[:max_length]
    
    # 如果為空，使用默認名稱
    if not clean_title:
        clean_title = "untitled"
    
    return clean_title

def parse_line_message(message_text: str) -> Dict[str, str]:
    """
    解析Line消息內容
    
    Args:
        message_text: Line消息文本
        
    Returns:
        解析結果字典
    """
    result = {
        'title': '',
        'content': '',
        'category': '',
        'tags': []
    }
    
    lines = message_text.strip().split('\n')
    
    if not lines:
        return result
    
    # 解析特殊標記
    for i, line in enumerate(lines):
        line = line.strip()
        
        if line.startswith('#標題:') or line.startswith('#title:'):
            result['title'] = line.split(':', 1)[1].strip()
        elif line.startswith('#分類:') or line.startswith('#category:'):
            result['category'] = line.split(':', 1)[1].strip()
        elif line.startswith('#標籤:') or line.startswith('#tags:'):
            tags_str = line.split(':', 1)[1].strip()
            result['tags'] = [tag.strip() for tag in tags_str.split(',')]
        else:
            # 普通內容行
            if not result['title'] and not line.startswith('#'):
                # 如果還沒有標題，且不是特殊標記，則作為標題
                result['title'] = line
            elif line and not line.startswith('#'):
                # 作為內容
                if result['content']:
                    result['content'] += '\n' + line
                else:
                    result['content'] = line
    
    # 如果沒有明確的標題，使用內容的第一行
    if not result['title'] and result['content']:
        content_lines = result['content'].split('\n')
        if content_lines:
            result['title'] = content_lines[0][:50]  # 限制標題長度
            result['content'] = '\n'.join(content_lines[1:]) if len(content_lines) > 1 else ""
    
    return result

def log_operation(operation: str, success: bool, details: str = ""):
    """
    記錄操作日志
    
    Args:
        operation: 操作名稱
        success: 是否成功
        details: 詳細信息
    """
    timestamp = format_timestamp()
    status = "✅ 成功" if success else "❌ 失敗"
    
    log_entry = f"[{timestamp}] {operation} - {status}"
    if details:
        log_entry += f" - {details}"
    
    print(log_entry)
    
    # 可選：寫入日志文件
    try:
        with open("webtech_automation.log", "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    except Exception:
        pass  # 日志寫入失敗不影響主流程

def retry_on_failure(func, max_retries: int = 3, delay: float = 1.0):
    """
    重試裝飾器函數
    
    Args:
        func: 要重試的函數
        max_retries: 最大重試次數
        delay: 重試間隔
        
    Returns:
        裝飾器函數
    """
    def wrapper(*args, **kwargs):
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    print(f"⚠️ 第 {attempt + 1} 次嘗試失敗，{delay}秒後重試: {e}")
                    time.sleep(delay)
                else:
                    print(f"❌ 所有重試都失敗了: {e}")
        
        raise last_exception
    
    return wrapper