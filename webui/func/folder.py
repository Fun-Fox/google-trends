import os
import gradio as gr
import pandas as pd
from dotenv import load_dotenv

from webui.func.constant import task_root_dir, root_dir

load_dotenv()


def get_task_folders():
    """
    获取任务文件夹列表
    :return: 任务文件夹列表
    """
    # task_dir = task_dir
    if not os.path.exists(task_root_dir):
        return []
    folders = os.listdir(task_root_dir)
    return folders


def update_drop_down():
    return gr.Dropdown(label="采集热词任务列表", multiselect=False, choices=[''] + get_task_folders(),
                       allow_custom_value=True)


# 修改回调函数，正确更新 hotword_folders 的选项
def update_hot_word_folders(task_folder):
    if isinstance(task_folder, list) and task_folder:
        task_folder = task_folder[0]
    elif not isinstance(task_folder, str):
        return []
    task_dir = os.path.join(task_root_dir, task_folder)
    if not os.path.exists(task_dir):
        return []
    folders = [os.path.join(task_dir, folder) for folder in os.listdir(task_dir) if
               os.path.isdir(os.path.join(task_dir, folder))]
    if folders:
        return gr.Dropdown(choices=[''] + folders, label="热词文件夹", value='', interactive=True)
    else:
        return gr.Dropdown(choices=[], label="热词文件夹", value="", interactive=True)


def read_result_csv_file(csv_file_path):
    if csv_file_path is None or csv_file_path == '':
        return gr.DataFrame(value=None, label="热词口播文案显示(CSV文件)", column_widths=[20, 50],
                            max_height=150, max_chars=100), gr.Dropdown(
            label="选择口播文案", choices=[],
            allow_custom_value=True)
    csv_path = csv_file_path
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        # 检查 'hot_word' 列是否存在
        if 'hot_word' not in df.columns:
            print(f"CSV 文件中缺少 'hot_word' 列: {csv_path}")
            return gr.DataFrame(value=None, label="热词口播文案显示(CSV文件)", column_widths=[20, 150],
                                max_height=150, max_chars=200), gr.Dropdown(
                label="选择口播文案", choices=[],
                allow_custom_value=True)
        if 'result' not in df.columns:
            # 如果没有 result 列，提示用户“口播文案未生成”
            print(f"CSV 文件中缺少 'result' 列: {csv_path}")
            return gr.DataFrame(value=None, label="热词口播文案显示(CSV文件)", column_widths=[20, 150],
                                max_height=150, max_chars=200), gr.Dropdown(
                label="选择口播文案", choices=[],
                allow_custom_value=True)

        # 获取 'hot_word' 列的内容
        combined_choices = []
        for hw, hwc in zip(df['hot_word'], df['result']):
            # 使用 \n---\n 分割字符串为列表
            if hwc is None or str(hwc) == '' and str(hw) == 'nan':
                continue
            if '---' in str(hwc):
                results_list = hwc.split('---')
                for idx, result_item in enumerate(results_list, start=1):
                    combined_choices.append(f"{hw}/[{idx}]/{result_item.strip()}")
            elif '---' not in str(hwc):
                combined_choices.append(f"{hw}/[1]/{str(hwc).strip()}")
        # results_list = hwc.split('---')

        return gr.DataFrame(df[['hot_word', 'result']], label="热词口播文案显示(CSV文件)",
                            column_widths=[20, 150],
                            max_height=150, max_chars=200), gr.Dropdown(
            label="选择口播文案", choices=combined_choices,
            allow_custom_value=True)
    except Exception as e:
        print(f"口播音频时，读取 CSV 文件时发生错误: {e}")
        return "", []


# 获取 tts 文件夹下的所有子文件夹
def get_tts_folders():
    tts_dir = os.path.join(root_dir, os.getenv("TASK_DIR"), "tts")  # 修改为实际路径
    if not os.path.exists(tts_dir):
        return []

    folders = [f for f in os.listdir(tts_dir) if os.path.isdir(os.path.join(tts_dir, f))]
    return folders


# 根据选中的子文件夹，获取其中的 .wav 文件
def get_wav_files_in_folder(selected_folder):
    if not selected_folder:
        return []

    folder_path = os.path.join(root_dir, os.getenv("TASK_DIR"), "tts", task_name, selected_folder)
    if not os.path.exists(folder_path):
        return []

    wav_files = [f for f in os.listdir(folder_path) if f.endswith('.wav')]
    return wav_files


# 获取参考视频文件夹下的所有 .mp4 文件
def get_reference_videos():
    video_dir = os.path.join(root_dir, "doc", "数字人", "参考视频")
    if not os.path.exists(video_dir):
        return []

    videos = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
    return videos
