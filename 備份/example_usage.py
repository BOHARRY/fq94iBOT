"""
WebTech 自動化系統使用示例

這個文件展示了如何使用重構後的WebTech自動化系統
"""
import time
from webtech_automation import (
    WebTechAutomation, 
    quick_login, 
    quick_publish,
    get_info,
    parse_line_message
)

def example_1_basic_login():
    """示例1：基本登錄功能"""
    print("🚀 示例1：基本登錄功能")
    print("-" * 40)
    
    # 使用默認配置登錄
    with WebTechAutomation() as automation:
        success = automation.login()
        
        if success:
            print("✅ 登錄成功！")
            current_url = automation.get_current_url()
            print(f"🌐 當前頁面: {current_url}")
            
            # 截圖當前頁面
            automation.screenshot("example_login_success.png")
            
        else:
            print("❌ 登錄失敗！")

def example_2_custom_login():
    """示例2：自定義登錄參數"""
    print("🚀 示例2：自定義登錄參數")
    print("-" * 40)
    
    # 自定義登錄參數
    custom_automation = WebTechAutomation(headless=True)  # 無頭模式
    
    try:
        success = custom_automation.login(
            url="https://www.fq94i.com/webtech",
            username="your_username",
            password="your_password",
            max_retries=3
        )
        
        if success:
            print("✅ 自定義登錄成功！")
        else:
            print("❌ 自定義登錄失敗！")
            
    finally:
        custom_automation.close()

def example_3_quick_login():
    """示例3：快速登錄函數"""
    print("🚀 示例3：快速登錄函數")
    print("-" * 40)
    
    try:
        # 使用便捷函數快速登錄
        automation = quick_login(headless=False)
        
        print("✅ 快速登錄成功！")
        print(f"🌐 當前URL: {automation.get_current_url()}")
        
        # 記得關閉
        automation.close()
        
    except Exception as e:
        print(f"❌ 快速登錄失敗: {e}")

def example_4_publish_article():
    """示例4：發布文章"""
    print("🚀 示例4：發布文章")
    print("-" * 40)
    
    with WebTechAutomation() as automation:
        # 先登錄
        if not automation.login():
            print("❌ 登錄失敗，無法發布文章")
            return
        
        # 準備文章內容
        title = "測試文章標題"
        content = """這是一篇測試文章的內容。

        文章包含多個段落：
        1. 第一段內容
        2. 第二段內容
        3. 結論段落
        
        發布時間: """ + time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 可選：包含圖片
        images = []  # ["path/to/image1.jpg", "path/to/image2.png"]
        
        # 發布文章
        success = automation.publish_article(
            title=title,
            content=content,
            images=images,
            category="測試分類"
        )
        
        if success:
            print("✅ 文章發布成功！")
        else:
            print("❌ 文章發布失敗！")

def example_5_auto_login_and_publish():
    """示例5：一鍵登錄並發布"""
    print("🚀 示例5：一鍵登錄並發布")
    print("-" * 40)
    
    with WebTechAutomation() as automation:
        # 一鍵完成登錄和發布
        success = automation.auto_login_and_publish(
            title="自動化發布測試",
            content="這是通過自動化系統一鍵發布的文章",
            images=None,
            category="自動化測試"
        )
        
        if success:
            print("✅ 一鍵發布成功！")
        else:
            print("❌ 一鍵發布失敗！")

def example_6_quick_publish():
    """示例6：快速發布函數"""
    print("🚀 示例6：快速發布函數")
    print("-" * 40)
    
    # 使用便捷函數快速發布
    success = quick_publish(
        title="快速發布測試",
        content="使用快速發布函數發布的文章",
        auto_login=True
    )
    
    if success:
        print("✅ 快速發布成功！")
    else:
        print("❌ 快速發布失敗！")

def example_7_parse_line_message():
    """示例7：解析Line消息"""
    print("🚀 示例7：解析Line消息格式")
    print("-" * 40)
    
    # 模擬Line Bot收到的消息
    line_message = """#標題: 今天的工作總結
    
    今天完成了以下工作：
    1. 完成了系統重構
    2. 編寫了使用文檔
    3. 測試了所有功能
    
    #分類: 工作日誌
    #標籤: 工作, 總結, 開發"""
    
    # 解析消息
    parsed = parse_line_message(line_message)
    
    print("📝 解析結果:")
    print(f"  標題: {parsed['title']}")
    print(f"  內容: {parsed['content'][:50]}...")
    print(f"  分類: {parsed['category']}")
    print(f"  標籤: {parsed['tags']}")
    
    # 可以直接用於發布
    # quick_publish(parsed['title'], parsed['content'])

def example_8_batch_operations():
    """示例8：批量操作"""
    print("🚀 示例8：批量操作")
    print("-" * 40)
    
    # 準備多篇文章
    articles = [
        {
            "title": "文章1: 系統介紹",
            "content": "這是第一篇介紹性文章...",
            "category": "介紹"
        },
        {
            "title": "文章2: 使用教程", 
            "content": "這是第二篇教程文章...",
            "category": "教程"
        },
        {
            "title": "文章3: 常見問題",
            "content": "這是第三篇FAQ文章...",
            "category": "FAQ"
        }
    ]
    
    with WebTechAutomation() as automation:
        # 只需要登錄一次
        if not automation.login():
            print("❌ 登錄失敗，終止批量操作")
            return
        
        success_count = 0
        
        for i, article in enumerate(articles, 1):
            print(f"\n📝 發布第 {i} 篇文章: {article['title']}")
            
            success = automation.publish_article(
                title=article['title'],
                content=article['content'],
                category=article.get('category')
            )
            
            if success:
                success_count += 1
                print(f"✅ 第 {i} 篇文章發布成功")
            else:
                print(f"❌ 第 {i} 篇文章發布失敗")
            
            # 避免發布太快
            time.sleep(5)
        
        print(f"\n📊 批量發布完成: {success_count}/{len(articles)} 篇成功")

def example_9_error_handling():
    """示例9：錯誤處理"""
    print("🚀 示例9：錯誤處理")
    print("-" * 40)
    
    from webtech_automation.exceptions import LoginError, PublishError
    
    try:
        with WebTechAutomation() as automation:
            # 嘗試使用錯誤的登錄信息
            success = automation.login(
                username="wrong_user",
                password="wrong_pass",
                max_retries=2
            )
            
            if not success:
                raise LoginError("登錄失敗")
                
    except LoginError as e:
        print(f"🔴 登錄錯誤: {e}")
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")
    
    print("✅ 錯誤處理演示完成")

def example_10_system_info():
    """示例10：系統信息"""
    print("🚀 示例10：系統信息")
    print("-" * 40)
    
    # 獲取系統信息
    info = get_info()
    
    print(f"📋 系統名稱: {info['name']}")
    print(f"🔖 版本: {info['version']}")
    print(f"👨‍💻 作者: {info['author']}")
    print(f"📝 描述: {info['description']}")
    print("🎯 主要功能:")
    for feature in info['features']:
        print(f"  - {feature}")

def main():
    """主函數 - 運行所有示例"""
    print("🤖 WebTech 自動化系統 - 使用示例集合")
    print("=" * 60)
    
    examples = [
        ("基本登錄", example_1_basic_login),
        ("自定義登錄", example_2_custom_login),
        ("快速登錄", example_3_quick_login),
        ("發布文章", example_4_publish_article),
        ("一鍵發布", example_5_auto_login_and_publish),
        ("快速發布", example_6_quick_publish),
        ("消息解析", example_7_parse_line_message),
        ("批量操作", example_8_batch_operations),
        ("錯誤處理", example_9_error_handling),
        ("系統信息", example_10_system_info)
    ]
    
    print("📋 可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    try:
        choice = input("\n請選擇要運行的示例 (1-10, 或 'all' 運行所有示例): ").strip()
        
        if choice.lower() == 'all':
            print("\n🚀 運行所有示例...\n")
            for name, example_func in examples:
                print(f"\n{'='*20} {name} {'='*20}")
                try:
                    example_func()
                except Exception as e:
                    print(f"❌ 示例 '{name}' 運行失敗: {e}")
                print("-" * 60)
        else:
            try:
                index = int(choice) - 1
                if 0 <= index < len(examples):
                    name, example_func = examples[index]
                    print(f"\n🚀 運行示例: {name}\n")
                    example_func()
                else:
                    print("❌ 無效的選擇")
            except ValueError:
                print("❌ 請輸入有效的數字")
                
    except KeyboardInterrupt:
        print("\n\n⚠️ 用戶中斷操作")
    except Exception as e:
        print(f"\n❌ 運行示例時出錯: {e}")
    
    print("\n🔒 示例演示結束")

if __name__ == "__main__":
    main()