import json
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

__all__ = ['parse_cookie_string', 'init_browser', 'close_browser']

def parse_cookie_string(cookie_str: str) -> list:
    """解析从浏览器复制的cookie字符串，返回Playwright所需的cookie列表"""
    cookies = []
    for pair in cookie_str.split(';'):
        if '=' in pair:
            key, value = pair.strip().split('=', 1)
            cookies.append({"name": key, "value": value, "url": "https://trends.google.com/"})
    return cookies

async def init_browser(logging):
    p = await async_playwright().__aenter__()
    headless = os.getenv('HEADLESS', 'True').lower() == 'true'
    browser = await p.chromium.launch(headless=headless,proxy={"server": os.getenv("PROXY_URL", "127.0.0.1:7890")})
    context = await browser.new_context()

    # 解析并设置cookies
    if os.path.exists("setting.json"):
        with open("setting.json", "r") as f:
            settings = json.load(f)
        cookie_str = settings.get("COOKIE_STRING")
    else:
        cookie_str = os.getenv('COOKIE_STRING')

    if cookie_str:
        cookies = parse_cookie_string(cookie_str)
        await context.add_cookies(cookies)
        logging.info('Cookies 设置成功')
    else:
        logging.warning('未找到环境变量中的 COOKIE_STRING')

    # 打开页面
    page = await context.new_page()
    return p, browser, context, page

async def close_browser(p, browser, logging):
    await browser.close()
    await p.stop()
    logging.info('浏览器和Playwright资源已关闭')