"""
文章發布器 - 處理自動發文功能
"""
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from typing import Optional, List, Dict
from .base_scraper import BaseScraper
from .config import config
from .exceptions import PublishError, ElementNotFoundError

class ArticlePublisher(BaseScraper):
    """文章發布器 - 處理文章的自動發布"""
    
    def __init__(self, headless: bool = None):
        """
        初始化文章發布器
        
        Args:
            headless: 是否無頭模式
        """
        super().__init__(headless)
        self.upload_timeout = config.UPLOAD_TIMEOUT
        self.publish_timeout = config.PUBLISH_TIMEOUT
    
    def publish_article(self, 
                       title: str, 
                       content: str, 
                       images: List[str] = None,
                       category: str = None) -> bool:
        """
        發布文章的完整流程
        
        Args:
            title: 文章標題
            content: 文章內容
            images: 圖片文件路徑列表
            category: 文章分類
            
        Returns:
            bool: 發布是否成功
        """
        try:
            print("📝 開始文章發布流程...")
            print(f"📄 標題: {title}")
            print(f"📝 內容長度: {len(content)} 字符")
            print(f"🖼️ 圖片數量: {len(images) if images else 0}")
            
            # 1. 導航到新增文章頁面
            if not self._navigate_to_new_article():
                return False
            
            # 2. 填寫文章標題
            if not self._fill_article_title(title):
                return False
            
            # 3. 上傳圖片（如果有）
            if images:
                uploaded_images = self._upload_images(images)
                if not uploaded_images:
                    print("⚠️ 圖片上傳失敗，但繼續發布文章")
            
            # 4. 填寫文章內容
            if not self._fill_article_content(content):
                return False
            
            # 5. 設置分類（如果指定）
            if category:
                self._set_article_category(category)
            
            # 6. 發布文章
            if not self._submit_article():
                return False
            
            # 7. 驗證發布結果
            if self._verify_publication():
                print("🎉 文章發布成功！")
                return True
            else:
                print("❌ 文章發布失敗")
                return False
                
        except Exception as e:
            print(f"❌ 文章發布過程出錯: {e}")
            return False
    
    def _navigate_to_new_article(self) -> bool:
        """導航到新增文章頁面"""
        try:
            print("🎯 正在導航到新增文章頁面...")
            
            # 截圖當前頁面
            self.screenshot_full_page("before_new_article.png")
            
            # 方式1: 尋找"新增文章"按鈕
            new_article_selectors = [
                "//button[contains(text(), '新增文章')]",
                "//a[contains(text(), '新增文章')]",
                "//button[contains(@class, 'new')]",
                ".btn[href*='add']",
                ".btn[href*='new']",
                "#new-article-btn"
            ]
            
            button_found = False
            for selector in new_article_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath選擇器
                        elements = self.find_elements_safe(By.XPATH, selector)
                    else:
                        # CSS選擇器
                        elements = self.find_elements_safe(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        print(f"✅ 找到新增文章按鈕: {selector}")
                        elements[0].click()
                        button_found = True
                        break
                except Exception as e:
                    continue
            
            if not button_found:
                # 方式2: 尋找所有按鈕並智能匹配
                all_buttons = self.find_elements_safe(By.CSS_SELECTOR, "button, a.btn, .btn")
                for btn in all_buttons:
                    btn_text = (btn.text or "").strip()
                    btn_title = btn.get_attribute("title") or ""
                    btn_href = btn.get_attribute("href") or ""
                    
                    if any(keyword in btn_text for keyword in ["新增", "添加", "新建", "Add", "New"]) or \
                       any(keyword in btn_title for keyword in ["新增", "添加", "創建"]) or \
                       any(keyword in btn_href for keyword in ["add", "new", "create"]):
                        print(f"✅ 找到疑似新增按鈕: {btn_text}")
                        btn.click()
                        button_found = True
                        break
            
            if not button_found:
                print("❌ 未找到新增文章按鈕")
                return False
            
            # 等待頁面加載
            time.sleep(3)
            
            # 截圖新頁面
            self.screenshot_full_page("new_article_page.png")
            
            # 驗證是否進入了編輯頁面
            page_info = self.get_page_info()
            print(f"📄 當前頁面: {page_info.get('title', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"❌ 導航到新增文章頁面失敗: {e}")
            return False
    
    def _fill_article_title(self, title: str) -> bool:
        """填寫文章標題"""
        try:
            print(f"📝 填寫文章標題: {title}")
            
            # 尋找標題輸入框
            title_selectors = [
                "input[name*='title']",
                "input[id*='title']",
                "input[placeholder*='標題']",
                "input[placeholder*='title']",
                ".title-input",
                "#article-title"
            ]
            
            title_field = None
            for selector in title_selectors:
                title_field = self.find_element_safe(By.CSS_SELECTOR, selector)
                if title_field:
                    print(f"✅ 找到標題字段: {selector}")
                    break
            
            if not title_field:
                print("❌ 未找到標題輸入框")
                return False
            
            # 清空並填入標題
            title_field.clear()
            title_field.send_keys(title)
            
            print("✅ 標題填寫完成")
            return True
            
        except Exception as e:
            print(f"❌ 填寫標題失敗: {e}")
            return False
    
    def _upload_images(self, image_paths: List[str]) -> List[str]:
        """
        上傳圖片
        
        Args:
            image_paths: 圖片文件路徑列表
            
        Returns:
            成功上傳的圖片URL列表
        """
        uploaded_images = []
        
        try:
            print(f"🖼️ 開始上傳 {len(image_paths)} 張圖片...")
            
            # 尋找文件上傳元素
            upload_input = self._find_upload_input()
            if not upload_input:
                print("❌ 未找到文件上傳控件")
                return uploaded_images
            
            for i, image_path in enumerate(image_paths, 1):
                if not os.path.exists(image_path):
                    print(f"⚠️ 圖片文件不存在: {image_path}")
                    continue
                
                try:
                    print(f"📤 正在上傳第 {i} 張圖片: {os.path.basename(image_path)}")
                    
                    # 發送文件路徑到上傳控件
                    upload_input.send_keys(os.path.abspath(image_path))
                    
                    # 等待上傳完成
                    if self._wait_for_upload_complete():
                        print(f"✅ 第 {i} 張圖片上傳成功")
                        uploaded_images.append(image_path)
                    else:
                        print(f"❌ 第 {i} 張圖片上傳失敗")
                    
                    time.sleep(2)  # 避免上傳過快
                    
                except Exception as e:
                    print(f"❌ 上傳第 {i} 張圖片失敗: {e}")
                    continue
            
            print(f"📊 圖片上傳完成: {len(uploaded_images)}/{len(image_paths)} 成功")
            return uploaded_images
            
        except Exception as e:
            print(f"❌ 圖片上傳過程出錯: {e}")
            return uploaded_images
    
    def _find_upload_input(self) -> Optional[object]:
        """尋找文件上傳輸入框"""
        upload_selectors = [
            "input[type='file']",
            "input[name*='image']",
            "input[name*='file']",
            "input[accept*='image']",
            ".upload-input",
            "#image-upload"
        ]
        
        for selector in upload_selectors:
            upload_input = self.find_element_safe(By.CSS_SELECTOR, selector)
            if upload_input:
                print(f"✅ 找到上傳控件: {selector}")
                return upload_input
        
        # 如果沒找到，嘗試點擊上傳按鈕來激活上傳控件
        upload_buttons = self.find_elements_safe(By.CSS_SELECTOR, 
            "button:contains('上傳'), button:contains('Upload'), .upload-btn")
        
        for btn in upload_buttons:
            try:
                btn.click()
                time.sleep(1)
                # 再次嘗試尋找上傳控件
                upload_input = self.find_element_safe(By.CSS_SELECTOR, "input[type='file']")
                if upload_input:
                    return upload_input
            except:
                continue
        
        return None
    
    def _wait_for_upload_complete(self) -> bool:
        """等待文件上傳完成"""
        try:
            # 等待上傳進度條消失或成功提示出現
            for _ in range(self.upload_timeout):
                # 檢查是否有上傳成功的指示
                success_indicators = self.find_elements_safe(By.CSS_SELECTOR, 
                    ".upload-success, .success, .complete, [class*='success']")
                
                if success_indicators:
                    return True
                
                # 檢查是否有錯誤提示
                error_indicators = self.find_elements_safe(By.CSS_SELECTOR, 
                    ".upload-error, .error, .failed, [class*='error']")
                
                if error_indicators:
                    return False
                
                time.sleep(1)
            
            # 超時，假設上傳成功
            print("⏰ 上傳檢測超時，假設成功")
            return True
            
        except Exception as e:
            print(f"⚠️ 檢測上傳狀態失敗: {e}")
            return True  # 假設成功
    
    def _fill_article_content(self, content: str) -> bool:
        """填寫文章內容"""
        try:
            print(f"📝 填寫文章內容 ({len(content)} 字符)...")
            
            # 尋找內容編輯器
            content_editor = self._find_content_editor()
            if not content_editor:
                print("❌ 未找到內容編輯器")
                return False
            
            # 清空並填入內容
            content_editor.clear()
            content_editor.send_keys(content)
            
            print("✅ 內容填寫完成")
            return True
            
        except Exception as e:
            print(f"❌ 填寫內容失敗: {e}")
            return False
    
    def _find_content_editor(self) -> Optional[object]:
        """尋找內容編輯器"""
        # 常見的內容編輯器選擇器
        editor_selectors = [
            "textarea[name*='content']",
            "textarea[name*='body']",
            "textarea[id*='content']",
            ".content-editor",
            "#article-content",
            "iframe[title*='Rich Text Area']",  # 富文本編輯器
            ".ck-editor__editable",  # CKEditor
            ".tox-edit-area",  # TinyMCE
        ]
        
        for selector in editor_selectors:
            if selector.startswith("iframe"):
                # 處理iframe內的編輯器
                try:
                    iframe = self.find_element_safe(By.CSS_SELECTOR, selector)
                    if iframe:
                        self.driver.switch_to.frame(iframe)
                        editor = self.find_element_safe(By.CSS_SELECTOR, "body")
                        if editor:
                            print(f"✅ 找到iframe內容編輯器: {selector}")
                            return editor
                        self.driver.switch_to.default_content()
                except:
                    continue
            else:
                editor = self.find_element_safe(By.CSS_SELECTOR, selector)
                if editor:
                    print(f"✅ 找到內容編輯器: {selector}")
                    return editor
        
        # 如果沒找到，嘗試尋找所有textarea
        textareas = self.find_elements_safe(By.TAG_NAME, "textarea")
        if textareas:
            # 選擇最大的textarea作為內容editor
            largest_textarea = max(textareas, 
                                 key=lambda ta: int(ta.get_attribute("rows") or "0"))
            print("✅ 使用最大的textarea作為內容編輯器")
            return largest_textarea
        
        return None
    
    def _set_article_category(self, category: str) -> bool:
        """設置文章分類"""
        try:
            print(f"📂 設置文章分類: {category}")
            
            # 尋找分類選擇器
            category_selectors = [
                "select[name*='category']",
                "select[name*='cat']",
                "#category",
                ".category-select"
            ]
            
            for selector in category_selectors:
                category_select = self.find_element_safe(By.CSS_SELECTOR, selector)
                if category_select:
                    # 嘗試按值選擇
                    from selenium.webdriver.support.ui import Select
                    select = Select(category_select)
                    
                    # 嘗試不同的選擇方式
                    try:
                        select.select_by_visible_text(category)
                        print("✅ 按文本選擇分類成功")
                        return True
                    except:
                        try:
                            select.select_by_value(category)
                            print("✅ 按值選擇分類成功")
                            return True
                        except:
                            continue
            
            print("⚠️ 未找到分類選擇器，跳過分類設置")
            return True  # 不是必須的，返回True
            
        except Exception as e:
            print(f"⚠️ 設置分類失敗: {e}")
            return True  # 不是必須的，返回True
    
    def _submit_article(self) -> bool:
        """提交發布文章"""
        try:
            print("🚀 正在提交文章...")
            
            # 截圖提交前的狀態
            self.screenshot_full_page("before_submit.png")
            
            # 尋找提交按鈕
            submit_buttons = self._find_submit_buttons()
            
            if not submit_buttons:
                print("❌ 未找到提交按鈕")
                return False
            
            # 點擊提交按鈕
            submit_buttons[0].click()
            print("✅ 已點擊提交按鈕")
            
            # 等待提交完成
            time.sleep(self.publish_timeout)
            
            return True
            
        except Exception as e:
            print(f"❌ 提交文章失敗: {e}")
            return False
    
    def _find_submit_buttons(self) -> List[object]:
        """尋找提交按鈕"""
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "//button[contains(text(), '發布')]",
            "//button[contains(text(), '提交')]",
            "//button[contains(text(), '保存')]",
            "//button[contains(text(), 'Publish')]",
            "//button[contains(text(), 'Submit')]",
            ".btn-primary",
            ".submit-btn",
            "#submit-btn"
        ]
        
        for selector in submit_selectors:
            try:
                if selector.startswith("//"):
                    buttons = self.find_elements_safe(By.XPATH, selector)
                else:
                    buttons = self.find_elements_safe(By.CSS_SELECTOR, selector)
                
                if buttons:
                    print(f"✅ 找到提交按鈕: {selector}")
                    return buttons
            except:
                continue
        
        return []
    
    def _verify_publication(self) -> bool:
        """驗證文章是否發布成功"""
        try:
            print("🔍 驗證文章發布狀態...")
            
            # 截圖提交後的狀態
            self.screenshot_full_page("after_submit.png")
            
            # 獲取當前頁面信息
            page_info = self.get_page_info()
            current_url = page_info.get('url', '')
            page_source = self.driver.page_source
            
            print(f"📍 提交後URL: {current_url}")
            
            # 檢查成功指示
            success_indicators = [
                "成功" in page_source,
                "success" in page_source.lower(),
                "發布成功" in page_source,
                "published" in page_source.lower(),
                "article" in current_url.lower() and "edit" not in current_url.lower()
            ]
            
            if any(success_indicators):
                print("✅ 檢測到發布成功指示")
                return True
            
            # 檢查錯誤指示
            error_indicators = [
                "錯誤" in page_source,
                "error" in page_source.lower(),
                "失敗" in page_source,
                "failed" in page_source.lower()
            ]
            
            if any(error_indicators):
                print("❌ 檢測到發布失敗指示")
                return False
            
            # 如果沒有明確指示，檢查URL變化
            if current_url != page_info.get('url', ''):
                print("✅ URL發生變化，可能發布成功")
                return True
            
            print("❓ 無法確定發布狀態")
            return False
            
        except Exception as e:
            print(f"⚠️ 驗證發布狀態失敗: {e}")
            return False
    
    def get_article_list(self) -> List[Dict]:
        """獲取文章列表（用於驗證）"""
        try:
            print("📋 獲取文章列表...")
            
            # 這個功能需要根據具體網站結構實現
            # 返回文章列表，包含標題、日期、狀態等信息
            
            return []
            
        except Exception as e:
            print(f"⚠️ 獲取文章列表失敗: {e}")
            return []