import os
import requests
from dotenv import load_dotenv
from duckduckgo_search import DDGS

load_dotenv()

# 设置代理
proxies = {
    "http": f"{os.getenv('PROXY_URL')}",
    "https": f"{os.getenv('PROXY_URL')}",
}


def call_llm(prompt,logger):
    try:
        # 使用本地ollama模型gemma3
        url = f"{os.getenv('LLM_URL')}"
        payload = {
            "model": f"{os.getenv('MODEL_NAME')}",
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(url, json=payload, proxies=proxies)
        if response.status_code == 200:
            return response.json().get("response", ""), True
        else:
            logger.error(f"错误: 无法从模型获取响应。状态码: {response.status_code}")
            return "错误: 无法从模型获取响应。", False
    except Exception as e:
        logger.error(f"调用LLM时发生异常: {e}")
        return "错误: 调用LLM时发生异常。", False


def search_web(query, hot_word_path,logger):
    try:
        # 使用serper.dev进行网络搜索
        logger.info(f"## 查询: {query}")

        api_key = os.getenv("SERPER_API_KEY", None)
        if api_key:

            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": query
            }
            response = requests.post(url, headers=headers, json=payload, proxies=proxies)
            if response.status_code == 200:
                results = response.json().get("organic", [])
                results_str = "\n\n".join(
                    [f"标题: {r['title']}\nURL: {r['link']}\n摘要: {r['snippet']}" for r in results])
            else:
                logger.error(f"错误: 无法获取搜索结果。状态码: {response.status_code}")
                return "错误: 无法获取搜索结果。"
        else:
            with DDGS(proxy=os.getenv("PROXY_URL"), timeout=20) as ddgs:
                news_results = ddgs.text(query, max_results=5)
                search_image(query, hot_word_path,logger)
                # Convert results to a string
                results_str = "\n\n".join(
                    [f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}" for r in news_results])

        logger.info(f"## 结果: {results_str}")
        return results_str
    except Exception as e:
        logger.error(f"搜索网络时发生异常: {e}")
        return "错误: 搜索网络时发生异常。"


def search_image(query, hot_word_path,logger):
    logger.info(f"## 查询: {query}")
    with DDGS(proxy=os.getenv("PROXY_URL"), timeout=20) as ddgs:
        img_results = ddgs.images(query, max_results=5, size="medium")
        # 下载并保存图片
        for i, result in enumerate(img_results):
            image_url = result["image"]
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    # 保存图片
                    # save_dir = "image"
                    # os.makedirs(save_dir, exist_ok=True)
                    save_path = os.path.join(hot_word_path, f"{query}_{i + 1}.jpg")
                    with open(save_path, "wb") as file:
                        file.write(response.content)
                    print(f"图片已保存到: {save_path}")
                else:
                    print(f"无法下载图片 {image_url}，状态码: {response.status_code}")
            except Exception as e:
                print(f"下载图片 {image_url} 时发生异常: {e}")
    # return save_dir


if __name__ == "__main__":
    # logger.info("## 测试 call_llm")
    # prompt = "用简短的语言描述，生命的意义是什么？"
    # logger.info(f"## 提示: {prompt}")
    # response = call_llm(prompt)
    # logger.info(f"## 响应: {response}")

    print("## 测试 search_web")
    query = "谁获得了2024年诺贝尔物理学奖？"
    print(f"## 查询: {query}")
    results = search_web(query)
    print(f"## 结果: {results}")
