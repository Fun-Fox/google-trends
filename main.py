import gradio as gr
from tabs import cookie_settings, trend_crawler, deep_search, voice_script_generation, voice_synthesis, digital_human, downloads

from moviepy.editor import *

with gr.Blocks(title="Google Trends 助手") as app:
    with gr.Tab("Cookie 设置"):
        cookie_settings.build_tab()

    with gr.Tab("时下热词-采集"):
        trend_crawler.build_tab()

    with gr.Tab("时下热词-深度搜索"):
        deep_search.build_tab()

    with gr.Tab("口播文案生成"):
        voice_script_generation.build_tab()

    with gr.Tab("口播音频生成"):
        voice_synthesis.build_tab()

    with gr.Tab("多角色数字人合成"):
        digital_human.build_tab()

    with gr.Tab("下载"):
        downloads.build_tab()

if __name__ == "__main__":
    app.launch()