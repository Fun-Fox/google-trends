import datetime
import os

from agent import hot_word_research_assistant
from core import get_logger
from webui.func.constant import task_root_dir, root_dir
from webui.func.md2html import (get_random_bg_image,convert_md_to_output)


def research_all_hot_word(task_folders, language):
    agent_log_file_path = f"agent_{datetime.datetime.now().strftime('%Y年%m月%d日%H时%M分')}.log"

    agent_logger = get_logger(__name__, agent_log_file_path)

    task_dir = os.path.join(task_root_dir, task_folders)
    # 修改逻辑：只扫描 task_root_dir 下的一层目录
    hot_words_folders = [os.path.join(task_dir, d) for d in os.listdir(task_dir) if
                         os.path.isdir(os.path.join(task_dir, d))]

    result = []
    print(f"开始处理热词文件夹：{hot_words_folders}")
    for hot_words_folders_path in hot_words_folders:
        try:
            ret = hot_word_research_assistant(hot_words_folders_path, language, agent_logger)
            print(f"热词处理成功：{hot_words_folders}")
            print(f"查询md汇总文件,：{hot_words_folders}")
            input_md_path=load_summary_and_paths(hot_words_folders_path)
            convert_to_img(input_md_path)
        except Exception as e:
            print(f"正在处理热词：{hot_words_folders_path}发生异常，下一个热词")
            continue
        result.append(ret)
    return result


def research_hot_word(hot_words_folders_path, language):
    print(f"开始处理热词文件夹：{hot_words_folders_path},输出语言{language}")
    agent_log_file_path = f"agent_{datetime.datetime.now().strftime('%Y年%m月%d日%H时%M分')}.log"

    agent_logger = get_logger(__name__, agent_log_file_path)

    ret = hot_word_research_assistant(hot_words_folders_path, language, agent_logger)
    print(f"热词处理成功：{hot_words_folders_path}")
    print(f"查询md汇总文件,：{hot_words_folders_path}")
    input_md_path = load_summary_and_paths(hot_words_folders_path)
    convert_to_img(input_md_path)
    return ret



def load_summary_and_paths(hot_word_path):
    if not hot_word_path:
        return "",

    md_dir = os.path.join(hot_word_path, "md")
    # 查找 .md 文件
    md_files = [f for f in os.listdir(md_dir) if f.endswith(".md")]
    if not md_files:
        return "未找到 .md 文件", "", "", ""
    # 获取完整路径，并按修改时间排序
    files_with_path = [os.path.join(md_dir, f) for f in md_files]
    latest_file = max(files_with_path, key=os.path.getmtime)  # 最新修改的文件

    # input_md_path = os.path.join(md_dir, md_files[0])  # 取第一个

    return latest_file


# ===== 定义按钮点击事件 =====
def convert_to_img(md_path):
    if not md_path or not os.path.exists(md_path):
        return "❌ Markdown 文件不存在，无法转换"

    try:
        # 调用你的转换函数
        bg_folder = os.path.join(root_dir, "webui", "bg")
        bg_image_path = get_random_bg_image(bg_folder)
        bg_image_url = bg_image_path.replace("\\", "/") if bg_image_path else None

        font_url = "https://fonts.googleapis.com/css2?family=Roboto&display=swap"
        base_name = os.path.splitext(os.path.basename(md_path))[0]
        md_dir = os.path.dirname(md_path)
        output_html = os.path.join(md_dir, f"{base_name}.html")
        output_image = os.path.join(md_dir, f"{base_name}.png")
        video_path = os.path.join(md_dir, f"{base_name}.mp4")
        html_path = output_html
        image_path = output_image

        convert_md_to_output(
            md_path=md_path,
            html_path=html_path,
            image_path=image_path,
            video_path=video_path,
            background_image=bg_image_url,
            custom_font=font_url
        )
        # 返回成功消息和生成的图片
        return f"✅ 转换成功！HTML 已保存至 {html_path}"
    except Exception as e:
        return f"❌ 转换失败: {str(e)}"
