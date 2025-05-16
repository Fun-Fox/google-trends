# tabs/trend_crawler.py
import gradio as gr

from webui.func.conf import load_regions_choices
from webui.service.crawler import run_crawler
from webui.func.log import update_task_log_textbox


def build_tab():
    gr.Markdown("点击“开始采集”按钮启动采集任务，并显示日志。")
    with gr.Row():
        with gr.Column():
            to_download_image = gr.Checkbox(label="下载Google Trends上的三张图片", value=False, )
            # 修改 origin 和 category 的 choices 属性

            choices_data = load_regions_choices()  # 加载 config.ini 中的 Regions 和 category_names
            origin = gr.Dropdown(label="地区", choices=list(choices_data['regions'].keys()), value="美国")
            category = gr.Dropdown(label="分类", choices=list(choices_data['category_names'].keys()),
                                   value="所有分类")
            nums = gr.Slider(minimum=1, maximum=25, step=1, label="热词采集数量（最大25）", value=25)
            button = gr.Button("开始采集")
            button.click(fn=run_crawler, inputs=[to_download_image, origin, category, nums],
                         outputs=gr.Textbox(label="采集结果"))
        gr.Textbox(label="采集日志", value=update_task_log_textbox, lines=10, max_lines=15,
                                      every=5)