import os
import random

import newspaper
from newspaper.configuration import Configuration

from dotenv import load_dotenv

load_dotenv()

__all__ = ["NewsCrawler"]



class NewsCrawler:

    def __init__(self, source_urls_=None):

        # 使用 None 避免可变默认参数问题
        self.source_urls_ = source_urls_
        config = Configuration()
        config.memoize_articles = False  # 禁用缓存，确保获取最新内容
        config.verbose = False  # 关闭详细日志
        proxy_url = os.getenv("PROXY_URL")
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        } if proxy_url else None
        # 多设备User-Agent池
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.4 (KHTML, like Gecko) Version/14.0 Mobile/15A5370a Safari/604.1",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.4 (KHTML, like Gecko) Version/14.0 Mobile/15A5370a Safari/604.1"
        ]

        # 随机选择User-Agent
        selected_ua = random.choice(user_agents)
        config.requests_params = {
            "timeout": 30,
            "proxies": proxies,
            "headers": {
                "User-Agent": selected_ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.google.com/",
                "Connection": "keep-alive",
                "Cache-Control": "no-cache",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1"
            },
        }
        self.config = config

    def extract_information(self):
        article = newspaper.Article(url=self.source_urls_,config=self.config)
        article.download()
        article.parse()
        return {
            "title": article.title,
            "authors": article.authors,
            "text": article.text[:2000],
            "url": article.url
        }


if __name__ == "__main__":
    source_urls = 'https://slate.com'  # Add your news source URLs here
    crawler = NewsCrawler(source_urls)
    # crawler.crawl_articles()
    content = crawler.extract_information()
    print(content)
