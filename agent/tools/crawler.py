# 导入所需库
import os

import requests  # 用于发起 HTTP 请求获取网页内容
from bs4 import BeautifulSoup  # 用于解析 HTML 页面结构
from urllib.parse import urljoin, urlparse  # 用于处理 URL 拼接与解析
from typing import Dict, List, Set, Any  # 类型提示，提高代码可读性

__all__=["WebCrawler"]
class WebCrawler:
    """WebCrawler 是一个简单的网页爬虫类，用于抓取指定网站的内容并提取文本、链接等信息。

    功能包括：
    - 提取页面标题和正文内容
    - 提取页面中的超链接
    - 控制爬取范围在同一个域名下
    - 限制最大爬取页数防止无限爬取
    """

    def __init__(self, base_url: str, max_pages: int = 0):
        """初始化爬虫实例

        参数:
            base_url (str): 起始网址
            max_pages (int): 最大爬取页数，默认为10
        """
        self.base_url = base_url  # 初始访问地址
        self.max_pages = max_pages  # 最大爬取页面数量
        self.visited: Set[str] = set()  # 已访问的URL集合，避免重复爬取

    def is_valid_url(self, url: str) -> bool:
        """判断给定的 URL 是否属于初始域名，确保只爬取目标站点的内容

        参数:
            url (str): 待检查的 URL

        返回:
            bool: 如果是同域名返回 True，否则返回 False
        """
        base_domain = urlparse(self.base_url).netloc  # 获取初始域名
        url_domain = urlparse(url).netloc  # 获取当前 URL 的域名
        return base_domain == url_domain  # 判断是否为同一域名

    def extract_page_content(self, url: str) -> dict[str, str | None | list[Any]] | None:
        """从指定 URL 抓取页面内容，并提取关键信息

        参数:
            url (str): 要抓取的页面地址

        返回:
            Dict: 包含页面信息的字典，如标题、正文、链接等；失败时返回 None
        """
        try:
            proxy_url = os.getenv("PROXY_URL")
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            } if proxy_url else None

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.google.com/",
                "Connection": "keep-alive"
            }

            response = requests.get(url, headers=headers,proxies=proxies,timeout=10)
            response.raise_for_status()  # 如果响应状态码不是 200，抛出异常

            soup = BeautifulSoup(response.text, "html.parser")  # 解析 HTML 内容

            # 构建包含页面信息的字典
            content = {
                "url": url,  # 当前页面 URL
                "title": soup.title.string if soup.title else "",  # 页面标题
                "text": soup.get_text(separator="\n", strip=True),  # 页面正文内容，用换行分隔并去除空白
                # "links": []  # 存储提取到的链接
            }

            # 遍历页面中的所有 <a> 标签，提取 href 属性
            # for link in soup.find_all("a"):
            #     href = link.get("href")
            #     if href:
            #         absolute_url = urljoin(url, href)  # 将相对路径转为绝对 URL
            #         if self.is_valid_url(absolute_url):  # 只保留同域名下的链接
            #             content["links"].append(absolute_url)

            return content

        except Exception as e:
            print(f"爬取 {url} 时发生错误: {str(e)}")
            return None

    def crawl(self) -> List[Dict]:
        """开始爬取流程，从 base_url 开始，逐步爬取相关页面

        返回:
            List[Dict]: 爬取结果列表，每个元素是一个页面的信息字典
        """
        to_visit = [self.base_url]  # 待爬取的 URL 列表
        results = []  # 存储最终爬取结果

        while to_visit and len(self.visited) <= self.max_pages:  # 当还有链接待爬且未超过最大页数时继续
            url = to_visit.pop(0)  # 从队列中取出第一个 URL

            if url in self.visited:
                continue  # 如果已访问过，跳过该页面

            print(f"正在爬取: {url}")
            content = self.extract_page_content(url)  # 抓取页面内容

            if content:
                self.visited.add(url)  # 将当前 URL 加入已访问集合
                results.append(content)  # 添加到结果列表

                # # 找出新的 URL 并加入待访问队列
                # new_urls = [url for url in content["links"]
                #             if url not in self.visited and url not in to_visit]
                # to_visit.extend(new_urls)

        return results