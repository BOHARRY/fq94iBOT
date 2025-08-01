"""
WebTech 自動化系統主程序
"""
import time
import sys
from typing import List, Optional
from .config import config
from .auth_manager import AuthManager
from .article_publisher import ArticlePublisher
from .exceptions import WebTechError

class WebTechAutomation:
    """WebTech自動化系統主類"""
    
    def __init__(self, headless: bool = None, openai_api_key: str = None):
        """
        初始化自動化系統
        
        Args:
            headless: 是否無頭模式
            openai_api_key: OpenAI API密鑰
        """
        self.headless = headless if headless is not None else config.HEADLESS
        self.openai_api_key = openai_api_key or config.OPENAI_API_KEY
        
        # 初始化管理器（延遲初始化）
        self.auth_manager: Optional[AuthManager] = None
        self.article_publisher: Optional[ArticlePublisher] = None
        self.is_logged_in = False
    
    def login(self, 
              url: str = None, 
              username: str = None, 
              password: str = None,
              max_retries: int = None) -> bool:
        """
        登錄系統
        
        Args:
            url: 登錄URL
            username: 用戶名
            password: 密碼
            max_retries: 最大重試次數
            
        Returns:
            bool: 登錄是否成功
        """
        try:
            if not self.auth_manager:
                self.auth_manager = AuthManager(self.headless, self.openai_api_key)
            
            print("🔐 開始登錄流程...")
            success = self.auth_manager.login_with_retry(url, username, password, max_retries)
            
            if success:
                self.is_logged_in = True
                print("✅ 登錄成功！")
                
                # 保存登錄後的頁面內容
                self._save_login_content()
                
                return True
            else:
                print("❌ 登錄失敗！")
                return False
                
        except Exception as e:
            print(f"❌ 登錄過程出錯: {e}")
            return False
    
    def publish_article(self, 
                       title: str, 
                       content: str, 
                       images: List[str] = None,
                       category: str = None) -> bool:
        """
        發布文章
        
        Args:
            title: 文章標題
            content: 文章內容
            images: 圖片文件路徑列表
            category: 文章分類
            
        Returns:
            bool: 發布是否成功
        """
        try:
            # 檢查是否已登錄
            if not self.is_logged_in:
                print("⚠️ 尚未登錄，先執行登錄流程...")
                if not self.login():
                    return False
            
            # 初始化文章發布器（使用現有的瀏覽器會話）
            if not self.article_publisher:
                if self.auth_manager:
                    # 使用相同的瀏覽器實例
                    self.article_publisher = ArticlePublisher(self.headless)
                    self.article_publisher.driver = self.auth_manager.driver
                    self.article_publisher.wait = self.auth_manager.wait
                else:
                    self.article_publisher = ArticlePublisher(self.headless)
            
            print("📝 開始文章發布流程...")
            success = self.article_publisher.publish_article(title, content, images, category)
            
            if success:
                print("🎉 文章發布成功！")
                return True
            else:
                print("❌ 文章發布失敗！")
                return False
                
        except Exception as e:
            print(f"❌ 文章發布過程出錯: {e}")
            return False
    
    def auto_login_and_publish(self, 
                              title: str, 
                              content: str, 
                              images: List[str] = None,
                              category: str = None) -> bool:
        """
        自動登錄並發布文章的完整流程
        
        Args:
            title: 文章標題
            content: 文章內容
            images: 圖片文件路徑列表
            category: 文章分類
            
        Returns:
            bool: 整個流程是否成功
        """
        try:
            print("🚀 開始自動登錄並發布文章流程...")
            
            # 1. 登錄
            if not self.login():
                return False
            
            # 2. 發布文章
            if not self.publish_article(title, content, images, category):
                return False
            
            print("🎉 自動發文流程完成！")
            return True
            
        except Exception as e:
            print(f"❌ 自動發文流程出錯: {e}")
            return False
    
    def _save_login_content(self):
        """保存登錄後的頁面內容"""
        try:
            if self.auth_manager and self.auth_manager.driver:
                page_content = self.auth_manager.driver.page_source
                
                with open("logged_in_content.html", "w", encoding="utf-8") as f:
                    f.write(page_content)
                print(f"💾 登錄後頁面內容已保存 ({len(page_content)} 字符)")
        except Exception as e:
            print(f"⚠️ 保存頁面內容失敗: {e}")
    
    def get_current_url(self) -> str:
        """獲取當前頁面URL"""
        try:
            if self.auth_manager and self.auth_manager.driver:
                return self.auth_manager.driver.current_url
            elif self.article_publisher and self.article_publisher.driver:
                return self.article_publisher.driver.current_url
            return ""
        except:
            return ""
    
    def screenshot(self, filename: str) -> bool:
        """截圖當前頁面"""
        try:
            if self.auth_manager:
                return self.auth_manager.screenshot_full_page(filename)
            elif self.article_publisher:
                return self.article_publisher.screenshot_full_page(filename)
            return False
        except:
            return False
    
    def close(self):
        """關閉所有資源"""
        try:
            if self.auth_manager:
                self.auth_manager.close()
                print("🔒 登錄管理器已關閉")
            
            if self.article_publisher and self.article_publisher != self.auth_manager:
                self.article_publisher.close()
                print("🔒 文章發布器已關閉")
            
            self.is_logged_in = False
            
        except Exception as e:
            print(f"⚠️ 關閉資源時出錯: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

def main():
    """主程序入口"""
    try:
        print("🤖 WebTech 自動化系統啟動")
        print("="*60)
        
        # 從配置文件讀取設置
        config.validate()
        
        print(f"🎯 目標網址: {config.LOGIN_URL}")
        print(f"👤 用戶名: {config.USERNAME}")
        print(f"🧠 AI驗證碼識別: {'✅ 已啟用' if config.OPENAI_API_KEY else '❌ 未配置'}")
        print(f"🖥️ 瀏覽器模式: {'無頭模式' if config.HEADLESS else '可視模式'}")
        print("="*60)
        
        # 使用上下文管理器
        with WebTechAutomation() as automation:
            
            # 執行登錄
            login_success = automation.login()
            
            if login_success:
                print("\n" + "="*60)
                print("🎉 登錄成功！系統已就緒")
                print("="*60)
                
                # 獲取當前URL
                current_url = automation.get_current_url()
                print(f"🌐 當前頁面: {current_url}")
                
                # 示例：發布測試文章（可選）
                test_mode = input("\n是否發布測試文章？(y/n，默認n): ").strip().lower()
                
                if test_mode in ['y', 'yes']:
                    test_title = "自動化測試文章"
                    test_content = "這是一篇由自動化系統發布的測試文章。\n\n發布時間: " + time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    publish_success = automation.publish_article(test_title, test_content)
                    
                    if publish_success:
                        print("🎉 測試文章發布成功！")
                    else:
                        print("❌ 測試文章發布失敗")
                
                # 保持瀏覽器開啟選項
                keep_open = input("\n是否保持瀏覽器開啟？(y/n，默認5秒後關閉): ").strip().lower()
                
                if keep_open in ['y', 'yes']:
                    print("🖥️ 瀏覽器保持開啟，按 Enter 鍵退出...")
                    input()
                else:
                    print("⏰ 5秒後自動關閉...")
                    for i in range(5, 0, -1):
                        print(f"   {i}...", end="", flush=True)
                        time.sleep(1)
                    print("\n👋 系統關閉")
                    
            else:
                print("\n" + "="*60)
                print("❌ 登錄失敗！系統退出")
                print("="*60)
                
                print("🔍 可能的原因:")
                print("  1. 帳號或密碼錯誤")
                print("  2. 驗證碼識別失敗")
                print("  3. 網站結構發生變化")
                print("  4. 網絡連接問題")
                
                print("\n💡 建議:")
                print("  - 檢查配置文件中的帳號密碼")
                print("  - 查看截圖文件確認頁面狀態")
                print("  - 手動測試網站是否可正常訪問")
                
    except KeyboardInterrupt:
        print("\n\n⚠️ 用戶中斷操作")
    except Exception as e:
        print(f"\n\n❌ 系統執行出錯: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🔒 系統已安全退出")

if __name__ == "__main__":
    main()