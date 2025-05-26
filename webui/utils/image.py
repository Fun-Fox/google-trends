import os
import gradio as gr
import pandas as pd


def get_hot_word_images_and_narratives(hot_word_folder):
    """
    获取图片列表并读取 CSV 文件中的 hotword 对应的 chinese 和 output 叙事
    :param hot_word_folder: 热词文件夹名称
    :return: 图片列表和叙事内容
    """
    # 确保 hotword_folder 是字符串类型
    if isinstance(hot_word_folder, list) and hot_word_folder:
        hot_word_folder = hot_word_folder[0]
    elif not isinstance(hot_word_folder, str):
        return [], ""

    image_dir = hot_word_folder
    task_dir = os.path.dirname(hot_word_folder)
    hot_word = os.path.basename(hot_word_folder)
    if not os.path.exists(hot_word_folder):
        return [], ""

    # 获取图片列表
    images = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith(('.jpg', '.png'))]

    # 获取 CSV 文件路径
    csv_files = [os.path.join(task_dir, f) for f in os.listdir(task_dir) if f.endswith('.csv')]
    if not csv_files:
        return gr.Gallery(label="图片", value=images, interactive=False), ""

    # 读取第一个 CSV 文件
    csv_path = csv_files[0]
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        if 'hot_word' in df.columns and 'chinese' in df.columns and 'output' in df.columns:
            # 过滤出 hot_word 为 'hotword' 的行
            filtered_df = df[df['hot_word'] == hot_word]
            if not filtered_df.empty:
                narratives = filtered_df[['chinese', 'output']].to_dict(orient='records')
                narratives_str = "\n".join(
                    [f"===中文===\n{n['chinese']}\n===其他语言===\n {n['output']}\n" for n in narratives])
                return gr.Gallery(label="热词-对应图片信息", value=images, interactive=False, columns=5), gr.Textbox(
                    label="热词叙事", value=narratives_str, lines=5, interactive=False)
    except Exception as e:
        print(f"webui:读取 CSV 文件时发生错误: {e}")

    return gr.Gallery(label="图片", value=images, interactive=False), ""
