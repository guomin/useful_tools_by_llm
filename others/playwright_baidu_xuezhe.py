from playwright.sync_api import sync_playwright
import os
import time
from urllib.parse import urlparse

def setup_environment():
    """设置运行环境"""
    os.makedirs("screenshots", exist_ok=True)
    os.makedirs("data", exist_ok=True)

def run_baidu_scholar_search(scholar_name="李彦宏", max_results=3, max_retries=3, page_timeout=30000):
    """在百度学术搜索学者并访问其主页
    
    Args:
        scholar_name (str): 要搜索的学者姓名
        max_results (int): 最多获取的结果数量
        max_retries (int): 搜索框定位最大重试次数
        page_timeout (int): 页面操作超时时间(毫秒)
    """
    setup_environment()
    
    with sync_playwright() as p:
        # 浏览器配置（使用真实Chrome浏览器）
        browser = p.chromium.launch(
            headless=False,  # 设为True可无头运行
            channel="chrome",
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        
        # 浏览器上下文配置
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="zh-CN",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        )
        
        try:
            page = context.new_page()
            
            # 1. 访问百度学术首页
            print("正在访问百度学术...")
            page.goto("https://xueshu.baidu.com/", timeout=page_timeout)
            page.wait_for_load_state("networkidle")
            page.screenshot(path="screenshots/1_scholar_home.png")
            
            # 处理可能出现的弹窗
            try:
                close_button = page.locator("text=我知道了").first
                if close_button.is_visible():
                    close_button.click()
                    print("已关闭提示弹窗")
                    page.wait_for_load_state("networkidle")
            except:
                pass
            
            # 2. 输入搜索关键词 - 使用更健壮的搜索框定位方法
            print(f"正在搜索学者: {scholar_name}...")
            
            # 多选择器搜索框定位尝试
            search_input = None
            selectors = [
                ".main-search .s_ipt",                      # 原选择器
                "#kw",                                      # ID选择器
                "input.s_ipt",                              # 类选择器
                "input[name='wd']",                         # 属性选择器
                "//input[@class='s_ipt']",                  # XPath
                "//div[contains(@class,'main-search')]//input"  # 宽松XPath
            ]
            
            # 重试机制
            for attempt in range(max_retries):
                print(f"尝试定位搜索框 (第{attempt+1}次)")
                page.wait_for_timeout(1000)  # 等待1秒确保页面完全加载
                
                # 尝试各种选择器
                for selector in selectors:
                    try:
                        print(f"尝试选择器: {selector}")
                        # 检查元素是否存在并可见
                        if selector.startswith("//"):  # XPath
                            element = page.locator(f"xpath={selector}")
                        else:
                            element = page.locator(selector)
                            
                        if element.count() > 0 and element.first.is_visible():
                            search_input = element.first
                            print(f"✓ 成功定位搜索框: {selector}")
                            break
                    except Exception as e:
                        print(f"使用选择器 {selector} 定位失败: {str(e)}")
                        continue
                
                if search_input:
                    break
                
                print(f"搜索框定位失败，刷新页面重试...")
                page.reload()
                page.wait_for_load_state("networkidle")
            
            if not search_input:
                # 如果所有尝试都失败，保存更多调试信息
                page.screenshot(path="screenshots/search_box_not_found.png", full_page=True)
                # 保存HTML源码以便检查
                html_content = page.content()
                with open("data/page_source.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                raise Exception("无法定位搜索框，已保存页面源代码供分析")
            
            # 执行搜索
            search_input.fill(scholar_name)
            page.screenshot(path="screenshots/2_before_search.png")
            
            # 尝试定位搜索按钮
            search_buttons = [
                ".main-search .s_btn",
                ".sc_search_btn",
                "#su",
                "//input[@type='submit']",
                "button[type='submit']"
            ]
            
            search_button = None
            for btn_selector in search_buttons:
                try:
                    if btn_selector.startswith("//"):  # XPath
                        btn = page.locator(f"xpath={btn_selector}")
                    else:
                        btn = page.locator(btn_selector)
                        
                    if btn.count() > 0 and btn.first.is_visible():
                        search_button = btn.first
                        print(f"✓ 成功定位搜索按钮: {btn_selector}")
                        break
                except Exception:
                    continue
            
            if not search_button:
                # 如果找不到搜索按钮，尝试按回车键
                print("未找到搜索按钮，尝试按回车键提交搜索")
                search_input.press("Enter")
            else:
                search_button.click()
            
            # 等待搜索结果加载
            print("等待搜索结果加载...")
            try:
                page.wait_for_selector(".sc_content", state="visible", timeout=page_timeout)
            except:
                print("未找到标准结果容器，尝试备用选择器")
                # 尝试备用选择器
                try:
                    page.wait_for_selector(".result", state="visible", timeout=page_timeout)
                    print("已找到备用结果容器")
                except:
                    print("无法识别搜索结果页面，继续尝试提取数据")
                
            page.wait_for_load_state("networkidle")
            page.screenshot(path="screenshots/3_search_results.png", full_page=True)
            
            # 3. 提取学者信息
            print("\n=== 学者搜索结果 ===")
            scholar_results = []
            
            # 首先保存结果页面HTML用于调试
            html_content = page.content()
            with open("data/search_results.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("已保存搜索结果页面HTML到data/search_results.html")
            
            # 首先检查是否存在学者卡片格式 (专门处理多个同名学者的情况)
            scholar_card_exists = page.locator(".op-scholar-authorcard-wr").count() > 0
            
            if scholar_card_exists:
                print("检测到学者卡片格式，提取多位学者信息...")
                try:
                    # 获取所有学者卡片项
                    scholar_items = page.locator(".op-scholar-authorcard-item").all()
                    print(f"找到 {len(scholar_items)} 位学者")
                    
                    for idx, item in enumerate(scholar_items, 1):
                        try:
                            # 提取姓名
                            name_el = item.locator(".op-scholar-authorcard-name").first
                            name = name_el.text_content() if name_el else "未知学者"
                            
                            # 提取机构
                            affil_el = item.locator(".op-scholar-authorcard-info p").first
                            affiliation = affil_el.text_content() if affil_el else "未知机构"
                            
                            # 提取链接
                            link_el = item.locator(".op-scholar-authorcard-name").first
                            profile_url = link_el.get_attribute("href") if link_el else "#"
                            
                            # 处理链接前缀
                            if profile_url and profile_url.startswith("//"):
                                profile_url = "https:" + profile_url
                            
                            scholar_info = {
                                "rank": idx,
                                "name": name.strip() if name else "未知学者",
                                "affiliation": affiliation.strip() if affiliation else "未知机构",
                                "profile_url": profile_url
                            }
                            
                            scholar_results.append(scholar_info)
                            print(f"{idx}. {scholar_info['name']} - {scholar_info['affiliation']}")
                            print(f"   主页链接: {scholar_info['profile_url']}")
                            
                        except Exception as e:
                            print(f"处理第{idx}位学者时出错: {str(e)}")
                            continue
                
                except Exception as e:
                    print(f"处理学者卡片时出错: {str(e)}")
                    # 如果学者卡片处理失败，会继续执行后续的标准结果提取
            
            # 如果没有从学者卡片获取到结果，则使用标准方法提取
            if not scholar_results:
                print("使用标准方法提取搜索结果...")
                # 使用多种选择器尝试提取搜索结果
                result_selectors = [
                    ".sc_content",
                    ".result-item",
                    ".result",
                    "//div[contains(@class, 'result')]",
                    "//div[contains(@class, 'sc_default')]"
                ]
                
                items = []
                successful_selector = None
                
                for selector in result_selectors:
                    try:
                        print(f"尝试使用选择器提取结果: {selector}")
                        if selector.startswith("//"):
                            elements = page.locator(f"xpath={selector}").all()
                        else:
                            elements = page.locator(selector).all()
                        
                        if len(elements) > 0:
                            items = elements
                            successful_selector = selector
                            print(f"✓ 成功找到{len(elements)}个结果项 (使用{selector})")
                            break
                    except Exception as e:
                        print(f"使用选择器 {selector} 提取失败: {str(e)}")
                
                if not items:
                    print("无法找到搜索结果项，尝试直接提取页面作者链接...")
                    # 备选方案：直接查找页面上的作者链接
                    try:
                        author_links = page.locator("a.author_name, a.author_main, a[href*='author']").all()
                        if author_links:
                            print(f"找到 {len(author_links)} 个可能的作者链接")
                            # 继续使用这些链接
                        else:
                            print("未找到任何作者链接")
                    except Exception as e:
                        print(f"提取作者链接失败: {str(e)}")
                
                # 遍历并提取学者信息，增加超时控制和错误处理
                processed_count = 0
                for idx, item in enumerate(items[:max_results], 1):
                    print(f"\n正在处理第{idx}条结果...")
                    try:
                        # 增加更多调试信息
                        try:
                            item_html = item.evaluate("el => el.outerHTML")
                            print(f"结果项HTML结构预览: {item_html[:200]}...")  # 仅显示前200个字符
                        except:
                            print("无法获取结果项HTML")
                        
                        # 使用更灵活的选择器和备选方案
                        name = None
                        affiliation = None
                        profile_url = None
                        
                        # 尝试多种名称选择器
                        name_selectors = [
                            ".author_wr .author_text", 
                            ".author_name",
                            ".author_main",
                            "a[title*='主页']",
                            "//a[contains(@href, 'author')]"
                        ]
                        
                        for name_sel in name_selectors:
                            try:
                                if name_sel.startswith("//"):
                                    name_el = item.locator(f"xpath={name_sel}").first
                                else:
                                    name_el = item.locator(name_sel).first
                                    
                                if name_el and name_el.is_visible(timeout=5000):
                                    name = name_el.text_content(timeout=5000)
                                    print(f"找到作者名: {name} (使用选择器:{name_sel})")
                                    
                                    # 如果找到名字，尝试从同一元素获取链接
                                    try:
                                        profile_url = name_el.get_attribute("href", timeout=5000)
                                        if profile_url:
                                            print(f"从名字元素获取到链接: {profile_url}")
                                    except:
                                        pass
                                    break
                            except Exception as e:
                                print(f"使用选择器 {name_sel} 获取作者名失败: {str(e)}")
                        
                        # 尝试多种机构选择器
                        if name:  # 只有在找到名字后才尝试查找机构
                            affil_selectors = [
                                ".author_wr .author_affiliation",
                                ".author_affiliation", 
                                ".inst",
                                ".organization",
                                "//span[contains(@class, 'affiliation')]"
                            ]
                            
                            for affil_sel in affil_selectors:
                                try:
                                    if affil_sel.startswith("//"):
                                        affil_el = item.locator(f"xpath={affil_sel}").first
                                    else:
                                        affil_el = item.locator(affil_sel).first
                                        
                                    if affil_el and affil_el.is_visible(timeout=5000):
                                        affiliation = affil_el.text_content(timeout=5000)
                                        print(f"找到机构: {affiliation} (使用选择器:{affil_sel})")
                                        break
                                except Exception as e:
                                    print(f"使用选择器 {affil_sel} 获取机构失败: {str(e)}")
                            
                            # 如果仍未找到机构，设置默认值
                            if not affiliation:
                                affiliation = "未找到机构信息"
                        
                        # 尝试获取个人主页链接（如果之前没有找到）
                        if name and not profile_url:
                            link_selectors = [
                                "a.author_main",
                                "a.author_name",
                                "a[href*='author']",
                                "a[title*='主页']"
                            ]
                            
                            for link_sel in link_selectors:
                                try:
                                    link_el = item.locator(link_sel).first
                                    if link_el and link_el.is_visible(timeout=5000):
                                        profile_url = link_el.get_attribute("href", timeout=5000)
                                        print(f"找到个人主页链接: {profile_url} (使用选择器:{link_sel})")
                                        break
                                except Exception as e:
                                    print(f"使用选择器 {link_sel} 获取链接失败: {str(e)}")
                        
                        # 如果成功提取到作者姓名，添加到结果中
                        if name:
                            scholar_info = {
                                "rank": idx,
                                "name": name.strip() if name else "未知学者",
                                "affiliation": affiliation.strip() if affiliation else "未知机构",
                                "profile_url": profile_url if profile_url else "#"
                            }
                            
                            scholar_results.append(scholar_info)
                            processed_count += 1
                            
                            print(f"{idx}. {scholar_info['name']} - {scholar_info['affiliation']}")
                            print(f"   主页链接: {scholar_info['profile_url']}")
                        else:
                            print(f"跳过第{idx}条结果：无法提取作者名")
                            
                    except Exception as e:
                        print(f"处理第{idx}条结果时出错: {str(e)}")
                        continue
                
                print(f"\n成功处理 {processed_count}/{len(items[:max_results])} 条搜索结果")
                
            # 4. 访问学者主页(如果找到结果)
            if scholar_results:
                # 如果有多个学者，提示用户选择
                selected_scholar = scholar_results[0]  # 默认选择第一个
                
                if len(scholar_results) > 1:
                    print("\n找到多位同名学者，请选择要查看的学者：")
                    for i, scholar in enumerate(scholar_results, 1):
                        print(f"{i}. {scholar['name']} - {scholar['affiliation']}")
                    
                    try:
                        choice = input("\n请输入序号(默认1): ").strip()
                        if choice and choice.isdigit() and 1 <= int(choice) <= len(scholar_results):
                            selected_scholar = scholar_results[int(choice) - 1]
                        else:
                            print("使用默认选择: 1")
                    except Exception as e:
                        print(f"选择错误: {str(e)}, 使用默认选择: 1")
                
                print(f"\n正在访问学者主页: {selected_scholar['name']}...")
                
                # 检查是否有有效的主页URL
                if selected_scholar['profile_url'] and selected_scholar['profile_url'] != "#":
                    try:
                        # 清理URL，移除换行符和可能导致CSS选择器语法错误的字符
                        profile_url = selected_scholar['profile_url'].strip().replace('\n', '').replace('\r', '')
                        print(f"处理后的URL: {profile_url}")
                        
                        # 修复：确保URL有正确的协议前缀
                        if profile_url.startswith("//"):
                            profile_url = "https:" + profile_url
                        elif not profile_url.startswith(("http://", "https://")):
                            profile_url = "https://" + profile_url
                        
                        # 使用Playwright的原生API打开新标签页，替代JavaScript方式
                        print("使用Playwright API打开新标签页...")
                        
                        # 直接创建新页面并导航
                        new_page = context.new_page()
                        print(f"正在导航至: {profile_url}")
                        new_page.goto(profile_url, timeout=page_timeout)
                        
                        # 使用更可靠的页面加载检测方法
                        print(f"等待页面加载: {new_page.url}")
                        
                        # 首先等待基本DOM加载完成 - 这个条件最容易满足
                        try:
                            new_page.wait_for_load_state("domcontentloaded", timeout=15000)
                            print("✓ DOM内容已加载")
                        except Exception as e:
                            print(f"DOM加载等待超时，继续执行: {str(e)}")
                        
                        # 然后等待页面基本渲染完成
                        try:
                            new_page.wait_for_load_state("load", timeout=15000)
                            print("✓ 页面基本加载完成")
                        except Exception as e:
                            print(f"页面加载等待超时，继续执行: {str(e)}")
                        
                        # 最后尝试等待网络静默，但设置较短的超时时间，避免无限等待
                        try:
                            new_page.wait_for_load_state("networkidle", timeout=10000)
                            print("✓ 网络请求已静默")
                        except Exception as e:
                            print(f"网络静默等待超时，这是正常的，将继续处理: {str(e)}")
                        
                        # 确保页面至少有一些基本内容
                        content_check_script = """
                            () => {
                                return {
                                    hasBody: !!document.body,
                                    bodySize: document.body ? document.body.innerHTML.length : 0,
                                    title: document.title
                                }
                            }
                        """
                        try:
                            page_check = new_page.evaluate(content_check_script)
                            print(f"页面内容检查: 标题='{page_check['title']}', 内容大小={page_check['bodySize']}字节")
                            if page_check['bodySize'] < 100:
                                print("警告: 页面内容非常少，可能加载不完整")
                            else:
                                print("✓ 页面内容看起来已经加载")
                        except Exception as e:
                            print(f"页面内容检查失败: {str(e)}")
                        
                        # 稍微等待一下确保渲染完成
                        new_page.wait_for_timeout(2000)
                        
                        # 保存新页面截图和HTML以便调试
                        # new_page.screenshot(path="screenshots/scholar_page_debug.png", full_page=True)
                        with open("data/scholar_page.html", "w", encoding="utf-8") as f:
                            f.write(new_page.content())
                        print("已保存学者页面HTML和截图用于调试")
                        
                        # 获取学者详细页信息时使用更灵活的选择器和错误处理
                        scholar_info_selectors = {
                            "name": [".p_name", "#author_intro_wr .p_name", "//div[@class='p_name']"],
                            "affiliation": [".p_affiliate", "#author_intro_wr .p_affiliate", "//div[@class='p_affiliate']"],
                            "domain": [".person_domain", ".person_text a", "//span[@class='person_domain']/a"],
                            "citations": [".p_ach_wr li:nth-child(1) .p_ach_num", "//ul[@class='p_ach_wr']/li[1]/p[@class='p_ach_num']"],
                            "publications": [".p_ach_wr li:nth-child(2) .p_ach_num", "//ul[@class='p_ach_wr']/li[2]/p[@class='p_ach_num']"],
                            "h_index": [".p_ach_wr li:nth-child(3) .p_ach_num", "//ul[@class='p_ach_wr']/li[3]/p[@class='p_ach_num']"],
                            "g_index": [".p_ach_wr li:nth-child(4) .p_ach_num", "//ul[@class='p_ach_wr']/li[4]/p[@class='p_ach_num']"],
                            "scholar_id": [".p_scholarID_id", "//span[@class='p_scholarID_id']"]
                        }
                        
                        scholar_details = {}
                        
                        # 遍历每个信息类型和其对应的选择器
                        for info_type, selector_list in scholar_info_selectors.items():
                            for selector in selector_list:
                                try:
                                    if selector.startswith("//"):  # XPath
                                        element = new_page.locator(f"xpath={selector}").first
                                    else:  # CSS选择器
                                        element = new_page.locator(selector).first
                                    
                                    if element and element.is_visible(timeout=2000):
                                        content = element.text_content(timeout=2000).strip()
                                        if content:  # 只有当获取到非空内容时才保存
                                            scholar_details[info_type] = content
                                            print(f"找到学者{info_type}: {content}")
                                            break
                                except Exception as e:
                                    print(f"使用选择器 {selector} 获取{info_type}失败: {str(e)}")
                                    continue
                            
                            # 如果未找到，设置默认值
                            if info_type not in scholar_details:
                                scholar_details[info_type] = f"未找到{info_type}信息"
                        
                        print(f"\n=== 学者详细信息 ===")
                        print(f"姓名: {scholar_details.get('name', '未找到')}")
                        print(f"职称: {scholar_details.get('title', '未找到')}")
                        print(f"机构: {scholar_details.get('affiliation', '未找到')}")
                        
                        # 保存截图
                        # new_page.screenshot(path="screenshots/4_scholar_profile.png", full_page=True)
                        
                        # 将学者信息保存为JSON
                        import json
                        scholar_data = {
                            "basic_info": {
                                "name": scholar_details.get('name', selected_scholar['name']),
                                "title": scholar_details.get('title', '未知'),
                                "affiliation": scholar_details.get('affiliation', selected_scholar['affiliation']),
                                "profile_url": new_page.url,
                                "domain": scholar_details.get('domain', '未知'),
                                "scholar_id": scholar_details.get('scholar_id', '未知')
                            },
                            "academic_info": {
                                "citations": int(scholar_details.get('citations', '0')),
                                "publications": int(scholar_details.get('publications', '0')),
                                "h_index": int(scholar_details.get('h_index', '0')),
                                "g_index": int(scholar_details.get('g_index', '0'))
                            }
                        }
                        
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        filename = f"data/{scholar_data['basic_info']['name']}_{timestamp}.json"
                        with open(filename, "w", encoding="utf-8") as f:
                            json.dump(scholar_data, f, ensure_ascii=False, indent=2)
                        print(f"\n学者信息已保存到: {filename}")
                        
                        # 关闭学者页面
                        new_page.close()
                    except Exception as e:
                        print(f"访问学者主页时出错: {str(e)}")
                        print(f"有问题的URL: {selected_scholar.get('profile_url', '无URL')}")
                        # 尝试保存当前页面以便调试
                        try:
                            page.screenshot(path="screenshots/error_before_profile.png", full_page=True)
                            with open("data/error_page.html", "w", encoding="utf-8") as f:
                                f.write(page.content())
                            print("已保存出错页面截图和HTML")
                        except:
                            pass
                else:
                    print(f"无法访问学者主页，未找到有效的主页链接")
            else:
                print("\n未找到有效的学者信息，跳过访问学者主页")
            
            return scholar_results
            
        except Exception as e:
            print(f"主流程出错: {str(e)}")
            page.screenshot(path="screenshots/error.png", full_page=True)
            raise
        finally:
            # 关闭浏览器
            time.sleep(2)  # 演示观察用
            browser.close()

if __name__ == "__main__":
    scholar_name = input("请输入要搜索的学者姓名（默认: 李彦宏）: ") or "李彦宏"
    try:
        run_baidu_scholar_search(scholar_name=scholar_name, max_retries=3, page_timeout=45000)
    except Exception as e:
        print(f"程序执行失败: {str(e)}")
        print("请检查网络连接或百度学术网站是否可访问")