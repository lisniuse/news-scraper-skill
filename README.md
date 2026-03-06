# 新闻抓取工具 (news-scraper)

一个基于 Playwright 的自动化新闻抓取工具，用于获取每日最新资讯，包括天气、贵金属价格、外汇牌价、国内外新闻、国际物流航运新闻和经济新闻。

## 功能特性

- 🌤️ **本地天气** - 使用免费天气 API 获取实时天气信息
- 🥇 **贵金属价格** - 抓取国际国内金价、银价、铂金价格
- 💱 **外汇牌价** - 获取中国银行汇率（默认美元，可指定多种货币）
- 📺 **国内外热点新闻** - 抓取央视新闻（国内10条+国际10条，共20条）
- 🚢 **国际物流航运** - 抓取航运新闻前5条
- 💰 **经济动向** - 抓取 Bloomberg 经济新闻前5条

## 环境要求

- Python 3.8+
- Playwright

## 安装

### 1. 安装 Python 依赖

```bash
cd news-scraper
pip3 install -r scripts/requirements.txt
```

### 2. 安装 Playwright 浏览器

```bash
playwright install chromium
```

## 使用方法

### 基本用法

```bash
# 抓取所有资讯
python3 scripts/news_scraper.py
```

### 指定城市天气

```bash
python3 scripts/news_scraper.py -c 上海
```

### 仅获取特定类型资讯

```bash
# 仅获取天气
python3 scripts/news_scraper.py --weather-only

# 仅获取贵金属价格
python3 scripts/news_scraper.py --gold-only

# 仅获取外汇牌价（默认只获取美元）
python3 scripts/news_scraper.py --forex-only

# 指定多种货币（用逗号分隔）
python3 scripts/news_scraper.py --forex-only --forex-currencies "美元,欧元,日元,英镑"

# 获取所有主要货币
python3 scripts/news_scraper.py --forex-only --forex-currencies "美元,港币,欧元,日元,英镑,澳大利亚元,加拿大元,新加坡元"

# 仅获取新闻（央视新闻+航运+Bloomberg）
python3 scripts/news_scraper.py --news-only
```

### 指定输出文件

```bash
python3 scripts/news_scraper.py -o output/my_news.json
```

## 文件结构

```
news-scraper/
├── README.md              # 项目说明文件
├── SKILL.md               # Skill 定义文件
├── scripts/               # Python 脚本
│   ├── news_scraper.py    # 主抓取程序
│   └── requirements.txt   # 依赖文件
├── assets/                # 资源文件目录
└── output/                # 输出文件目录
    └── news_YYYYMMDD_HHMMSS.json
```

## 输出示例

抓取结果会保存为 JSON 文件，格式如下：

```json
{
  "天气": {
    "城市": "北京",
    "日期": "2026-03-06",
    "当前温度": "15°C",
    "体感温度": "14°C",
    "湿度": "45%",
    "风速": "10 km/h",
    "天气状况": "晴朗",
    "今日最高温": "18°C",
    "今日最低温": "8°C",
    "降水量": "0mm"
  },
  "贵金属": {
    "国际贵金属": {
      "国际金价": {
        "最新价": "5119.42",
        "涨跌": "38.54",
        "幅度": "0.76%",
        "最高价": "5143.64",
        "最低价": "5066.42",
        "报价时间": "14:33:54"
      }
    },
    "国内贵金属": {...},
    "品牌金店价格": [...],
    "抓取时间": "2026-03-06 14:30:00"
  },
  "外汇牌价": {
    "外汇牌价": [
      {
        "货币名称": "美元",
        "现汇买入价": "689.13",
        "现钞买入价": "689.13",
        "现汇卖出价": "692.03",
        "现钞卖出价": "692.03",
        "中行折算价": "690.25",
        "发布日期": "2026/03/06",
        "发布时间": "14:29:17"
      }
    ],
    "抓取时间": "2026-03-06 14:30:00"
  },
  "央视新闻": {
    "新闻": [
      {
        "title": "新闻标题",
        "url": "https://news.cctv.com/..."
      }
    ],
    "抓取时间": "2026-03-06 14:30:00"
  },
  "国际物流航运": {
    "航运新闻": [...],
    "抓取时间": "2026-03-06 14:30:00"
  },
  "Bloomberg经济": {
    "经济新闻": [...],
    "抓取时间": "2026-03-06 14:30:00"
  }
}
```

## 数据来源

| 数据类型 | 来源网站 | 说明 |
|---------|---------|------|
| 天气 | Open-Meteo API | 免费，无需 API Key |
| 贵金属 | http://www.huangjinjiage.cn | 国际国内金价 |
| 外汇牌价 | https://www.boc.cn/sourcedb/whpj/ | 中国银行汇率 |
| 国内新闻 | https://news.cctv.com | 央视新闻 |
| 航运新闻 | http://info.shippingchina.com | 国际物流航运 |
| 经济新闻 | https://www.bloomberg.com | Bloomberg |

## 定时任务设置

建议设置定时任务每日自动运行：

### Linux/macOS (使用 cron)

```bash
# 编辑 crontab
crontab -e

# 每天早上 8 点运行
0 8 * * * cd /path/to/news-scraper && python3 scripts/news_scraper.py
```

### Windows (使用任务计划程序)

1. 打开任务计划程序
2. 创建基本任务
3. 设置触发器为每天
4. 设置操作为启动程序
5. 程序路径填写 `python3` 或 `python`
6. 参数填写 `scripts/news_scraper.py`
7. 起始于填写项目目录路径

## 注意事项

- 首次运行需要下载 Playwright 浏览器，可能需要几分钟时间
- 抓取过程可能需要 30-60 秒，请耐心等待
- 部分网站可能有访问限制，如遇失败可稍后重试
- 建议使用稳定的网络环境运行
- 输出文件会自动保存到 `output/` 目录（已被 .gitignore 忽略，不会提交到 git）

## Bloomberg 抓取说明

Bloomberg 网站有严格的反爬虫机制，脚本使用 Chrome DevTools Protocol (CDP) 连接到本地 Chrome 浏览器进行抓取：

1. **启动 Chrome 并开启远程调试：**
   ```bash
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_dev_profile
   ```

2. **如果 Bloomberg 显示验证码页面：**
   - 脚本会自动检测到验证页面并暂停
   - 请在 Chrome 浏览器中手动完成人机验证
   - 脚本会自动轮询检测新闻元素，验证通过后会继续抓取

3. **如果无法连接 Chrome：**
   - 脚本会自动回退到使用之前保存的缓存数据

## 故障排除

### 1. Playwright 安装失败

```bash
# 重新安装 Playwright
pip3 uninstall playwright
pip3 install playwright
playwright install chromium
```

### 2. 抓取超时

部分网站加载较慢，脚本已设置适当的等待时间。如仍超时，可尝试：
- 检查网络连接
- 稍后重试
- 单独运行特定抓取任务

### 3. 数据为空

- 检查网站是否可访问
- 网站结构可能已更改，需要更新选择器
- 查看错误信息排查问题

## 许可证

本项目采用 MIT 许可证。
