import os

import imagehash
import requests
from dotenv import load_dotenv
from duckduckgo_search import DDGS

load_dotenv()

# 设置代理
proxies = {
    "http": f"{os.getenv('PROXY_URL')}",
    "https": f"{os.getenv('PROXY_URL')}",
}


def call_llm(prompt, logger):
    try:
        logger.info(f"## 提示: {prompt}")
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


def search_web(query, hot_word_path, logger):
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
                news_results = ddgs.text(query, max_results=3)
                search_image(query, hot_word_path, logger)
                # Convert results to a string
                results_str = "\n\n".join(
                    [f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}" for r in news_results])

        logger.info(f"## 结果: {results_str}")
        return results_str
    except Exception as e:
        logger.error(f"搜索网络时发生异常: {e}")
        return "错误: 搜索网络时发生异常。"


def search_image(query, hot_word_path, logger):
    logger.info(f"## 查询: {query}")

    # 检查 hot_word_path 目录下的图片数量
    existing_images = [f for f in os.listdir(hot_word_path) if f.endswith(('.jpg', '.png'))]
    if len(existing_images) >= 8:
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
        img_results = ddgs.images(query, max_results=3, size="Large")
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
                    print(f"图片已保存到: {save_path}")

                    # 更新现有哈希值
                    existing_hashes[new_hash] = os.path.basename(save_path)

                    # 再次检查图片数量，避免超过10个
                    existing_images = [f for f in os.listdir(hot_word_path) if f.endswith(('.jpg', '.png'))]
                    if len(existing_images) >= 10:
                        logger.info(f"目录 {hot_word_path} 中已有 {len(existing_images)} 张图片，不再下载新图片。")
                        break
                else:
                    print(f"无法下载图片 {image_url}，状态码: {response.status_code}")
            except Exception as e:
                print(f"下载图片 {image_url} 时发生异常: {e}")


import os
import json
import requests
from PIL import Image
from io import BytesIO
from base64 import b64encode

api_key = "sk-xprtiszdkkdaadtwsilquhcxyjaguhjfrtfncpzlgckhwaje"
api_url = "https://api.siliconflow.cn/v1/chat/completions"
MAX_RETRIES = 2


def evaluate_image_relevance(prompt, image_path, logger):
    """评估图片与叙事的相关性，并对图片进行评分。

    Args:
        image_path: 图片文件路径。
        logger
    Returns:
        包含评估结果的字典。
    """
    for attempt in range(MAX_RETRIES):
        try:
            # 将图片转换为Base64编码
            image_base64 = convert_image_to_base64(image_path)
            # 构建请求负载
            payload = _build_evaluation_payload(prompt, image_base64)
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            response = requests.post(api_url, json=payload, headers=headers)
            if response.status_code == 200:
                try:
                    # 解析 JSON 数据
                    json_data = response.json()
                    choices = json_data.get("choices", [])

                    if choices:  # 确保 choices 列表非空
                        first_choice = choices[0]  # 获取第一个选择
                        message = first_choice.get("message", {})
                        content = message.get("content", "无内容")  # 获取 content 字段，若不存在则返回默认值
                        reasoning_content = message.get("reasoning_content", "无推理内容")  # 获取 reasoning_content 字段

                        logger.info(f"API 响应: Content={content}\n, Reasoning Content={reasoning_content}")
                        return content  # 返回 content 字段
                    else:
                        logger.warning("API 响应中没有 choices 数据")
                        return "无内容"
                except KeyError as e:
                    logger.error(f"JSON 解析错误: {e}")
                    return "错误: JSON 解析失败"
            logger.warning(f"第 {attempt + 1} 次尝试失败，状态码: {response.status_code}")
        except Exception as e:
            logger.warning(f"第 {attempt + 1} 次尝试失败: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                logger.error("所有尝试均失败")
                raise Exception(f"评估图片相关性失败，尝试 {MAX_RETRIES} 次后仍未成功: {str(e)}")
    raise Exception("evaluate_image_relevance 方法中发生意外错误")


def convert_image_to_base64(image_path, quality=80) -> str:
    """将图片转换为Base64编码，支持多种格式，并记录日志。"""
    with Image.open(image_path) as img:
        format = img.format or "JPEG"
        byte_stream = BytesIO()

        if format.upper() == "PNG" and img.mode == "RGBA":
            img.save(byte_stream, format=format)
        else:
            img = img.convert("RGB")
            img.save(byte_stream, format=format, quality=quality)

        image_bytes = byte_stream.getvalue()
        base64_bytes = b64encode(image_bytes)
        return base64_bytes.decode('utf-8')


# model_name = "Qwen/Qwen2.5-VL-32B-Instruct"
model_name = "deepseek-ai/deepseek-vl2"


def _build_evaluation_payload(prompt, image_base64) -> dict:
    """构建评估请求负载。"""
    return {
        "model": f"{model_name}",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "stream": False
    }


def get_images(hotword_folder):
    """
    获取图片列表
    :param task_folders:
    :param hotword_folder: 热词文件夹名称
    :return: 图片列表
    """
    # 确保 hotword_folder 是字符串类型
    if isinstance(hotword_folder, list) and hotword_folder:
        hotword_folder = hotword_folder[0]
    elif not isinstance(hotword_folder, str):
        return []

    image_dir = hotword_folder
    if not os.path.exists(hotword_folder):
        return []
    images = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith(('.jpg', '.png'))]
    return images


if __name__ == "__main__":
    # logger.info("## 测试 call_llm")
    # prompt = "用简短的语言描述，生命的意义是什么？"
    # logger.info(f"## 提示: {prompt}")
    # response = call_llm(prompt)
    # logger.info(f"## 响应: {response}")

    print("## 测试 search_web")
    # query = "谁获得了2024年诺贝尔物理学奖？"
    # print(f"## 查询: {query}")
    # results = search_web(query,)
    # print(f"## 结果: {results}")
