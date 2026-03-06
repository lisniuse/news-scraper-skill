#!/usr/bin/env python3
"""
新闻抓取工具 - 使用 Playwright 抓取各类新闻资讯
"""

import asyncio
import json
import argparse
import re
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import Stealth, ALL_EVASIONS_DISABLED_KWARGS
import aiohttp


class NewsScraper:
    def __init__(self):
        self.results = {}
        
    async def create_stealth_browser(self, p):
        """创建隐藏爬虫特征的浏览器"""
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        return browser
    
    async def create_stealth_page(self, browser):
        """创建隐藏爬虫特征的页面"""
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            permissions=['geolocation'],
            geolocation={'latitude': 39.9042, 'longitude': 116.4074},
            color_scheme='light',
            java_script_enabled=True,
            bypass_csp=True,
            ignore_https_errors=True
        )
        
        page = await context.new_page()
        
        # 注入脚本隐藏 webdriver 特征
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
            window.chrome = {
                runtime: {}
            };
            Object.defineProperty(navigator, 'chrome', {
                get: () => window.chrome
            });
        """)
        
        # 应用 stealth 模式
        stealth_config = Stealth(
            navigator_languages_override=("zh-CN", "zh", "en"),
            navigator_platform_override="MacIntel",
            navigator_user_agent_override='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        await page.add_init_script(script=stealth_config.script_payload)
        
        return page
        
    async def fetch_weather(self, city="北京"):
        """获取本地天气信息 - 使用免费天气 API"""
        print(f"正在获取 {city} 天气信息...")
        
        # 使用 Open-Meteo 免费天气 API
        try:
            # 获取城市坐标（简化版，使用北京坐标作为示例）
            lat, lon = 39.9042, 116.4074
            
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=Asia/Shanghai"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()
                    
                    weather_code_map = {
                        0: "晴朗", 1: "主要晴朗", 2: "部分多云", 3: "多云",
                        45: "雾", 48: "雾凇",
                        51: "毛毛雨", 53: "中度毛毛雨", 55: "大毛毛雨",
                        61: "小雨", 63: "中雨", 65: "大雨",
                        71: "小雪", 73: "中雪", 75: "大雪",
                        95: "雷雨", 96: "雷雨伴冰雹", 99: "强雷雨伴冰雹"
                    }
                    
                    current = data.get('current', {})
                    daily = data.get('daily', {})
                    
                    weather_info = {
                        "城市": city,
                        "日期": datetime.now().strftime("%Y-%m-%d"),
                        "当前温度": f"{current.get('temperature_2m', 'N/A')}°C",
                        "体感温度": f"{current.get('apparent_temperature', 'N/A')}°C",
                        "湿度": f"{current.get('relative_humidity_2m', 'N/A')}%",
                        "风速": f"{current.get('wind_speed_10m', 'N/A')} km/h",
                        "天气状况": weather_code_map.get(current.get('weather_code', 0), "未知"),
                        "今日最高温": f"{daily.get('temperature_2m_max', ['N/A'])[0]}°C" if daily.get('temperature_2m_max') else "N/A",
                        "今日最低温": f"{daily.get('temperature_2m_min', ['N/A'])[0]}°C" if daily.get('temperature_2m_min') else "N/A",
                        "降水量": f"{daily.get('precipitation_sum', ['N/A'])[0]}mm" if daily.get('precipitation_sum') else "N/A"
                    }
                    
                    self.results["天气"] = weather_info
                    print(f"✓ 天气信息获取成功")
                    return weather_info
                    
        except Exception as e:
            print(f"✗ 天气信息获取失败: {e}")
            self.results["天气"] = {"错误": str(e)}
            return None
    
    async def fetch_gold_price(self):
        """抓取贵金属价格 - 从 http://www.huangjinjiage.cn"""
        print("正在获取贵金属价格...")
        
        async with async_playwright() as p:
            browser = await self.create_stealth_browser(p)
            page = await self.create_stealth_page(browser)
            
            try:
                await page.goto("http://www.huangjinjiage.cn", wait_until="networkidle")
                
                # 等待页面加载
                await page.wait_for_timeout(2000)
                
                # 提取国际金价数据
                gold_data = await page.evaluate("""
                    () => {
                        const data = {};
                        // 获取国际金价
                        const intlRows = document.querySelectorAll('table');
                        intlRows.forEach(table => {
                            const rows = table.querySelectorAll('tr');
                            rows.forEach(row => {
                                const cells = row.querySelectorAll('td');
                                if (cells.length >= 7) {
                                    const name = cells[0]?.textContent?.trim();
                                    if (name && ['国际金价', '国际铂金', '国际银价', '国际钯金'].includes(name)) {
                                        data[name] = {
                                            '最新价': cells[1]?.textContent?.trim(),
                                            '涨跌': cells[2]?.textContent?.trim(),
                                            '幅度': cells[3]?.textContent?.trim(),
                                            '最高价': cells[4]?.textContent?.trim(),
                                            '最低价': cells[5]?.textContent?.trim(),
                                            '报价时间': cells[6]?.textContent?.trim()
                                        };
                                    }
                                }
                            });
                        });
                        return data;
                    }
                """)
                
                # 提取国内金价数据
                domestic_data = await page.evaluate("""
                    () => {
                        const data = {};
                        const tables = document.querySelectorAll('table');
                        tables.forEach(table => {
                            const rows = table.querySelectorAll('tr');
                            rows.forEach(row => {
                                const cells = row.querySelectorAll('td');
                                if (cells.length >= 7) {
                                    const name = cells[0]?.textContent?.trim();
                                    if (name && ['国内金价', '国内银价', '投资金条', '黄金回收价格'].includes(name)) {
                                        data[name] = {
                                            '最新价': cells[1]?.textContent?.trim(),
                                            '涨跌': cells[2]?.textContent?.trim(),
                                            '幅度': cells[3]?.textContent?.trim(),
                                            '最高价': cells[4]?.textContent?.trim(),
                                            '最低价': cells[5]?.textContent?.trim(),
                                            '报价时间': cells[6]?.textContent?.trim()
                                        };
                                    }
                                }
                            });
                        });
                        return data;
                    }
                """)
                
                # 提取品牌金店价格
                brand_prices = await page.evaluate("""
                    () => {
                        const brands = [];
                        const tables = document.querySelectorAll('table');
                        tables.forEach(table => {
                            const rows = table.querySelectorAll('tr');
                            rows.forEach(row => {
                                const cells = row.querySelectorAll('td');
                                if (cells.length >= 7) {
                                    const brand = cells[0]?.textContent?.trim();
                                    const goldPrice = cells[1]?.textContent?.trim();
                                    if (brand && goldPrice && brand.includes('周') || brand.includes('中国黄金') || brand.includes('老庙') || brand.includes('老凤祥')) {
                                        brands.push({
                                            '品牌': brand,
                                            '黄金价格': goldPrice,
                                            '铂金价格': cells[2]?.textContent?.trim(),
                                            '金条价格': cells[3]?.textContent?.trim(),
                                            '报价时间': cells[6]?.textContent?.trim()
                                        });
                                    }
                                }
                            });
                        });
                        return brands.slice(0, 10);  // 只取前10个
                    }
                """)
                
                result = {
                    "国际贵金属": gold_data,
                    "国内贵金属": domestic_data,
                    "品牌金店价格": brand_prices,
                    "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                self.results["贵金属"] = result
                print(f"✓ 贵金属价格获取成功")
                return result
                
            except Exception as e:
                print(f"✗ 贵金属价格获取失败: {e}")
                self.results["贵金属"] = {"错误": str(e)}
                return None
            finally:
                await browser.close()
    
    async def fetch_exchange_rate(self):
        """抓取外汇牌价 - 从 https://www.boc.cn/sourcedb/whpj/"""
        print("正在获取外汇牌价...")
        
        async with async_playwright() as p:
            browser = await self.create_stealth_browser(p)
            page = await self.create_stealth_page(browser)
            
            try:
                await page.goto("https://www.boc.cn/sourcedb/whpj/", wait_until="networkidle")
                
                # 等待表格加载
                await page.wait_for_selector("table", timeout=10000)
                
                # 提取主要货币汇率
                rates = await page.evaluate("""
                    () => {
                        const data = [];
                        const rows = document.querySelectorAll('table tr');
                        const targetCurrencies = ['美元', '港币', '欧元', '日元', '英镑', '澳大利亚元', '加拿大元', '新加坡元'];
                        
                        rows.forEach(row => {
                            const cells = row.querySelectorAll('td');
                            if (cells.length >= 8) {
                                const currency = cells[0]?.textContent?.trim();
                                if (targetCurrencies.includes(currency)) {
                                    data.push({
                                        '货币名称': currency,
                                        '现汇买入价': cells[1]?.textContent?.trim(),
                                        '现钞买入价': cells[2]?.textContent?.trim(),
                                        '现汇卖出价': cells[3]?.textContent?.trim(),
                                        '现钞卖出价': cells[4]?.textContent?.trim(),
                                        '中行折算价': cells[5]?.textContent?.trim(),
                                        '发布日期': cells[6]?.textContent?.trim(),
                                        '发布时间': cells[7]?.textContent?.trim()
                                    });
                                }
                            }
                        });
                        return data;
                    }
                """)
                
                result = {
                    "外汇牌价": rates,
                    "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                self.results["外汇牌价"] = result
                print(f"✓ 外汇牌价获取成功")
                return result
                
            except Exception as e:
                print(f"✗ 外汇牌价获取失败: {e}")
                self.results["外汇牌价"] = {"错误": str(e)}
                return None
            finally:
                await browser.close()
    
    async def fetch_cctv_news(self):
        """抓取央视新闻 - 从 https://news.cctv.com"""
        print("正在获取央视新闻...")
        
        async with async_playwright() as p:
            browser = await self.create_stealth_browser(p)
            page = await self.create_stealth_page(browser)
            
            try:
                await page.goto("https://news.cctv.com", wait_until="networkidle")
                
                # 等待页面加载
                await page.wait_for_timeout(3000)
                
                # 提取新闻标题和链接
                news = await page.evaluate("""
                    () => {
                        const newsList = [];
                        // 获取主要新闻
                        const links = document.querySelectorAll('a');
                        links.forEach(link => {
                            const title = link.textContent?.trim();
                            const href = link.href;
                            if (title && title.length > 10 && title.length < 100 && href && href.includes('cctv.com')) {
                                // 去重
                                if (!newsList.find(n => n.title === title)) {
                                    newsList.push({
                                        title: title,
                                        url: href
                                    });
                                }
                            }
                        });
                        return newsList.slice(0, 20);  // 取前20条
                    }
                """)
                
                result = {
                    "新闻": news,
                    "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                self.results["央视新闻"] = result
                print(f"✓ 央视新闻获取成功，共 {len(news)} 条")
                return result
                
            except Exception as e:
                print(f"✗ 央视新闻获取失败: {e}")
                self.results["央视新闻"] = {"错误": str(e)}
                return None
            finally:
                await browser.close()
    
    async def fetch_shipping_news(self):
        """抓取国际物流航运新闻 - 从 http://info.shippingchina.com"""
        print("正在获取国际物流航运新闻...")
        
        async with async_playwright() as p:
            browser = await self.create_stealth_browser(p)
            page = await self.create_stealth_page(browser)
            
            try:
                await page.goto("http://info.shippingchina.com/", wait_until="networkidle")
                
                # 等待页面加载 - 增加等待时间确保动态内容加载
                await page.wait_for_timeout(3000)
                
                # 等待 hotNewsC 元素出现，最多等待15秒
                hotNewsFound = False
                for attempt in range(3):
                    try:
                        await page.wait_for_selector('.hotNewsC', timeout=5000)
                        hotNewsFound = True
                        print(f"  ✓ hotNewsC 元素已找到 (尝试 {attempt + 1})")
                        break
                    except:
                        if attempt < 2:
                            print(f"  等待 hotNewsC 元素... (尝试 {attempt + 1}/3)")
                            await page.wait_for_timeout(2000)
                        else:
                            print("  警告: hotNewsC 元素未找到，使用备用选择器")
                
                # 提取新闻 - 从 hotNewsC 结构中获取
                news = await page.evaluate("""
                    () => {
                        const newsList = [];
                        
                        // 获取 hotNewsC 容器中的新闻
                        const hotNewsContainer = document.querySelector('.hotNewsC');
                        if (hotNewsContainer) {
                            console.log('找到 hotNewsC 容器');
                            
                            // 获取主标题新闻
                            const mainTitle = hotNewsContainer.querySelector('h2 a');
                            if (mainTitle) {
                                const title = mainTitle.getAttribute('title') || mainTitle.textContent?.trim();
                                const href = mainTitle.href;
                                console.log('主标题:', title);
                                if (title && title.length > 5) {
                                    newsList.push({
                                        title: title,
                                        url: href,
                                        category: '航运物流-头条'
                                    });
                                }
                            }
                            
                            // 获取描述段落
                            const descP = hotNewsContainer.querySelector('p');
                            if (descP) {
                                const desc = descP.textContent?.trim();
                                if (desc && desc.length > 10) {
                                    newsList.push({
                                        title: desc.substring(0, 60) + (desc.length > 60 ? '...' : ''),
                                        url: '',
                                        category: '航运物流-摘要'
                                    });
                                }
                            }
                            
                            // 获取列表中的新闻
                            const listItems = hotNewsContainer.querySelectorAll('ul li a');
                            console.log('列表项数量:', listItems.length);
                            listItems.forEach((link, index) => {
                                const title = link.textContent?.trim();
                                const href = link.href;
                                console.log(`列表项 ${index}:`, title);
                                if (title && title.length > 5 && title.length < 100) {
                                    if (!newsList.find(n => n.title === title)) {
                                        newsList.push({
                                            title: title,
                                            url: href,
                                            category: '航运物流'
                                        });
                                    }
                                }
                            });
                        } else {
                            console.log('未找到 hotNewsC 容器');
                        }
                        
                        // 如果 hotNewsC 没有内容，尝试其他选择器
                        if (newsList.length === 0) {
                            console.log('使用备用选择器');
                            const allLinks = document.querySelectorAll('a[href*="/detail/id/"]');
                            allLinks.forEach(link => {
                                const title = link.textContent?.trim();
                                const href = link.href;
                                if (title && title.length > 5 && title.length < 100) {
                                    if (!newsList.find(n => n.title === title)) {
                                        newsList.push({
                                            title: title,
                                            url: href,
                                            category: '航运物流'
                                        });
                                    }
                                }
                            });
                        }
                        
                        return newsList.slice(0, 7);  // 取前7条（包含主标题+摘要+列表）
                    }
                """)
                
                result = {
                    "航运新闻": news,
                    "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                self.results["国际物流航运"] = result
                print(f"✓ 国际物流航运新闻获取成功，共 {len(news)} 条")
                return result
                
            except Exception as e:
                print(f"✗ 国际物流航运新闻获取失败: {e}")
                self.results["国际物流航运"] = {"错误": str(e)}
                return None
            finally:
                await browser.close()
    
    async def fetch_bloomberg_news(self):
        """抓取 Bloomberg 经济新闻 - 从 https://www.bloomberg.com
        使用 Chrome DevTools Protocol (CDP) 连接到本地 Chrome 浏览器
        """
        print("正在获取 Bloomberg 经济新闻...")
        print("  尝试使用 Chrome DevTools Protocol (CDP) 连接到本地 Chrome")
        
        try:
            async with async_playwright() as p:
                # 尝试连接到本地 Chrome 浏览器的 CDP 端口
                # 需要先启动 Chrome: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
                try:
                    browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                    print("  ✓ 成功连接到本地 Chrome 浏览器")
                except Exception as e:
                    print(f"  ✗ 无法连接到本地 Chrome: {e}")
                    print("  提示: 请先运行以下命令启动 Chrome:")
                    print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
                    return await self._load_manual_bloomberg_data()
                
                # 创建新页面或复用现有页面
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                page = await context.new_page()
                
                try:
                    print("  正在访问 Bloomberg...")
                    await page.goto("https://www.bloomberg.com/asia", wait_until="networkidle", timeout=60000)
                    
                    # 等待页面加载
                    await page.wait_for_timeout(3000)
                    
                    # 检查是否是验证页面
                    page_title = await page.title()
                    page_content = await page.content()
                    
                    is_captcha_page = (
                        "captcha" in page_content.lower() or
                        "perimeterx" in page_content.lower() or
                        "verify" in page_title.lower() or
                        "unusual activity" in page_content.lower() or
                        "are you a robot" in page_content.lower() or
                        "px-captcha" in page_content.lower()
                    )
                    
                    if is_captcha_page:
                        print("\n" + "=" * 60)
                        print("⚠️  检测到 Bloomberg 验证页面（CAPTCHA）")
                        print("=" * 60)
                        print("请在已打开的 Chrome 浏览器中完成人机验证")
                        print("脚本将自动检测新闻元素...")
                        print("=" * 60 + "\n")
                    
                    # 轮询检测新闻元素（最多等待5分钟）
                    max_wait_time = 300  # 5分钟
                    check_interval = 3   # 每3秒检查一次
                    elapsed_time = 0
                    news = []
                    
                    while elapsed_time < max_wait_time:
                        # 提取新闻
                        news = await page.evaluate("""
                            () => {
                                const newsList = [];
                                const seen = new Set();
                                
                                // 获取所有新闻链接
                                const allLinks = document.querySelectorAll('a');
                                
                                allLinks.forEach(link => {
                                    const href = link.href || '';
                                    const title = link.textContent?.trim() || '';
                                    
                                    if (href.includes('bloomberg.com/news/articles') && title.length > 20 && title.length < 200) {
                                        if (!title.includes('Sign In') && 
                                            !title.includes('Subscribe') &&
                                            !title.includes('Live TV') &&
                                            !title.startsWith('http') &&
                                            !title.includes('AP Photo') &&
                                            !title.includes('Getty Images') &&
                                            !title.includes('Illustration:')) {
                                            
                                            if (!seen.has(title)) {
                                                seen.add(title);
                                                newsList.push({
                                                    title: title,
                                                    url: href
                                                });
                                            }
                                        }
                                    }
                                });
                                
                                return newsList.slice(0, 5);
                            }
                        """)
                        
                        if news and len(news) > 0:
                            print(f"  ✓ 检测到 {len(news)} 条新闻（等待 {elapsed_time} 秒）")
                            break
                        
                        # 检查是否仍在验证页面
                        if elapsed_time > 0 and elapsed_time % 10 == 0:
                            print(f"  仍在等待... 已等待 {elapsed_time} 秒，请完成验证")
                        
                        await page.wait_for_timeout(check_interval * 1000)
                        elapsed_time += check_interval
                    
                    if news and len(news) > 0:
                        result = {
                            "经济新闻": news,
                            "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "抓取方式": "chrome-cdp"
                        }
                        
                        self.results["Bloomberg经济"] = result
                        print(f"✓ Bloomberg 经济新闻获取成功，共 {len(news)} 条")
                        
                        # 保存到手动抓取文件，供后续使用
                        import os
                        bloomberg_file = os.path.join(os.path.dirname(__file__), '..', 'output', 'bloomberg_manual.json')
                        with open(bloomberg_file, 'w', encoding='utf-8') as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)
                        
                        return result
                    else:
                        print(f"  等待 {max_wait_time} 秒后仍未找到新闻，可能页面结构已更改")
                        return await self._load_manual_bloomberg_data()
                    
                except Exception as e:
                    print(f"✗ 页面访问失败: {e}")
                    return await self._load_manual_bloomberg_data()
                finally:
                    await page.close()
                    
        except Exception as e:
            print(f"✗ Bloomberg 经济新闻获取失败: {e}")
            return await self._load_manual_bloomberg_data()
    
    async def _load_manual_bloomberg_data(self):
        """加载手动抓取的 Bloomberg 数据"""
        try:
            import os
            bloomberg_file = os.path.join(os.path.dirname(__file__), '..', 'output', 'bloomberg_manual.json')
            
            if os.path.exists(bloomberg_file):
                with open(bloomberg_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.results["Bloomberg经济"] = data
                    news_count = len(data.get("经济新闻", []))
                    print(f"✓ Bloomberg 经济新闻获取成功，共 {news_count} 条 (来自手动抓取)")
                    return data
        except Exception as e:
            print(f"  手动数据也加载失败: {e}")
        
        self.results["Bloomberg经济"] = {
            "经济新闻": [],
            "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "备注": "自动抓取和手动数据都失败"
        }
        return self.results["Bloomberg经济"]
    
    async def run_all(self, city="北京"):
        """运行所有抓取任务"""
        print("=" * 60)
        print("开始抓取新闻资讯...")
        print("=" * 60)
        
        # 顺序执行所有抓取任务
        await self.fetch_weather(city)
        await self.fetch_gold_price()
        await self.fetch_exchange_rate()
        await self.fetch_cctv_news()
        await self.fetch_shipping_news()
        await self.fetch_bloomberg_news()
        
        print("=" * 60)
        print("抓取完成！")
        print("=" * 60)
        
        return self.results
    
    def save_results(self, filename=None):
        """保存结果到 JSON 文件"""
        import os
        
        # 获取脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取项目根目录（scripts的父目录）
        project_dir = os.path.dirname(script_dir)
        
        if filename is None:
            filename = os.path.join(project_dir, f"output/news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        elif not os.path.isabs(filename):
            # 如果是相对路径，转换为绝对路径
            filename = os.path.join(project_dir, filename)
        
        # 确保 output 目录存在
        output_dir = os.path.dirname(filename)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"\n创建目录: {output_dir}")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存到: {filename}")
        except Exception as e:
            print(f"\n保存结果失败: {e}")
    
    def print_summary(self):
        """打印摘要"""
        print("\n" + "=" * 60)
        print("抓取结果摘要")
        print("=" * 60)
        
        for category, data in self.results.items():
            if "错误" in data:
                print(f"\n❌ {category}: 抓取失败 - {data['错误']}")
            else:
                print(f"\n✅ {category}: 抓取成功")
                if isinstance(data, dict):
                    if "新闻" in data:
                        print(f"   共 {len(data['新闻'])} 条新闻")
                    elif "外汇牌价" in data:
                        print(f"   共 {len(data['外汇牌价'])} 种货币")
                    elif "国际贵金属" in data:
                        print(f"   包含国际/国内贵金属价格")
                    elif "城市" in data:
                        print(f"   {data['城市']} {data['天气状况']} {data['当前温度']}")


async def main():
    parser = argparse.ArgumentParser(description='新闻抓取工具')
    parser.add_argument('-c', '--city', type=str, default='北京',
                        help='城市名称（用于天气查询）')
    parser.add_argument('-o', '--output', type=str, default=None,
                        help='输出文件路径')
    parser.add_argument('--weather-only', action='store_true',
                        help='仅获取天气')
    parser.add_argument('--gold-only', action='store_true',
                        help='仅获取贵金属价格')
    parser.add_argument('--forex-only', action='store_true',
                        help='仅获取外汇牌价')
    parser.add_argument('--news-only', action='store_true',
                        help='仅获取新闻')
    
    args = parser.parse_args()
    
    scraper = NewsScraper()
    
    # 根据参数执行特定任务或全部任务
    if args.weather_only:
        await scraper.fetch_weather(args.city)
    elif args.gold_only:
        await scraper.fetch_gold_price()
    elif args.forex_only:
        await scraper.fetch_exchange_rate()
    elif args.news_only:
        await scraper.fetch_cctv_news()
        await scraper.fetch_shipping_news()
        await scraper.fetch_bloomberg_news()
    else:
        await scraper.run_all(args.city)
    
    # 打印摘要
    scraper.print_summary()
    
    # 保存结果
    scraper.save_results(args.output)


if __name__ == "__main__":
    asyncio.run(main())
