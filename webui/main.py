import argparse
import os

import gradio as gr
from dotenv import load_dotenv

from webui.func.constant import root_dir
from webui.views import cookie_settings, trend_crawler, deep_search, voice_script_generation, voice_synthesis, \
    digital_human, downloads

load_dotenv()

with gr.Blocks(title="GT") as app:
    gr.Markdown("# Google Trends 热点采集、优质报道深度搜索、口播文案生成、口播语音生成、数字人生成、定时批量任务设置")

    with gr.Tab("Cookie 设置"):
        cookie_settings.build_tab()

    with gr.Tab("时下热词-采集"):
        trend_crawler.build_tab()

    with gr.Tab("优质报道-深度搜索"):
        deep_search.build_tab()

    with gr.Tab("口播文案生成"):
        voice_script_generation.build_tab()

    with gr.Tab("口播音频生成"):
        voice_synthesis.build_tab()

    with gr.Tab("多角色数字人合成"):
        digital_human.build_tab()

    with gr.Tab("下载"):
        downloads.build_tab()

def start():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=7866, help='Gradio 应用监听的端口号')
    args = parser.parse_args()
    app.queue(20)
    if os.getenv('PLATFORM', '') == 'local':
        app.launch(share=False,
                   allowed_paths=[os.path.join(root_dir, os.getenv('ROOT', '')),
                                  os.path.join(root_dir, os.getenv('ZIP_DIR', '')),
                                  os.path.join(root_dir, os.getenv('TASK_DIR', '')),
                                  os.path.join(root_dir, "tmp"),
                                  os.path.join(root_dir, 'Log')],
                   server_port=args.port, favicon_path="favicon.ico")
    elif os.getenv('PLATFORM', '') == 'server':
        app.launch(share=False, server_name="0.0.0.0",
                   allowed_paths=[os.path.join(root_dir, os.getenv('ROOT', '')),
                                  os.path.join(root_dir, os.getenv('ZIP_DIR', '')),
                                  os.path.join(root_dir, os.getenv('TASK_DIR', '')),
                                  os.path.join(root_dir, "doc"),
                                  os.path.join(root_dir, "tmp"),
                                  os.path.join(root_dir, 'Log')],
                   server_port=args.port, favicon_path="favicon.ico")
