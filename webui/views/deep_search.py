import gradio as gr

from webui.utils.image import get_hot_word_images_and_narratives
from webui.utils.log import update_agent_log_textbox
from webui.service.search import research_all_hot_word, research_hot_word, md_to_img, to_notion
from webui.utils.folder import get_task_folders, update_hot_word_folders


def build_tab():
    gr.Markdown("选择任务记录文件夹以查看热词、图片、以及热词对应的叙事csv文件。")
    with gr.Row():
        task_folders = gr.Dropdown(label="任务记录", multiselect=False, choices=[''] + get_task_folders(),
                                   allow_custom_value=True)

        hot_word_folders = gr.Dropdown(label="热词", multiselect=False,
                                       allow_custom_value=True)
    refresh_button = gr.Button("刷新任务记录")  # 新增刷新按钮
    narratives_textbox = gr.Textbox(label="叙事", value="", lines=5, interactive=False)

    def update_drop_down():
        return gr.Dropdown(label="任务记录", multiselect=False, choices=[''] + get_task_folders(),
                           allow_custom_value=True)

    refresh_button.click(update_drop_down, outputs=task_folders)

    with gr.Row():
        with gr.Column():
            # 仅提供语言名称选项，不要编码
            language_dropdown = gr.Dropdown(
                label="选择采样信息输出语言",
                choices=["简体中文", "繁体中文", "英文", "日文", "韩文", "俄文"],
                value="简体中文"
            )

        with gr.Column():
            research_button = gr.Button("🤐特定-热词-网络搜索")

            research_button.click(fn=research_hot_word, inputs=[hot_word_folders, language_dropdown],
                                  outputs=gr.Textbox(label=""))
        with gr.Column():
            research_button = gr.Button("🤐热词-搜索内容转海报")

            research_button.click(fn=md_to_img, inputs=[hot_word_folders, language_dropdown],
                                  outputs=gr.Textbox(label=""))
        with gr.Column():
            research_button = gr.Button("🤐海报同步至Notion笔记")

            research_button.click(fn=to_notion, inputs=[hot_word_folders],
                                  outputs=gr.Textbox(label=""))
        with gr.Column():
            research_all_keyword_button = gr.Button("🤐全部-热词-网络搜索")

            research_all_keyword_button.click(fn=research_all_hot_word, inputs=[task_folders, language_dropdown],
                                              outputs=gr.Textbox(label=""))
    with gr.Row():
        gr.Textbox(label="AI搜索助手-执行记录", value=update_agent_log_textbox, lines=9,
                   max_lines=15,
                   every=5)
        image_gallery = gr.Gallery(label="热词-对应图片信息", value=[], interactive=False, columns=5)

    # 修改回调函数，正确更新 hotword_folders 的选项
    task_folders.change(fn=update_hot_word_folders, inputs=[task_folders], outputs=hot_word_folders)
    hot_word_folders.change(fn=get_hot_word_images_and_narratives, inputs=[hot_word_folders],
                            outputs=[image_gallery, narratives_textbox])
    # 修改get_images 增加获取hotword_folders 文件下的csv文件读取csv中hotword列对应的hotword 对应的chinese、english叙事，显示在textbox中
    # image_gallery 显示图片文件名称
