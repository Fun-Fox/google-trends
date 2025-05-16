import os

import gradio as gr

from webui.func.build_zip import download_folder, refresh_zip_files
from webui.func.constant import task_root_dir, root_dir


def build_tab():
    gr.Markdown("### 查看历史记录\n支持单个文件夹或多个文件压缩后下载。")
    with gr.Row():
        with gr.Column():
            file_explorer = gr.FileExplorer(
                label="任务文件夹",
                glob="**/*",
                root_dir=task_root_dir,
                every=1,
                height=300,
            )
            refresh_btn = gr.Button("刷新")

            def update_file_explorer():
                return gr.FileExplorer(root_dir="")

            def update_file_explorer_2():
                return gr.FileExplorer(root_dir=task_root_dir)

            refresh_btn.click(update_file_explorer, outputs=file_explorer).then(update_file_explorer_2,
                                                                                outputs=file_explorer)
        download_output = gr.File(label="ZIP下载链接",
                                  value=refresh_zip_files,
                                  height=100,
                                  every=10)
    download_button = gr.Button("ZIP压缩")



    download_button.click(
        fn=download_folder,  # 调用下载函数
        inputs=file_explorer,  # 获取选中的文件夹路径
        outputs=download_output  # 提供下载链接
    )