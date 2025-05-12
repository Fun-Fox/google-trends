from io import BytesIO

from duckduckgo_search import DDGS
import imagehash
from PIL import Image
import requests
import os
from serpapi import GoogleSearch
from typing import Dict, List, Optional

from dotenv import load_dotenv
load_dotenv()

__all__=["search_web"]
# 设置代理
proxies = {
    "http": f"{os.getenv('PROXY_URL')}",
    "https": f"{os.getenv('PROXY_URL')}",
}

search_web_call_count = 0
#
# class SearchTool:
#     """Tool for performing web searches using SerpAPI"""
#
#     def __init__(self, api_key: Optional[str] = None):
#         """Initialize search tool with API key
#
#         Args:
#             api_key (str, optional): SerpAPI key. Defaults to env var SERPAPI_API_KEY.
#         """
#         self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
#         if not self.api_key:
#             raise ValueError("SerpAPI key not found. Set SERPAPI_API_KEY env var.")
#
#     def search(self, query: str, num_results: int = 5) -> List[Dict]:
#         """Perform Google search via SerpAPI
#
#         Args:
#             query (str): Search query
#             num_results (int, optional): Number of results to return. Defaults to 5.
#
#         Returns:
#             List[Dict]: Search results with title, snippet, and link
#         """
#         # Configure search parameters
#         params = {
#             "engine": "google",
#             "q": query,
#             "api_key": self.api_key,
#             "num": num_results
#         }
#
#         try:
#             # Execute search
#             search = GoogleSearch(params)
#             results = search.get_dict()
#
#             # Extract organic results
#             if "organic_results" not in results:
#                 return []
#
#             processed_results = []
#             for result in results["organic_results"][:num_results]:
#                 processed_results.append({
#                     "title": result.get("title", ""),
#                     "snippet": result.get("snippet", ""),
#                     "link": result.get("link", "")
#                 })
#
#             return processed_results
#
#         except Exception as e:
#             print(f"Search error: {str(e)}")
#             return []

def search_web(query, hot_word_path, logger,num_results=5):
    try:
        # 使用serper.dev进行网络搜索
        # logger.info(f"## 查询: {query}")

        api_key = os.getenv("SERPAPI_API_KEY", None)
        if api_key:
            global search_web_call_count
            search_web_call_count += 1
            logger.info(f"[SearchWeb] 第 {search_web_call_count} 次调用，查询词: {query}")

            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": query,
                "engine": "google",
                "num": num_results
            }
            response = requests.post(url, headers=headers, json=payload, proxies=proxies)
            if response.status_code == 200:
                results = response.json().get("organic", [])
                results_str = "\n\n".join(
                    [f"标题: {r['title']}\n源链接: {r['link']}\n摘要: {r['snippet']}" for r in results])
                results_dict = [{'title':r['title'],'snippet':r['snippet'],'link':r['link']}  for r in results]
                search_image(query, hot_word_path, logger)
            else:
                logger.error(f"错误: 无法获取搜索结果。状态码: {response.status_code}")
                return "错误: 无法获取搜索结果。",None
        else:
            logger.info(f"使用DuckDuckgo免费搜索进行查询")

            with DDGS(proxy=os.getenv("PROXY_URL"), timeout=20) as ddgs:
                news_results = ddgs.text(query, max_results=num_results)
                search_image(query, hot_word_path, logger)
                # Convert results to a string
                results_str = "\n\n".join(
                    [f"标题: {r['title']}\n源链接: {r['href']}\n摘要: {r['body']}" for r in news_results])
                results_dict = [{'title':r['title'],'snippet':r['body'],'link':r['href']}  for r in news_results]
        # logger.info(f"## 结果: {results_str}")
        return results_str,results_dict
    except Exception as e:
        logger.error(f"搜索网络时发生异常: {e}")
        return "错误: 搜索网络时发生异常。"


def search_image(query, hot_word_path, logger,num_results=8):
    # logger.info(f"## 查询: {query}")

    # 检查 hot_word_path 目录下的图片数量
    existing_images = [f for f in os.listdir(hot_word_path) if f.endswith(('.jpg', '.png'))]
    if len(existing_images) >= num_results:
        logger.info(f"目录 {hot_word_path} 中已有 {len(existing_images)} 张图片，不再下载新图片。")
        return

    # 计算现有图片的哈希值
    existing_hashes = {}
    for img_name in existing_images:
        img_path = os.path.join(hot_word_path, img_name)
        try:
            with Image.open(img_path) as img:
                img_hash = imagehash.average_hash(img)
                existing_hashes[img_hash] = img_name
        except Exception as e:
            logger.error(f"计算图片 {img_path} 哈希值时发生异常: {e}")

    with DDGS(proxy=os.getenv("PROXY_URL"), timeout=20) as ddgs:
        img_results = ddgs.images(query, max_results=5, size="Large")
        # 下载并保存图片
        for i, result in enumerate(img_results):
            image_url = result["image"]
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    # 打开图片并计算哈希值
                    img = Image.open(BytesIO(response.content))
                    new_hash = imagehash.average_hash(img)

                    # 检查是否已有相似图片
                    if any(new_hash - existing_hash < 10 for existing_hash in existing_hashes):
                        logger.info(f"图片 {image_url} 与目录中的图片相似，不保存。")
                        continue

                    # 保存图片
                    save_path = os.path.join(hot_word_path, f"{query}_{i + 1}.jpg")
                    with open(save_path, "wb") as file:
                        file.write(response.content)
                    logger.info(f"图片已保存到: {save_path}")

                    # 更新现有哈希值
                    existing_hashes[new_hash] = os.path.basename(save_path)

                    # 再次检查图片数量，避免超过10个
                    existing_images = [f for f in os.listdir(hot_word_path) if f.endswith(('.jpg', '.png'))]
                    if len(existing_images) >= 10:
                        logger.info(f"目录 {hot_word_path} 中已有 {len(existing_images)} 张图片，不再下载新图片。")
                        break
                else:
                    logger.info(f"无法下载图片 {image_url}，状态码: {response.status_code}")
            except Exception as e:
                logger.info(f"下载图片 {image_url} 时发生异常: {e}")

