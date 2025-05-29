import os
import gradio as gr
from ffmpeg import output

from webui.utils.folder import get_task_folders, update_hot_word_folders
from heygem.digital_human_pipeline import digital_human_pipeline


def build_tab():
    """构建数字人生成页面 UI"""

    gr.Markdown("选择生成的配音以及参考数字人，生成数字人")

    # ======================
    # 第一行：任务记录 & 热词目录
    # ======================
    with gr.Row():
        task_folders = gr.Dropdown(
            label="任务记录",
            multiselect=False,
            choices=[''] + get_task_folders(),
            allow_custom_value=True
        )
        hot_word_folders = gr.Dropdown(
            label="热词目录",
            multiselect=False,
            allow_custom_value=True
        )

    refresh_button = gr.Button("刷新任务记录")  # 新增刷新按钮

    # ======================
    # 按钮事件绑定
    # ======================

    def refresh_task_dropdown():
        return gr.Dropdown(choices=[''] + get_task_folders())

    refresh_button.click(fn=refresh_task_dropdown, outputs=task_folders)
    task_folders.change(fn=update_hot_word_folders, inputs=task_folders, outputs=hot_word_folders)

    # ======================
    # 第二行：音频 & 视频选择器
    # ======================
    with gr.Row():
        tts_audio_selector = gr.Dropdown(
            label="选择角色配音 (WAV 文件)",
            multiselect=False,
            allow_custom_value=True
        )

        def get_ref_video_files():
            """
            获取 doc/数字人/参考视频 目录下的所有 .mp4 文件
            """
            video_dir = os.path.join("doc", "数字人", "参考视频")
            if not os.path.exists(video_dir):
                return []

            return [''] + [os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.endswith(".mp4")]

        video_selector = gr.Dropdown(
            label="选择角色参考视频 (MP4 文件)",
            multiselect=False,
            choices=get_ref_video_files(),
            allow_custom_value=True
        )

    def update_tts_wav_options(hot_word_path: str):
        """
        根据热词路径加载 tts 文件夹中的 wav 文件
        """
        if not hot_word_path or not os.path.isdir(hot_word_path):
            return []

        tts_dir = os.path.join(hot_word_path, "tts")
        if not os.path.isdir(tts_dir):
            return []
        wav_files = [os.path.join(tts_dir, f) for f in os.listdir(tts_dir) if f.endswith(".wav")]

        return gr.Dropdown(
            label="选择角色配音 (WAV 文件)",
            multiselect=False,
            choices=[''] + wav_files,
            allow_custom_value=True
        )

    # ======================
    # 事件绑定
    # ======================

    hot_word_folders.change(
        fn=update_tts_wav_options,
        inputs=[hot_word_folders],
        outputs=tts_audio_selector
    )

    # ======================
    # 生成按钮与执行函数
    # ======================
    generate_button = gr.Button("生成数字人")

    def gen_digital_human(tts_audio_file: str, video_file: str, hot_word_path: str):
        print(f"口播音频: {tts_audio_file}\n 参考视频: {video_file}\n 热词路径: {hot_word_path}")
        return digital_human_pipeline(tts_audio_file, video_file, hot_word_path)

    generate_button.click(
        fn=gen_digital_human,
        inputs=[tts_audio_selector, video_selector, hot_word_folders],
        outputs=[gr.Textbox(label="生成结果")]
    )
