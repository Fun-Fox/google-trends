import os
import gradio as gr

from webui.func.folder import get_tts_folders, get_wav_files_in_folder, get_reference_videos


def build_tab():
    with gr.Row():
        # 下拉选择 tts 文件夹下的子文件夹
        tts_folders = gr.Dropdown(
            label="选择已经生成口播音频的任务",
            choices=get_tts_folders(),
            allow_custom_value=True
        )

        # 下拉选择选中子文件夹下的 .wav 文件
        wav_files = gr.Dropdown(
            label="选择 .wav 音频文件",
            choices=[],
            allow_custom_value=True
        )

        # 当选择 tts 子文件夹时，更新 .wav 文件的下拉选项
        tts_folders.change(
            fn=get_wav_files_in_folder,
            inputs=tts_folders,
            outputs=wav_files
        )

        # 下拉选择参考视频文件
        reference_videos = gr.Dropdown(
            label="选择参考视频文件",
            choices=get_reference_videos(),
            allow_custom_value=False
        )

