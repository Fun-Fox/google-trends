import time

from dotenv import load_dotenv
import os
import requests

# 1. 从 .env 文件中获取 IP 地址
load_dotenv()
HEY_GEN_IP = os.getenv("HEY_GEN_IP", "127.0.0.1")

def call_easy_submit(audio_url, video_url, code):
    if '\\' in video_url:
        video_url= video_url.replace('\\', '/')
    url = f"http://{HEY_GEN_IP}:8383/easy/submit"
    data = {
        "audio_url": audio_url,
        "video_url": video_url,
        "code": code,
        "chaofen": 0,
        "watermark_switch": 0,
        "pn": 1
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"请求失败: {response.status_code}, {response.text}")


# 4. 每隔 5 秒调用 /easy/query 接口查询进度
def query_easy_status(task_code):
    url = f"http://{HEY_GEN_IP}:8383/easy/query?code={task_code}"
    max_retries = 30  # 增加最大重试次数以应对长时间任务
    attempt = 0

    while attempt < max_retries:
        try:
            response = requests.get(url, timeout=10)  # 添加超时
            attempt += 1

            if response.status_code == 200:
                result = response.json()

                print(f"第 {attempt} 次查询结果: {result}")
                if result.get("code") == 10004:
                    print("❌ 任务不存在！")
                    break
                if result.get("code") == 10000:
                    data = result.get("data", {})
                    if data.get("status") == 2 and data.get("progress") == 100:
                        video_path = data.get("result")
                        print(f"✅ 任务已完成！合成视频路径：{video_path}")
                        return video_path  # 返回视频路径
            else:
                print(f"第 {attempt} 次查询失败: {response.status_code}, {response.text}")

        except requests.RequestException as e:
            print(f"第 {attempt} 次请求异常: {e}")

        if attempt < max_retries:
            print(f"等待 5 秒后进行第 {attempt + 1} 次查询...")
            time.sleep(60)

    print("❌ 已达到最大查询次数，任务可能仍在处理中或接口异常。")
    return None  # 超时未完成或出错