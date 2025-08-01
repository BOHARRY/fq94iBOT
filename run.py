# run.py

import time

# 從我們的模組中導入爬蟲類別和設定
from scraper import SeleniumScraper
import config

def display_login_report(success):
    """根據登錄結果顯示報告。"""
    print("\n" + "="*60)
    if success:
        print("✅✅✅ 登錄成功 ✅✅✅")
        print("="*60)
    else:
        print("❌❌❌ 登錄失敗 ❌❌❌")
        print("="*60)
        print("所有重試機會都已用盡，未能成功登錄。")
        print("\n🔍 可能的原因:")
        print("  1. 帳號或密碼錯誤 (請檢查 config.py)。")
        print("  2. AI 持續無法正確識別驗證碼。")
        print("  3. 網站結構發生變化 (可能需要更新 config.py 中的選擇器)。")
        print("  4. 網路問題或網站防火牆攔截。")

def main():
    """主執行函數"""
    print("🤖 啟動智能自動化機器人")
    print(f"🎯 目標網址: {config.LOGIN_URL}")
    print(f"👤 用戶名: {config.USERNAME}")
    
    scraper = None
    try:
        # 1. 初始化爬蟲
        scraper = SeleniumScraper()
        
        # 2. 執行登錄流程
        login_successful = scraper.login_process()
        
        # 3. 顯示登錄結果報告
        display_login_report(login_successful)

        # 4. 如果登錄成功，執行發文流程
        if login_successful:
            post_successful = scraper.post_new_article()
            
            if post_successful:
                print("\n🎉🎉🎉 恭喜！已成功自動發布新文章！")
            else:
                print("\n😭😭😭 遺憾！文章發布流程失敗。")
                print("   請檢查 'post_error_page.png' 截圖以分析原因。")

            # 可選：保持瀏覽器開啟以便手動檢查
            keep_open = input("\n❓ 是否保持瀏覽器開啟以便手動操作？(y/n，默認10秒後自動關閉): ").strip().lower()
            if keep_open in ['y', 'yes']:
                input("  - 瀏覽器將保持開啟，按 Enter 鍵關閉...")
            else:
                print("  - 10秒後將自動關閉瀏覽器...")
                time.sleep(10)

    except KeyboardInterrupt:
        print("\n\n⚠️ 用戶手動中斷操作。")
    except Exception as e:
        print(f"\n\n💥 程序發生未預期的致命錯誤: {e}")
        if scraper:
            scraper.screenshot_full_page("fatal_error.png")
    finally:
        if scraper:
            scraper.close()
        print("🏁 程序執行完畢。")

if __name__ == "__main__":
    main()