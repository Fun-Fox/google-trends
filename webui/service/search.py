import datetime
import os
from typing import List

from lxml.isoschematron import extract_xsd

from agent import hot_word_research_assistant
from agent.tools.summary import generate_news_summary_report
from core import get_logger
from webui.utils.constant import task_root_dir, root_dir
from webui.utils.md2html import (get_random_bg_image, convert_md_to_output)
from webui.utils.png2notion import extract_title, upload_image_and_create_notion_page


async def research_all_hot_word(task_folders, language):
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
            input_md_path = load_summary_and_paths(hot_words_folders_path)
            await convert_md_file_to_img(input_md_path)
        except Exception as e:
            print(f"正在处理热词：{hot_words_folders_path}发生异常，下一个热词")
            continue
        result.append(ret)
    return result


import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()


def get_md_and_image_paths(hot_word_folder: str) -> (str, List[str]):
    """
    自动查找 hot_word_folder 下的 md 文件夹中的 .md 文件，以及同目录下的图片文件
    返回：
        md_file: Markdown 文件路径
        image_paths: 图片文件路径列表（支持多图）
    """
    # 构建 md 文件夹路径
    md_dir = os.path.join(hot_word_folder, "md")

    # 查找 .md 文件（取最新修改的一个）
    if not os.path.exists(md_dir):
        raise FileNotFoundError(f"未找到 md 文件夹: {md_dir}")

    md_files = [f for f in os.listdir(md_dir) if f.endswith(".md")]
    if not md_files:
        raise FileNotFoundError(f"未在 {md_dir} 中找到 .md 文件")
    latest_md_file = max([os.path.join(md_dir, f) for f in md_files], key=os.path.getmtime)

    # 查找图片文件（支持常见格式）
    SUPPORTED_IMAGE_EXTS = {".png"}
    image_paths = [
        os.path.join(md_dir, f)
        for f in os.listdir(md_dir)
        if os.path.splitext(f)[1].lower() in SUPPORTED_IMAGE_EXTS
    ]

    if not image_paths:
        raise FileNotFoundError(f"未在 {md_dir} 中找到任何图片文件")

    return latest_md_file, image_paths[-1]


def to_notion(hot_word_folders):
    try:
        database_id = os.getenv("DATABASE_ID")
        latest_md_file, image_path = get_md_and_image_paths(hot_word_folders)
        title = extract_title(latest_md_file)
        page = upload_image_and_create_notion_page(database_id, title, image_path)
    except Exception as e:
        print(f"上传失败: {e}")
        return f"上传失败: {e}"
    return f"上传成功: 请访问{page['url']}"


async def md_to_img(hot_words_folders_path, language):
    agent_log_file_path = f"agent_{datetime.datetime.now().strftime('%Y年%m月%d日%H时%M分')}.log"

    agent_logger = get_logger(__name__, agent_log_file_path)
    hot_words = os.path.basename(hot_words_folders_path)
    task_dir = os.path.dirname(hot_words_folders_path)
    hot_words_file_name = os.getenv("HOT_WORDS_FILE_NAME")
    csv_path = os.path.join(task_dir, hot_words_file_name)
    task_name = os.path.basename(task_dir)
    task_time = task_name.split('_')[0]
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"md_to_img:CSV 文件不存在: {csv_path}")
    df = pd.read_csv(csv_path)
    matched_rows = df[df['hot_word'] == hot_words]

    if matched_rows.empty:
        print(f"未找到热词 '{hot_words}' 对应的行")
        return None

    required_columns = ['output', 'highlights', 'search_volume',
                        'search_growth_rate', 'search_active_time', ]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise KeyError(f"md_to_img:缺失以下字段: {missing_cols}")
        # 6. 返回所需字段的数据（示例返回第一行）
    first_row = matched_rows.iloc[0]

    highlights_str = first_row["highlights"]
    output = first_row['output']
    hot_word_info = {
        'search_volume': first_row["search_volume"],
        'search_growth_rate': first_row["search_growth_rate"],
        'search_active_time': first_row["search_active_time"],
        'current_date': task_time
    }

    ret = generate_news_summary_report(highlights_str, output, hot_words_folders_path, hot_word_info, agent_logger,
                                       language)
    input_md_path = ret['file_path']
    # print(f"查询md汇总文件,：{hot_words_folders_path}")
    # input_md_path = load_summary_and_paths(hot_words_folders_path)
    # print(f"正在将md转为图片、视频、html：{hot_words_folders_path}")

    await convert_md_file_to_img(input_md_path)
    return "转换html、图片、视频成功"


async def research_hot_word(hot_words_folders_path, language):
    print(f"开始处理热词文件夹：{hot_words_folders_path},输出语言{language}")
    agent_log_file_path = f"agent_{datetime.datetime.now().strftime('%Y年%m月%d日%H时%M分')}.log"

    agent_logger = get_logger(__name__, agent_log_file_path)

    ret = hot_word_research_assistant(hot_words_folders_path, language, agent_logger)
    print(f"热词处理成功：{hot_words_folders_path}")
    print(f"查询md汇总文件,：{hot_words_folders_path}")
    input_md_path = load_summary_and_paths(hot_words_folders_path)
    await convert_md_file_to_img(input_md_path)
    return ret


def load_summary_and_paths(hot_word_path):
    if not hot_word_path:
        return "",

    md_dir = os.path.join(hot_word_path, "md")
    if os.path.exists(md_dir):
        # 查找 .md 文件
        md_files = [f for f in os.listdir(md_dir) if f.endswith(".md")]
        if not md_files:
            return None
        # 获取完整路径，并按修改时间排序
        files_with_path = [os.path.join(md_dir, f) for f in md_files]
        latest_file = max(files_with_path, key=os.path.getmtime)  # 最新修改的文件

        # input_md_path = os.path.join(md_dir, md_files[0])  # 取第一个
        return latest_file
    else:
        return None


# ===== 定义按钮点击事件 =====
async def convert_md_file_to_img(md_path, duration=7000):
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
        print("开始转换..")

        await convert_md_to_output(
            md_path=md_path,
            html_path=html_path,
            image_path=image_path,
            video_path=video_path,
            background_image=bg_image_url,
            custom_font=font_url,
            duration=duration
        )
        # 返回成功消息和生成的图片
        return f"✅ 转换成功！HTML 已保存至 {html_path}"
    except Exception as e:
        return f"❌ 转换失败: {str(e)}"
