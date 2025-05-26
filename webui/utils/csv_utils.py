import os

import pandas as pd

from webui.utils.constant import task_root_dir
import gradio as gr

def get_csv_files(task_folder):
    if not task_folder:
        return gr.Dropdown(label="选择热词清单(CSV文件)", choices=[], allow_custom_value=False)
    task_dir = os.path.join(task_root_dir, task_folder)
    if not os.path.exists(task_dir):
        return gr.Dropdown(label="选择热词清单(CSV文件)", choices=[], allow_custom_value=False)
    csv_files = [''] + [os.path.join(task_dir, f) for f in os.listdir(task_dir) if f.endswith('.csv')]
    return gr.Dropdown(label="选择热词清单(CSV文件)", value='', choices=csv_files,
                       allow_custom_value=False)


def clear_result_button_click(hot_word_csv_files_path):
    if hot_word_csv_files_path is None or hot_word_csv_files_path == '':
        return "请先选择文件"
    csv_path = hot_word_csv_files_path
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        df['result'] = ''
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    except Exception as e:
        return "result列清空异常" + e
    return "csv清空result列成功"


def read_csv_file(csv_file_path):
    if csv_file_path is None or csv_file_path == '':
        return gr.DataFrame(value=None, label="热词叙事内容显示(CSV文件)", column_widths=[20, 50, 50],
                            max_height=150, max_chars=100), gr.Dropdown(
            label="选择叙事内容", choices=[], allow_custom_value=True)
    csv_path = csv_file_path
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        # 检查 'hot_word' 列是否存在
        if 'hot_word' not in df.columns:
            print(f"CSV 文件中缺少 'hot_word' 列: {csv_path}")
            return gr.DataFrame(value=None, label="热词叙事内容显示(CSV文件)",
                                column_widths=[20, 50, 50], max_height=150, max_chars=100), gr.Dropdown(
                label="选择叙事内容", choices=[], allow_custom_value=True)

        # 获取 'hot_word' 列的内容
        combined_choices = []
        # for hw, hwc in zip(df['hot_word'], df['chinese']):
        #     if pd.notna(hwc) and hwc != "":  # 判断中文叙事不为空
        #         combined_choices.append(f"{hw}/{hwc}")

        for hw, hwc in zip(df['hot_word'], df['output']):
            if pd.notna(hwc) and hwc != "":  # 判断英文叙事不为空
                combined_choices.append(f"{hw}/{hwc}")
        return gr.DataFrame(df[['hot_word', 'chinese', 'output']], label="热词叙事内容显示(CSV文件)",
                            column_widths=[20, 50, 50],
                            max_height=150, max_chars=100), gr.Dropdown(
            label="选择叙事文案", choices=combined_choices,
            allow_custom_value=True)
    except Exception as e:
        print(f"口播文案：读取 CSV 文件时发生错误: {e}")
        return "", []
