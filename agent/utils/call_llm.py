import os
from asyncio import sleep
from dotenv import load_dotenv
load_dotenv()

# 设置代理
proxies = {
    "http": f"{os.getenv('PROXY_URL')}",
    "https": f"{os.getenv('PROXY_URL')}",
}

__all__ =["call_llm"]

def call_llm(prompt, logger=None, image_path='', ):
    if os.getenv("CLOUD_MODEL_NAME") != '' and image_path != "":
        # 只有视觉的模型调用云端模型
        logger.info(f"使用云端模型{os.getenv('CLOUD_MODEL_NAME')}")
        response,success = call_cloud_model(prompt, logger, image_path)
        return response,success
    if 'gemma3' in os.getenv("LOCAL_MODEL_NAME") and image_path != "":
        logger.info(f"使用本地模型{os.getenv('LOCAL_MODEL_NAME')}")
        response,success = call_local_llm(prompt, logger, image_path)
        return response,success
    elif 'gemma3' in os.getenv("LOCAL_MODEL_NAME") and image_path == "":
        logger.info(f"使用本地模型{os.getenv('LOCAL_MODEL_NAME')}")
        response,success = call_local_llm(prompt, logger)
        return response,success
    return None, None


def call_local_llm(prompt, logger=None, image_path='', ):
    # 支持视觉与非视觉模型  ·
    try:
        # logger.info(f"## 提示: {prompt}")
        # 使用本地ollama模型gemma3
        url = f"{os.getenv('LOCAL_LLM_URL')}"

        if os.getenv("LOCAL_MODEL_NAME") == "gemma3" and image_path != "":
            logger.info(f"使用本地模型{os.getenv('LOCAL_MODEL_NAME')},进行视觉操作")
            payload = {
                "model": f"{os.getenv('LOCAL_MODEL_NAME')}",
                "prompt": prompt,
                "stream": False,
                "image": convert_image_to_base64(image_path)
            }

        if image_path == "":
            logger.info(f"使用本地模型{os.getenv('LOCAL_MODEL_NAME')},进行语言(非视觉)操作")
            payload = {
                "model": f"{os.getenv('LOCAL_MODEL_NAME')}",
                "prompt": prompt,
                "stream": False
            }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logger.info(f"模型返回信息{response.json().get('response')}")
            return response.json().get("response", ""), True
        else:
            logger.error(f"错误: 无法从模型获取响应。状态码: {response.status_code}")
            return "错误: 无法从模型获取响应。", False
    except Exception as e:
        logger.error(f"调用LLM时发生异常: {e}")
        return "错误: 调用LLM时发生异常。", False


import os
import requests
from PIL import Image
from io import BytesIO
from base64 import b64encode

api_key = os.getenv("CLOUD_API_KEY")
api_url = os.getenv("CLOUD_API_URL")
MAX_RETRIES = 2


def call_cloud_model(prompt, logger=None, image_path=''):
    """评估图片与叙事的相关性，并对图片进行评分。

    Args:
        image_path: 图片文件路径。
        logger
    Returns:
        包含评估结果的字典。
        :param model_name:
        :param logger:
        :param image_path:
        :param prompt:
    """
    model_name = os.getenv("CLOUD_MODEL_NAME")
    for attempt in range(MAX_RETRIES):
        try:
            if image_path != "":
                logger.info(f"使用云端模型{os.getenv('CLOUD_MODEL_NAME')},进行视觉操作")

                # 将图片转换为Base64编码
                image_base64 = convert_image_to_base64(image_path)
                # 构建请求负载
                payload = _build_evaluation_payload(prompt, model_name, image_base64)
            else:
                logger.info(f"使用云端模型{os.getenv('CLOUD_MODEL_NAME')},进行语言(非视觉)操作")

                payload = _build_evaluation_payload(prompt, model_name, '')

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
                        return content,True  # 返回 content 字段
                    else:
                        logger.warning("API 响应中没有 choices 数据")
                        return "无内容", False
                except Exception as e:
                    logger.error(f"云端模型调用出现异常: {e}")
                    return "云端模型调用出现异常",False
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


def _build_evaluation_payload(prompt, model_name, image_base64='', ) -> dict:
    """构建评估请求负载。
    :type model_name: object
    """
    content = [
        {
            "type": "text",
            "text": prompt
        }
    ]

    # 仅当 image_base64 存在时添加图片内容
    if image_base64 != '':
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
        })

    return {
        "model": f"{model_name}",
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "stream": False
    }




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
