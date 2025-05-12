# tabs/trend_crawler.py
import gradio as gr
from core import crawl_google_trends_page
from agent.main import hot_word_research_assistant

def run_crawler(to_download_image, origin, category):
    # 模拟启动爬虫逻辑
    return "✅ 热点采集任务已完成"

def build_tab():
    with gr.Row():
        to_download_image = gr.Checkbox(label="下载Google Trends上的三张图片", value=False)
        origin = gr.Dropdown(label="地区", choices=["美国", "中国", "日本"], value="美国")
        category = gr.Dropdown(label="分类", choices=["所有分类", "科技", "娱乐"], value="所有分类")
        button = gr.Button("开始采集")
        output = gr.Textbox(label="采集结果")
        button.click(fn=run_crawler, inputs=[to_download_image, origin, category], outputs=output)

    task_log_textbox = gr.Textbox(label="采集日志", value="暂无日志...", lines=10, every=5)