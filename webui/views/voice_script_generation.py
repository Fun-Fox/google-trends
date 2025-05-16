import gradio as gr
from webui.func.csv import get_csv_files, read_csv_file
from webui.func.folder import get_task_folders, update_drop_down
from webui.service.write import process_prompt, save_result, batch_gen_save_result

# 口播文案生成
def build_tab():
    gr.Markdown("""
            流程：选择采集热词任务 >> 查看已完成深度搜索的热词叙事内容 >> 设置口播人设提示词 >> 点击【生成】生成口播文案
            """)
    with gr.Row():
        with gr.Column():
            task_folders = gr.Dropdown(label="选择采集热词任务列表", multiselect=False,
                                       choices=[''] + get_task_folders(),
                                       allow_custom_value=True)
            refresh_button = gr.Button("刷新任务列表")  # 新增刷新按钮

            refresh_button.click(update_drop_down, outputs=task_folders)

        with gr.Column():
            hot_word_csv_files_path = gr.Dropdown(label="选择热词清单(CSV文件)", choices=[],
                                                  allow_custom_value=False)
            refresh_csv_1_button = gr.Button("刷新热词清单(CSV文件)")

            task_folders.change(fn=get_csv_files, inputs=task_folders, outputs=hot_word_csv_files_path)
            refresh_csv_1_button.click(fn=get_csv_files, inputs=task_folders, outputs=hot_word_csv_files_path)

    with gr.Row():
        content_textbox = gr.DataFrame(value=None, label="热词叙事内容显示(CSV文件)",
                                       column_widths=[20, 50, 50], max_height=150, max_chars=100)
        selected_row = gr.Dropdown(label="选择叙事内容", choices=[], allow_custom_value=True)

        hot_word_csv_files_path.change(fn=read_csv_file, inputs=[hot_word_csv_files_path],
                                       outputs=[content_textbox, selected_row])

    with gr.Row():
        prompt_textbox1 = gr.Textbox(label="请输入口播人设提示词 1(可编辑)",
                                     value="""- 制作播音文稿，使用专业的新闻播音主持风格\n- 使用中文输出\n- 直接切入内容，无需开场的问候\n- 通过标点符号(-)在任意位置控制停顿""",
                                     lines=3)

        prompt_textbox2 = gr.Textbox(label="请输入口播人设提示词 2(可编辑)", value="""- 制作播音文稿，使用幽默搞笑的相声风格\n- 使用英文输出\n- 通过标点符号(-)在任意位置控制停顿
                """, lines=3)
        prompt_textbox3 = gr.Textbox(label="请输入口播人设提示词 3(可编辑)", value="""- 制作播音文稿，使用愤世嫉俗的批判主义风格\n- 使用中文输出\n- 通过标点符号(-)在任意位置控制停顿
                """, lines=3)

    with gr.Row():
        with gr.Column():
            prompt_button1 = gr.Button("生成结果")
            result1 = gr.Textbox(label="结果", value="", max_lines=6, lines=5, interactive=False)
            prompt_button1.click(
                fn=process_prompt,
                inputs=[selected_row, prompt_textbox1],
                outputs=result1
            )
            save_button1 = gr.Button("保存结果")
            save_button1.click(
                fn=save_result,
                inputs=[result1, hot_word_csv_files_path, selected_row],
                outputs=gr.Textbox(label="", value="", interactive=False)
            )

            batch_button1 = gr.Button("批量生成并保存结果")
            batch_button1.click(
                fn=batch_gen_save_result,
                inputs=[prompt_textbox1, hot_word_csv_files_path],
                outputs=gr.Textbox(label="", value="", interactive=False)
            )

        with gr.Column():
            prompt_button2 = gr.Button("生成结果")
            result2 = gr.Textbox(label="结果", value="", max_lines=6, lines=5, interactive=False)
            prompt_button2.click(
                fn=process_prompt,
                inputs=[selected_row, prompt_textbox2],
                outputs=result2
            )
            save_button2 = gr.Button("保存结果")

            save_button2.click(
                fn=save_result,
                inputs=[result2, hot_word_csv_files_path, selected_row],
                outputs=gr.Textbox(label="", value="", interactive=False)
            )

            batch_button2 = gr.Button("批量生成并保存结果")
            batch_button2.click(
                fn=batch_gen_save_result,
                inputs=[prompt_textbox2, hot_word_csv_files_path],
                outputs=gr.Textbox(label="", value="", interactive=False)
            )

        with gr.Column():
            prompt_button3 = gr.Button("生成结果")
            result3 = gr.Textbox(label="结果", value="", max_lines=6, lines=5, interactive=False)
            prompt_button3.click(
                fn=process_prompt,
                inputs=[selected_row, prompt_textbox3],
                outputs=result3
            )
            save_button3 = gr.Button("保存结果")

            save_button3.click(
                fn=save_result,
                inputs=[result3, hot_word_csv_files_path, selected_row],
                outputs=gr.Textbox(label="", value="", interactive=False)
            )

            batch_button3 = gr.Button("批量生成并保存结果")
            batch_button3.click(
                fn=batch_gen_save_result,
                inputs=[prompt_textbox3, hot_word_csv_files_path],
                outputs=gr.Textbox(label="", value="", interactive=False)
            )
