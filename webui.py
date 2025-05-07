import argparse
import csv
import os
import datetime
import shutil
import zipfile
from asyncio import sleep
import sys
import time
import warnings
import pandas as pd
from dotenv import load_dotenv

from agent.main import hot_word_research_assistant, write_in_style_assistant
from core import init_browser, close_browser, get_logger
from core import crawl_google_trends_page
import gradio as gr

load_dotenv()
# 动态生成日志文件路径
task_date = datetime.datetime.now().strftime("%Y年%m月%d日%H时%M分")
task_log_file_path = os.path.join(f"task_{task_date}.log")
os.makedirs("logs", exist_ok=True)

task_root_dir = os.getenv("TASK_DIR", "tasks")
current_dir = os.path.dirname(os.path.abspath(__file__))


async def start_crawler(url, to_download_image, origin="", category=""):
    """
    启动采集任务
    :param to_download_image:
    :type origin: string
    :param category:
    :param url: 目标URL
    """
    # 获取当前时间并创建任务文件夹
    task_dir_file_name = os.path.join(task_root_dir, task_date + f'_{origin}_{category}')
    os.makedirs(task_root_dir, exist_ok=True)

    logger = get_logger(__name__, task_log_file_path)

    p, browser, context, page = await init_browser(logger)

    choices = load_choices()
    origin_code = choices['regions'].get(origin, "US")  # 默认值为 "US"
    category_code = int(choices['category_names'].get(category, "0"))  # 默认值为 "0"

    await crawl_google_trends_page(page, logger, origin=origin_code, category=category_code, url=url,
                                   task_dir=task_dir_file_name,
                                   to_download_image=to_download_image)

    # 关闭页面和上下文
    await page.close()
    await context.close()

    # 关闭浏览器
    await close_browser(p, browser, logger)


# 新增 Gradio Web 页面
async def run_crawler(to_download_image, origin, category):
    """
    运行采集任务
    :return: 爬取任务完成的消息
    """
    url = "https://trends.google.com/trending"

    await start_crawler(url, to_download_image, origin=origin, category=category)
    return "热点采集任务已完成"


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


def get_hotword_folders(task_folder):
    """
    获取热词文件夹列表
    :param task_folder: 任务文件夹名称
    :return: 热词文件夹列表
    """
    # 确保 task_folder 是字符串类型
    if isinstance(task_folder, list) and task_folder:
        task_folder = task_folder[0]
    elif not isinstance(task_folder, str):
        return []

    hotword_dir = os.path.join(task_root_dir, task_folder)
    if not os.path.exists(hotword_dir):
        return []
    folders = os.listdir(hotword_dir)
    return folders


def get_hot_word_images_and_narratives(hot_word_folder):
    """
    获取图片列表并读取 CSV 文件中的 hotword 对应的 chinese 和 english 叙事
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
        df = pd.read_csv(csv_path)
        if 'hot_word' in df.columns and 'chinese' in df.columns and 'english' in df.columns:
            # 过滤出 hot_word 为 'hotword' 的行
            filtered_df = df[df['hot_word'] == hot_word]
            if not filtered_df.empty:
                narratives = filtered_df[['chinese', 'english']].to_dict(orient='records')
                narratives_str = "\n".join(
                    [f"===中文===\n{n['chinese']}\n===英文===\n {n['english']}\n" for n in narratives])
                return gr.Gallery(label="热词-对应图片信息", value=images, interactive=False, columns=5), gr.Textbox(
                    label="热词叙事", value=narratives_str, lines=5, interactive=False)
    except Exception as e:
        print(f"读取 CSV 文件时发生错误: {e}")

    return gr.Gallery(label="图片", value=images, interactive=False), ""


# 新增函数：获取 logs 目录下时间戳最新的日志文件
def get_latest_log_file(log_dir, start_str="task_"):
    """
    获取最新的日志文件
    :return: 最新的日志文件路径
    """

    if not os.path.exists(log_dir):
        return None
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.log') and f.startswith(start_str)]
    if not log_files:
        return None
    latest_log = max(log_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
    return os.path.join(log_dir, latest_log)


# 更新 Gradio 接口中的日志读取逻辑
def update_task_log_textbox():
    """
    更新日志文本框内容
    :return: 日志内容
    """
    log_dir = "logs"
    start_str = "task_"
    latest_log_file = get_latest_log_file(log_dir, start_str)
    if latest_log_file:
        with open(latest_log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        return log_content
    return "暂无日志文件"


# 更新 Gradio 接口中的日志读取逻辑
def update_agent_log_textbox():
    """
    更新日志文本框内容
    :return: 日志内容
    """
    log_dir = "logs"
    start_str = "agent_"
    latest_log_file = get_latest_log_file(log_dir, start_str)
    if latest_log_file:
        with open(latest_log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        return log_content
    return "暂无日志文件"


def refresh_folders():
    """
    刷新任务文件夹和热词文件夹的选项
    :return: 刷新后的任务文件夹和热词文件夹列表
    """
    task_folders = get_task_folders()
    hotword_folders = []
    if task_folders:
        # 确保 hotword_folders 的初始值在 choices 中
        hotword_folders = get_hotword_folders(task_folders[0])
    return task_folders, hotword_folders


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
        return gr.Dropdown(choices=folders, label="热词文件夹", value=folders[0], interactive=True)
    else:
        return gr.Dropdown(choices=[], label="热词文件夹", value="", interactive=True)


# Gradio 接口
with gr.Blocks(title="GT") as app:
    gr.Markdown("# Google Trends 时下热词 采集、搜索、叙事风格撰写")

    # 使用 Tab 方式组织界面
    with gr.Tab("Cookie 设置"):
        gr.Markdown("### 设置说明")
        gr.Markdown("在 `.env` 文件中配置 `COOKIE_STRING`，以支持采集访问 Google Trends 页面。")
        gr.Markdown("示例：")
        gr.Markdown("```plaintext\nCOOKIE_STRING=\"SID=...; HSID=...; SSID=...\"\n```")

        # 新增输入框和按钮
        cookie_input = gr.Textbox(label="输入 COOKIE_STRING", lines=3)
        save_button = gr.Button("保存并应用")
        status_text = gr.Textbox(label="状态", lines=1, interactive=False)

        # 加载 .env 文件中的 COOKIE_STRING 并回显
        try:

            initial_cookie = os.getenv('COOKIE_STRING', '')
            cookie_input.value = initial_cookie
        except Exception as e:
            status_text.value = f"加载 COOKIE_STRING 失败: {e}"


        # 保存按钮的回调函数
        def save_cookie(cookie_str):
            try:
                # 将新的 COOKIE_STRING 写入 .env 文件，并显式指定编码为 utf-8
                with open(".env", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                with open(".env", "w", encoding="utf-8") as f:
                    for line in lines:
                        if not line.startswith("COOKIE_STRING="):
                            f.write(line)
                    f.write(f"COOKIE_STRING=\"{cookie_str}\"\n")
                return "COOKIE_STRING 已成功保存"
            except Exception as e:
                return f"保存 COOKIE_STRING 失败: {e}"


        save_button.click(fn=save_cookie, inputs=cookie_input, outputs=status_text)

    with gr.Tab("时下热词-采集"):
        gr.Markdown("点击“开始采集”按钮启动采集任务，并显示日志。")
        with gr.Row():
            with gr.Column():
                to_download_image = gr.Checkbox(label="下载Google Trends上的三张图片", value=False, )
                # 修改 origin 和 category 的 choices 属性
                import configparser


                def load_choices():
                    config = configparser.ConfigParser()
                    with open('conf.ini', encoding='utf-8') as config_file:
                        config.read_file(config_file)

                    regions = {k: v for k, v in config['regions'].items()}
                    category_names = {k: v for k, v in config['category_names'].items()}

                    return {
                        'regions': regions,
                        'category_names': category_names
                    }


                choices_data = load_choices()  # 加载 config.ini 中的 Regions 和 category_names
                origin = gr.Dropdown(label="地区", choices=list(choices_data['regions'].keys()), value="美国")
                category = gr.Dropdown(label="分类", choices=list(choices_data['category_names'].keys()),
                                       value="所有分类")
                button = gr.Button("开始采集")
                button.click(fn=run_crawler, inputs=[to_download_image, origin, category],
                             outputs=gr.Textbox(label="采集结果"))
            task_log_textbox = gr.Textbox(label="采集日志", value=update_task_log_textbox, lines=10, max_lines=15,
                                          every=5)

    with gr.Tab("时下热词-深度搜索"):
        gr.Markdown("选择任务记录文件夹以查看热词、图片、以及热词对应的叙事csv文件。")
        with gr.Row():
            task_folders = gr.Dropdown(label="任务记录", multiselect=False, choices=[''] + get_task_folders(),
                                       allow_custom_value=True)

            hot_word_folders = gr.Dropdown(label="热词", multiselect=False,
                                           allow_custom_value=True)
        refresh_button = gr.Button("刷新任务记录")  # 新增刷新按钮
        narratives_textbox = gr.Textbox(label="叙事", value="", lines=5, interactive=False)


        def update_drop_down():
            return gr.Dropdown(label="任务记录", multiselect=False, choices=[''] + get_task_folders(),
                               allow_custom_value=True)


        refresh_button.click(update_drop_down, outputs=task_folders)

        with gr.Row():
            with gr.Column():
                research_button = gr.Button("🤐特定-热词-网络搜索")


                def research_hot_word(hot_words_folders_path):
                    agent_log_file_path = f"agent_{datetime.datetime.now().strftime('%Y年%m月%d日%H时%M分')}.log"

                    agent_logger = get_logger(__name__, agent_log_file_path)

                    ret = hot_word_research_assistant(hot_words_folders_path, agent_logger)
                    return ret


                research_button.click(fn=research_hot_word, inputs=[hot_word_folders],
                                      outputs=gr.Textbox(label=""))
            with gr.Column():
                research_all_keyword_button = gr.Button("🤐全部-热词-网络搜索")


                def research_all_hot_word(task_folders):
                    agent_log_file_path = f"agent_{datetime.datetime.now().strftime('%Y年%m月%d日%H时%M分')}.log"

                    agent_logger = get_logger(__name__, agent_log_file_path)

                    task_dir = os.path.join(task_root_dir, task_folders)
                    # 修改逻辑：只扫描 task_root_dir 下的一层目录
                    hot_words_folders = [os.path.join(task_dir, d) for d in os.listdir(task_dir) if
                                         os.path.isdir(os.path.join(task_dir, d))]

                    result = []
                    for hot_words_folders_path in hot_words_folders:
                        print(f"正在处理热词文件夹：{hot_words_folders_path}")
                        try:
                            ret = hot_word_research_assistant(hot_words_folders_path, agent_logger)
                        except Exception as e:
                            print(f"正在处理热词：{hot_words_folders_path}发生异常，下一个热词")
                            continue
                        sleep(5)
                        result.append(ret)
                    return result


                research_all_keyword_button.click(fn=research_all_hot_word, inputs=[task_folders],
                                                  outputs=gr.Textbox(label=""))
        with gr.Row():

            agent_log_textbox = gr.Textbox(label="AI搜索助手-执行记录", value=update_agent_log_textbox, lines=9,
                                           max_lines=15,
                                           every=5)
            image_gallery = gr.Gallery(label="热词-对应图片信息", value=[], interactive=False, columns=5)

        # 修改回调函数，正确更新 hotword_folders 的选项
        task_folders.change(fn=update_hot_word_folders, inputs=task_folders, outputs=hot_word_folders)
        hot_word_folders.change(fn=get_hot_word_images_and_narratives, inputs=[hot_word_folders],
                                outputs=[image_gallery, narratives_textbox])
        # 修改get_images 增加获取hotword_folders 文件下的csv文件读取csv中hotword列对应的hotword 对应的chinese、english叙事，显示在textbox中
        # image_gallery 显示图片文件名称

    with gr.Tab("口播文案生成"):
        gr.Markdown("""
        流程：选择采集热词任务 >> 查看已完成深度搜索的热词叙事内容 >> 设置口播人设提示词 >> 点击【生成】生成口播文案
        """)
        with gr.Row():
            with gr.Column():
                task_folders = gr.Dropdown(label="选择采集热词任务列表", multiselect=False,
                                           choices=[''] + get_task_folders(),
                                           allow_custom_value=True)
                refresh_button = gr.Button("刷新任务列表")  # 新增刷新按钮


                def update_drop_down():
                    return gr.Dropdown(label="采集热词任务列表", multiselect=False, choices=[''] + get_task_folders(),
                                       allow_custom_value=True)


                refresh_button.click(update_drop_down, outputs=task_folders)

            with gr.Column():
                hot_word_csv_files_path = gr.Dropdown(label="选择热词清单(CSV文件)", choices=[],
                                                      allow_custom_value=False)
                refresh_csv_1_button = gr.Button("刷新热词清单(CSV文件)")


                def get_csv_files(task_folder):
                    if not task_folder:
                        return gr.Dropdown(label="选择热词清单(CSV文件)", choices=[], allow_custom_value=False)
                    task_dir = os.path.join(task_root_dir, task_folder)
                    if not os.path.exists(task_dir):
                        return gr.Dropdown(label="选择热词清单(CSV文件)", choices=[], allow_custom_value=False)
                    csv_files = [''] + [os.path.join(task_dir, f) for f in os.listdir(task_dir) if f.endswith('.csv')]
                    return gr.Dropdown(label="选择热词清单(CSV文件)", value='', choices=csv_files,
                                       allow_custom_value=False)


                task_folders.change(fn=get_csv_files, inputs=task_folders, outputs=hot_word_csv_files_path)
                refresh_csv_1_button.click(fn=get_csv_files, inputs=task_folders, outputs=hot_word_csv_files_path)

        with gr.Row():
            content_textbox = gr.DataFrame(value=None, label="热词叙事内容显示(CSV文件)",
                                           column_widths=[20, 50, 50], max_height=150, max_chars=100)
            selected_row = gr.Dropdown(label="选择叙事内容", choices=[], allow_custom_value=True)


            def read_csv_file(csv_file_path):
                if csv_file_path is None or csv_file_path == '':
                    return gr.DataFrame(value=None, label="热词叙事内容显示(CSV文件)", column_widths=[20, 50, 50],
                                        max_height=150, max_chars=100), gr.Dropdown(
                        label="选择叙事内容", choices=[], allow_custom_value=True)
                csv_path = csv_file_path
                try:
                    df = pd.read_csv(csv_path)
                    # 检查 'hot_word' 列是否存在
                    if 'hot_word' not in df.columns:
                        print(f"CSV 文件中缺少 'hot_word' 列: {csv_path}")
                        return gr.DataFrame(value=None, label="热词叙事内容显示(CSV文件)",
                                            column_widths=[20, 50, 50], max_height=150, max_chars=100), gr.Dropdown(
                            label="选择叙事内容", choices=[], allow_custom_value=True)

                    # 获取 'hot_word' 列的内容
                    combined_choices = []
                    for hw, hwc in zip(df['hot_word'], df['chinese']):
                        if pd.notna(hwc) and hwc != "":  # 判断中文叙事不为空
                            combined_choices.append(f"{hw}/{hwc}")

                    for hw, hwc in zip(df['hot_word'], df['english']):
                        if pd.notna(hwc) and hwc != "":  # 判断英文叙事不为空
                            combined_choices.append(f"{hw}/{hwc}")
                    return gr.DataFrame(df[['hot_word', 'chinese', 'english']], label="热词叙事内容显示(CSV文件)",
                                        column_widths=[20, 50, 50],
                                        max_height=150, max_chars=100), gr.Dropdown(
                        label="选择叙事文案", choices=combined_choices,
                        allow_custom_value=True)
                except Exception as e:
                    print(f"读取 CSV 文件时发生错误: {e}")
                    return "", []


            hot_word_csv_files_path.change(fn=read_csv_file, inputs=[hot_word_csv_files_path],
                                           outputs=[content_textbox, selected_row])

        with gr.Row():
            prompt_textbox1 = gr.Textbox(label="请输入口播人设提示词 1",
                                         value="""- 制作播音文稿，使用专业的新闻播音主持风格\n- 使用英文输出\n- 通过标点符号(-)在任意位置控制停顿""",
                                         lines=3)

            prompt_textbox2 = gr.Textbox(label="请输入口播人设提示词 2", value="""- 制作播音文稿，使用幽默搞笑的相声风格\n- 使用英文输出\n- 通过标点符号(-)在任意位置控制停顿
            """, lines=3)
            prompt_textbox3 = gr.Textbox(label="请输入口播人设提示词 3", value="""- 制作播音文稿，使用愤世嫉俗的批判主义风格\n- 使用英文输出\n- 通过标点符号(-)在任意位置控制停顿
            """, lines=3)

        with gr.Row():

            def process_prompt(selected_row, prompt):
                draft = selected_row.split('/')[1]
                if not draft:
                    return "无法获取 draft"
                return write_in_style(draft, prompt)


            def save_result(result, csv_file_path, selected_row):
                if not result or not csv_file_path or not selected_row:
                    return "参数不完整，无法保存"

                hot_word = selected_row.split("/")[0]  # 提取热词
                temp_file = csv_file_path + ".tmp"  # 使用临时文件避免写入失败导致数据丢失

                try:
                    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        fieldnames = reader.fieldnames

                        # 检查 'result' 字段是否存在
                        has_result_field = 'result' in fieldnames

                        # 构建新的字段列表（如果需要）
                        if not has_result_field:
                            fieldnames.append('result')

                        with open(temp_file, mode='w', newline='', encoding='utf-8') as tmpfile:
                            writer = csv.DictWriter(tmpfile, fieldnames=fieldnames)
                            writer.writeheader()

                            for row in reader:
                                if row['hot_word'] == hot_word:
                                    # 如果有旧的 result，拼接新内容；否则直接写入
                                    old_result = row.get('result', '')
                                    if old_result:
                                        row['result'] = f"{old_result}\n---\n{result}"
                                    else:
                                        row['result'] = result
                                writer.writerow(row)

                    # 替换原文件
                    os.replace(temp_file, csv_file_path)
                    return "✅ 保存成功"
                except Exception as e:
                    print(f"保存失败: {e}")
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    return f"❌ 保存失败: {str(e)}"


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


            def write_in_style(draft, prompt):
                agent_log_file_path = f"agent_{datetime.datetime.now().strftime('%Y年%m月%d日%H时%M分')}.log"
                agent_logger = get_logger(__name__, agent_log_file_path)
                try:
                    ret = write_in_style_assistant(draft, prompt, agent_logger)
                    return ret
                except Exception as e:
                    print(f"处理热词时发生错误: {e}")
                    return f"处理热词时发生错误: {e}"

    with gr.Tab("口播音频生成"):

        with gr.Row():
            with gr.Column():
                task_folders = gr.Dropdown(label="选择采集热词任务列表", multiselect=False,
                                           choices=[''] + get_task_folders(),
                                           allow_custom_value=True)
                refresh_button = gr.Button("刷新任务列表")  # 新增刷新按钮


                def update_drop_down():
                    return gr.Dropdown(label="采集热词任务列表", multiselect=False, choices=[''] + get_task_folders(),
                                       allow_custom_value=True)


                refresh_button.click(update_drop_down, outputs=task_folders)

            with gr.Column():
                hot_word_csv_files_path = gr.Dropdown(label="选择热词清单(CSV文件)", choices=[],
                                                      allow_custom_value=False)
                refresh_csv_1_button = gr.Button("刷新热词清单(CSV文件)")


                def get_csv_files(task_folder):
                    if not task_folder:
                        return gr.Dropdown(label="选择热词清单(CSV文件)", choices=[], allow_custom_value=False)
                    task_dir = os.path.join(task_root_dir, task_folder)
                    if not os.path.exists(task_dir):
                        return gr.Dropdown(label="选择热词清单(CSV文件)", choices=[], allow_custom_value=False)
                    csv_files = [''] + [os.path.join(task_dir, f) for f in os.listdir(task_dir) if f.endswith('.csv')]
                    return gr.Dropdown(label="选择热词清单(CSV文件)", value='', choices=csv_files,
                                       allow_custom_value=False)


                task_folders.change(fn=get_csv_files, inputs=task_folders, outputs=hot_word_csv_files_path)
                refresh_csv_1_button.click(fn=get_csv_files, inputs=task_folders, outputs=hot_word_csv_files_path)

        with gr.Row():
            content_textbox = gr.DataFrame(value=None, label="热词口播文案显示(CSV文件)",
                                           column_widths=[20, 50, 50, 50], max_height=150, max_chars=100)
            selected_row_tmp = gr.Dropdown(label="选择口播文案", choices=[], allow_custom_value=True)


            def read_result_csv_file(csv_file_path):
                if csv_file_path is None or csv_file_path == '':
                    return gr.DataFrame(value=None, label="热词口播文案显示(CSV文件)", column_widths=[20, 50],
                                        max_height=150, max_chars=100), gr.Dropdown(
                        label="选择口播文案", choices=[],
                        allow_custom_value=True)
                csv_path = csv_file_path
                try:
                    df = pd.read_csv(csv_path)
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
                        results_list = hwc.split('---')
                        for idx, result_item in enumerate(results_list):
                            combined_choices.append(f"{hw}/[{idx}]/{result_item.strip()}")
                    return gr.DataFrame(df[['hot_word', 'result']], label="热词口播文案显示(CSV文件)",
                                        column_widths=[20, 150],
                                        max_height=150, max_chars=200), gr.Dropdown(
                        label="选择口播文案", choices=combined_choices,
                        allow_custom_value=True)
                except Exception as e:
                    print(f"读取 CSV 文件时发生错误: {e}")
                    return "", []


            warnings.filterwarnings("ignore", category=FutureWarning)
            warnings.filterwarnings("ignore", category=UserWarning)
            sys.path.append(current_dir)
            sys.path.append(os.path.join(current_dir, 'index-tts', "indextts"))
            from indextts.infer import IndexTTS
            from tools.i18n.i18n import I18nAuto

            i18n = I18nAuto(language="zh_CN")
            tts = IndexTTS(model_dir="index-tts/checkpoints", cfg_path="index-tts/checkpoints/config.yaml",
                           device="cuda:0",
                           use_cuda_kernel=True)

            os.makedirs(os.path.join(task_root_dir,"tts/tmp"), exist_ok=True)


            def parse_speakers_and_texts(selected_row_tmp_value):

                parts = selected_row_tmp_value.split("/")
                if len(parts) < 3:
                    return []

                content = "/".join(parts[2:])  # 获取实际文本部分，防止热词或序号中包含 '/'

                if '\n' not in content.strip().strip('\n'):
                    speaker, text = content.strip().strip('\n').split(':', 1)

                    return [{"speaker": speaker.strip(), "text": text.strip()}]

                lines = content.strip().split('\n')

                result = []
                for line in lines:
                    if '：' in line:
                        speaker, text = line.split('：', 1)
                        result.append({"speaker": speaker.strip(), "text": text.strip()})

                return result


            hot_word_csv_files_path.change(fn=read_result_csv_file, inputs=[hot_word_csv_files_path],
                                           outputs=[content_textbox, selected_row_tmp])

        synthesize_button = gr.Button("开始合成语音", variant="primary")


        @gr.render(inputs=selected_row_tmp)
        def render_audio_inputs(selected_row_tmp_value):
            if not selected_row_tmp_value:
                return

            speaker_text_list = parse_speakers_and_texts(selected_row_tmp_value)
            speaker_list = []
            for item in speaker_text_list:
                speaker = item["speaker"]
                if speaker not in speaker_list:
                    speaker_list.append(speaker)
            speaker_audio_list = []
            with gr.Row():

                for speaker in speaker_list:
                    speaker_audio = gr.Audio(label=f"请上传 {speaker} 的参考音频", sources=["upload", "microphone"],
                                             type="filepath")
                    speaker_audio_list.append(speaker_audio)

            with gr.Column():
                for idx, item in enumerate(speaker_text_list):
                    speaker = item["speaker"]
                    text = item["text"]
                    gr.Textbox(label=f"{speaker} 的台词[{idx}]", value=text, interactive=False)

            output_audio = gr.Audio(label="生成结果", visible=True)

            from pydub import AudioSegment

            def synthesize_multiple_voices(*speaker_au_list):
                print(speaker_au_list)
                output_files = []
                progress = gr.Progress()
                progress(0, desc="开始生成语音")
                text_length = len(speaker_text_list)
                for i, audio_item in enumerate(speaker_text_list, start=1):
                    progress(i / text_length * 0.1, f"开始生成第{i}段文本的语音")
                    speaker_name = audio_item["speaker"]
                    speaker_audio_path = speaker_audio_list[speaker_list.index(speaker_name)].value['path']
                    content = audio_item["text"]
                    if not speaker_audio_path or not content:
                        return None
                    output_path = os.path.join(task_root_dir,"tts/tmp", f"{i}_{speaker_name}_{int(time.time())}.wav")
                    progress(i / text_length * 0.8, f"第{i}段文本的语音生成成功")
                    tts.infer_fast(speaker_audio_path, content, output_path)
                    output_files.append(output_path)
                progress(0.9, "开始拼接语音")
                combined_audio = AudioSegment.empty()
                for file in output_files:
                    segment = AudioSegment.from_wav(file)
                    combined_audio += segment

                hot_word = selected_row_tmp_value.split("/")[0]
                hot_word_index = selected_row_tmp_value.split("/")[1]
                task_path = os.path.join(task_root_dir,"tts", os.path.basename(task_folders.value))

                os.makedirs(task_path, exist_ok=True)
                # 保存最终拼接文件
                final_output_path = os.path.join(task_path, f"{hot_word}_{hot_word_index}_{int(time.time())}.wav")
                combined_audio.export(final_output_path, format="wav")

                progress(1, f"语音拼接完成")
                # 清空零时文件夹
                tmp_folder = os.path.join(task_root_dir,"tts/tmp")
                if os.path.exists(tmp_folder):
                    for file in os.listdir(tmp_folder):
                        file_path = os.path.join(tmp_folder, file)
                        try:
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                        except Exception as e:
                            print(f"删除 {file_path} 失败: {e}")
                else:
                    os.makedirs(tmp_folder, exist_ok=True)

                return final_output_path

            synthesize_button.click(
                synthesize_multiple_voices,
                inputs=speaker_audio_list,  # 所有动态生成的 Audio + Textbox
                outputs=output_audio
            )

    with gr.Tab("下载"):
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


            def refresh_zip_files():
                """
                刷新 .zip 文件列表
                :return: 返回最新的 .zip 文件列表
                """
                zip_dir = os.getenv("ZIP_DIR", "zips")
                zip_path = os.path.join(current_dir, zip_dir)
                if not os.path.exists(zip_path):
                    os.makedirs(zip_path, exist_ok=True)
                return [os.path.join(zip_path, f) for f in os.listdir(zip_path) if f.endswith('.zip')]


            download_output = gr.File(label="ZIP下载链接",
                                      value=refresh_zip_files,
                                      height=100,
                                      every=10)
        download_button = gr.Button("ZIP压缩")


        def zip_folder(folder_path, zip_path):
            """
            将文件夹打包为 .zip 文件
            :param folder_path: 文件夹路径
            :param zip_path: .zip 文件路径
            """
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.isfile(folder_path):
                    # 如果 folder_path 是文件，则直接添加到 ZIP 文件中
                    file_name = os.path.basename(folder_path)
                    zipf.write(folder_path, file_name)
                elif os.path.isdir(folder_path):
                    # 如果 folder_path 是文件夹，则遍历文件夹并添加文件
                    for root, dirs, files in os.walk(folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            cname = os.path.relpath(str(file_path), str(folder_path))
                            zipf.write(str(file_path), cname)
                else:
                    raise ValueError(f"路径 {folder_path} 既不是文件也不是文件夹")


        def download_folder(folder_paths):
            """
            将选中的文件夹打包为 .zip 文件并提供下载链接
            :param folder_paths: 选中的文件夹路径列表
            :return: .zip 文件路径
            """
            if not folder_paths:
                return None  # 用户未选择任何文件夹

            # 只处理第一个选中的文件夹
            folder_path = folder_paths[0]

            # 读取环境变量指定的目录
            zip_dir = os.getenv("ZIP_DIR")
            zip_path = os.path.join(current_dir, zip_dir, f"{os.path.basename(folder_path)}.zip")
            os.makedirs(os.path.dirname(zip_path), exist_ok=True)
            zip_folder(folder_path, zip_path)
            return zip_path


        download_button.click(
            fn=download_folder,  # 调用下载函数
            inputs=file_explorer,  # 获取选中的文件夹路径
            outputs=download_output  # 提供下载链接
        )

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=7864, help='Gradio 应用监听的端口号')
    args = parser.parse_args()
    app.queue(20)
    if os.getenv('PLATFORM', '') == 'local':
        app.launch(share=False,
                   allowed_paths=[os.getenv('ROOT', ''), os.getenv('ZIP_DIR', ''),"tts", os.getenv('TASK_DIR', ''), "tmp",
                                  os.path.join(os.getcwd(), 'Log')],
                   server_port=args.port, favicon_path="favicon.ico")
    elif os.getenv('PLATFORM', '') == 'server':
        app.launch(share=False, server_name="0.0.0.0",
                   allowed_paths=[os.getenv('ROOT', ''), os.getenv('ZIP_DIR', ''),"tts", os.getenv('TASK_DIR', ''), "tmp",
                                  os.path.join(os.getcwd(), 'Log')],
                   server_port=args.port, favicon_path="favicon.ico")
