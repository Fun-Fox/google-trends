import os

from webui.func.constant import root_dir
from webui.func.folder import get_task_folders, update_hot_word_folders
from webui.service.md2html import get_random_bg_image, convert_md_to_output
import gradio as gr
def build_tab():
    # 示例配置
    with gr.Row():
        task_folders = gr.Dropdown(label="任务记录", multiselect=False, choices=[''] + get_task_folders(),
                                   allow_custom_value=True)

        hot_word_folders = gr.Dropdown(label="热词目录", multiselect=False,
                                       allow_custom_value=True)
    refresh_button = gr.Button("刷新任务记录")  # 新增刷新按钮

    def update_drop_down():
        return gr.Dropdown(label="任务记录", multiselect=False, choices=[''] + get_task_folders(),
                           allow_custom_value=True)

    refresh_button.click(update_drop_down, outputs=task_folders)

    task_folders.change(fn=update_hot_word_folders, inputs=task_folders, outputs=hot_word_folders)

    # 显示 summary.md 内容
    md_viewer = gr.Markdown(label="新闻总结报告")
    input_md_path = gr.Textbox(visible=False)

    # 输出路径作为隐藏输入
    output_html = gr.Textbox(visible=False)
    output_image = gr.Textbox(visible=False)

    # ===== 新增按钮 =====
    convert_button = gr.Button("🖼️ Markdown 转图片", variant="primary")

    # ===== 新增输出组件 =====
    html_output = gr.HTML(label="生成的 HTML 预览")
    image_output = gr.Image(label="生成的图片预览")


    # ===== 自动加载 summary.md 文件路径 =====
    def load_summary_and_paths(hot_word_path):
        if not hot_word_path:
            return "", "", "", ""

        md_dir = os.path.join(hot_word_path, "md")
        # 查找 .md 文件
        md_files = [f for f in os.listdir(md_dir) if f.endswith(".md")]
        if not md_files:
            return "未找到 .md 文件", "", "", ""

        input_md_path = os.path.join(md_dir, md_files[0])  # 取第一个

        # 构建输出路径
        base_name = os.path.splitext(os.path.basename(input_md_path))[0]
        output_html = os.path.join(md_dir, f"{base_name}.html")
        output_image = os.path.join(md_dir, f"{base_name}.png")

        # 读取 Markdown 内容
        if os.path.exists(input_md_path):
            with open(input_md_path, encoding='utf-8') as f:
                content = f.read()
        else:
            content = "未找到 summary.md 文件"

        return (
            content,
            input_md_path,
            output_html,
            output_image
        )

    # 热词目录变更后自动更新 Markdown 展示和路径信息
    hot_word_folders.change(
        fn=load_summary_and_paths,
        inputs=[hot_word_folders],
        outputs=[
            md_viewer,
            input_md_path,
            output_html,
            output_image
        ]
    )


    # ===== 定义按钮点击事件 =====
    def on_convert_click(md_path, html_path, image_path):
        if not md_path or not os.path.exists(md_path):
            return "❌ Markdown 文件不存在，无法转换", None

        try:
            # 调用你的转换函数
            bg_folder = os.path.join(root_dir, "webui", "bg")
            bg_image_path = get_random_bg_image(bg_folder)
            bg_image_url = bg_image_path.replace("\\", "/") if bg_image_path else None

            font_url = "https://fonts.googleapis.com/css2?family=Roboto&display=swap"

            convert_md_to_output(
                md_path=md_path,
                html_path=html_path,
                image_path=image_path,
                background_image=bg_image_url,
                custom_font=font_url
            )

            # 返回成功消息和生成的图片
            return f"✅ 转换成功！HTML 已保存至 {html_path}", image_path
        except Exception as e:
            return f"❌ 转换失败: {str(e)}", None


    # ===== 绑定按钮点击事件 =====
    convert_button.click(
        fn=on_convert_click,
        inputs=[input_md_path, output_html, output_image],
        outputs=[
            gr.Textbox(label="状态信息"),
            image_output
        ]
    )

    return hot_word_folders