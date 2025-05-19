import os
import gradio as gr

from webui.func.folder import get_task_folders, update_hot_word_folders


def build_tab():
    gr.Markdown("选择生成的配音以及参考数字人，生成数字人")
    with gr.Row():
        task_folders = gr.Dropdown(label="任务记录", multiselect=False, choices=[''] + get_task_folders(),
                                   allow_custom_value=True)

        hot_word_folders = gr.Dropdown(label="热词", multiselect=False,
                                       allow_custom_value=True)
    refresh_button = gr.Button("刷新任务记录")  # 新增刷新按钮

    def update_drop_down():
        return gr.Dropdown(label="任务记录", multiselect=False, choices=[''] + get_task_folders(),
                           allow_custom_value=True)
    refresh_button.click(update_drop_down, outputs=task_folders)
    task_folders.change(fn=update_hot_word_folders, inputs=task_folders, outputs=hot_word_folders)

    with gr.Row():
        tts_audio_selector = gr.Dropdown(label="选择角色配音(wav文件)", multiselect=False,allow_custom_value=True)
        video_selector = gr.Dropdown(label="选择角色参考数字人", multiselect=False, allow_custom_value=True)

    def get_tts_wav_audio(hot_word_path):
        """
        根据热词路径，读取其下 tts 文件夹中的 .wav 文件
        :param hot_word_path: 热词文件夹路径
        :return: 包含 .wav 文件名的列表，用于 Dropdown 显示
        """
        if not hot_word_path or not os.path.exists(hot_word_path):
            return []

        tts_dir = os.path.join(hot_word_path, "tts")
        if not os.path.isdir(tts_dir):
            return []

        wav_files = [f for f in os.listdir(tts_dir) if f.endswith(".wav")]
        return wav_files

    hot_word_folders.change(fn=get_tts_wav_audio, inputs=[hot_word_folders],
                            outputs=tts_audio_selector)

    # 生成按钮
    generate_button = gr.Button("生成数字人")

    from heygem.digital_human_pipeline import digital_human_pipeline
    def gen_digital_human(tts_audio_url, video_url, hot_word_path):
        print(tts_audio_url, video_url, hot_word_path)
        digital_human_pipeline(tts_audio_url, video_url, hot_word_path)

    generate_button.click(fn=gen_digital_human, inputs=[tts_audio_selector, video_selector, hot_word_folders])


