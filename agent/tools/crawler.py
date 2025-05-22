import os
import random

from newspaper import Source
from newspaper.configuration import Configuration
from newspaper.mthreading import fetch_news
import threading

from dotenv import load_dotenv

load_dotenv()

__all__ = ["NewsCrawler"]


class NewsCrawler:

    def __init__(self, source_urls_=None, config=None):
        # 使用 None 避免可变默认参数问题
        if source_urls_ is None:
            source_urls_ = []
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
            "timeout": 7,
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
        self.sources = [Source(url, config=config) for url in source_urls_]
        self.articles = []

    def build_sources(self):
        # Multithreaded source building
        threads = [threading.Thread(target=source.build) for source in self.sources]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    def crawl_articles(self):
        # Multithreaded article downloading
        self.articles = fetch_news(self.sources, threads=1, timeout=10)

    def extract_information(self):
        content = []
        # Extract information from each article
        for source in self.sources:
            print(f"Source {source.url}")
            for article in source.articles[:1]:
                article.parse()
                # print(f"Title: {article.title}")
                # print(f"Authors: {article.authors}")
                # print(f"url: {article.url}")
                # print(f"Text: {article.text[:2000]}...")  # Printing first 150 characters of text
                # print("-------------------------------")
                content.append({
                    "title": article.title,
                    "authors": article.authors,
                    "text": article.text[:2000],
                    "url": article.url
                })
        return content


if __name__ == "__main__":
    source_urls = ['https://slate.com', 'https://time.com']  # Add your news source URLs here
    crawler = NewsCrawler(source_urls)
    crawler.build_sources()
    # crawler.crawl_articles()
    crawler.extract_information()
