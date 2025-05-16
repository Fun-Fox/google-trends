from dotenv import load_dotenv
import os
import requests

# 1. 从 .env 文件中获取 IP 地址
load_dotenv()
HEY_GEN_IP = os.getenv("HEY_GEN_IP", "127.0.0.1")

def call_easy_submit(audio_url, video_url, code):
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
