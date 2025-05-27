import argparse
import os

import gradio as gr
from dotenv import load_dotenv

from webui.utils.constant import root_dir
from webui.views import (
    cookie_settings,
    trend_crawler,
    crontab_tasks,
    voice_text_generation,
    voice_audio,
    digital_human,
    deep_search,
    downloads
)

load_dotenv()
import requests

# 插入在 url 相关逻辑的位置
# url = f"{os.getenv('LOCAL_LLM_URL')}" 如果变量不为空，则请求一下url，查看是否响应，不响应则gr报错，提示异常
url = os.getenv('LOCAL_LLM_URL')

with gr.Blocks(title="GT") as app:
    if url:
        try:
            response = requests.get(url,timeout=5)
        except requests.exceptions.Timeout:
            gr.Markdown("⚠️ 请求超时：服务响应时间过长，请检查本地大模型是否已正常运行。")
        except requests.ConnectionError:
            gr.Markdown("⚠️ 无法连接到服务：请确认服务是否正在运行，以及 LOCAL_LLM_URL 是否配置正确。")

    gr.Markdown("# Google Trends 热点采集、优质报道深度搜索、口播文案生成、口播语音生成、数字人生成、定时批量任务设置")

    with gr.Tab("Cookie 设置"):
        cookie_settings.build_tab()

    with gr.Tab("时下热词.采集"):
        trend_crawler.build_tab()

    with gr.Tab("优质报道.深度搜索"):
        deep_search.build_tab()

    with gr.Tab("热点.定时任务"):
        crontab_tasks.build_tab()

    with gr.Tab("口播文案生成"):
        try:
            voice_text_generation.build_tab()
        except Exception as e:
            gr.Markdown(f"⚠️ 加载失败: {str(e)}")

    with gr.Tab("口播音频生成"):
        voice_audio.build_tab()
    #
    with gr.Tab("多角色数字人合成"):
        digital_human.build_tab()
    #
    with gr.Tab(" 整合及下载"):
        downloads.build_tab()


def start():
    import nltk
    nltk_path = os.path.join(root_dir, "nltk_data")
    os.makedirs(nltk_path, exist_ok=True)
    # 它是nltk的一个预训练分词模型，用于：英文句子分割识别缩写、标点等特殊结构这个资源被很多NLP模块依赖，比如新闻摘要提取、文章清洗、文本摘要生成等模块
    # 下载所需的 punkt_tab 资源
    nltk.data.path.append(os.path.join(root_dir, "nltk_data"))  # 添加自定义路径
    nltk.download('punkt_tab', download_dir=nltk_path)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=7866, help='Gradio 应用监听的端口号')
    args = parser.parse_args()
    app.queue(20)
    if os.getenv('PLATFORM', '') == 'local':
        app.launch(debug=True, share=False,
                   allowed_paths=[os.path.join(root_dir, os.getenv('ROOT', '')),
                                  os.path.join(root_dir, os.getenv('ZIP_DIR', '')),
                                  os.path.join(root_dir, os.getenv('TASK_DIR', '')),
                                  os.path.join(root_dir, 'Log'), nltk_path],
                   server_port=args.port, favicon_path="favicon.ico")
    elif os.getenv('PLATFORM', '') == 'server':
        app.launch(share=False, server_name="0.0.0.0",
                   allowed_paths=[os.path.join(root_dir, os.getenv('ROOT', '')),
                                  os.path.join(root_dir, os.getenv('ZIP_DIR', '')),
                                  os.path.join(root_dir, os.getenv('TASK_DIR', '')),
                                  os.path.join(root_dir, "doc"),
                                  os.path.join(root_dir, 'Log'), nltk_path],
                   server_port=args.port, favicon_path="favicon.ico")
