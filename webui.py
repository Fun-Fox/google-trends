import argparse
import os
import datetime
import zipfile
from asyncio import sleep

from dotenv import load_dotenv

from agent.main import write_style_assistant
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
    task_dir_file_name = os.path.join(task_root_dir, task_date+f'_{origin}_{category}')
    os.makedirs(task_root_dir, exist_ok=True)

    logger = get_logger(__name__, task_log_file_path)

    p, browser, context, page = await init_browser(logger)

    choices = load_choices()
    origin_code = choices['regions'].get(origin, "US")  # 默认值为 "US"
    category_code = int(choices['category_names'].get(category, "0"))  # 默认值为 "0"

    await crawl_google_trends_page(page, logger, origin=origin_code, category=category_code, url=url, task_dir=task_dir_file_name,
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


def get_images(hotword_folder):
    """
    获取图片列表
    :param task_folders:
    :param hotword_folder: 热词文件夹名称
    :return: 图片列表
    """
    # 确保 hotword_folder 是字符串类型
    if isinstance(hotword_folder, list) and hotword_folder:
        hotword_folder = hotword_folder[0]
    elif not isinstance(hotword_folder, str):
        return []

    image_dir = hotword_folder
    if not os.path.exists(hotword_folder):
        return []
    images = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith(('.jpg', '.png'))]
    return gr.Gallery(label="图片", value=images, interactive=False)


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
    gr.Markdown("# Google Trends 采集")

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

    with gr.Tab("热词采集"):
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

                    regions = { k:v for k, v in config['regions'].items()}
                    category_names = {k:v for k, v in config['category_names'].items()}

                    return {
                        'regions': regions,
                        'category_names': category_names
                    }

                choices_data = load_choices()  # 加载 config.ini 中的 Regions 和 category_names
                origin = gr.Dropdown(label="地区", choices=list(choices_data['regions'].keys()), value="美国")
                category = gr.Dropdown(label="分类", choices=list(choices_data['category_names'].keys()), value="所有分类")
                button = gr.Button("开始采集")
                button.click(fn=run_crawler, inputs=[to_download_image, origin, category],
                             outputs=gr.Textbox(label="采集结果"))
            task_log_textbox = gr.Textbox(label="采集日志", value=update_task_log_textbox, lines=10, max_lines=15,
                                          every=5)

    with gr.Tab("热词深度搜索"):
        gr.Markdown("选择任务记录文件夹以查看热词、图片、以及热词对应的叙事csv文件。")
        with gr.Row():
            task_folders = gr.Dropdown(label="任务记录", multiselect=False, choices=[''] + get_task_folders(),
                                       allow_custom_value=True)

            hotword_folders = gr.Dropdown(label="热词", multiselect=False,
                                          allow_custom_value=True)
        refresh_button = gr.Button("刷新任务记录")  # 新增刷新按钮


        def update_drop_down():
            return gr.Dropdown(label="任务记录", multiselect=False, choices=[''] +get_task_folders(),
                               allow_custom_value=True)


        refresh_button.click(update_drop_down, outputs=task_folders)
        with gr.Row():
            with gr.Column():
                research_button = gr.Button("🤐特定-热词-网络搜索")
                def research_hot_word(hot_words_folders_path):
                    agent_log_file_path = f"agent_{datetime.datetime.now().strftime('%Y年%m月%d日%H时%M分')}.log"

                    agent_logger = get_logger(__name__, agent_log_file_path)

                    ret = write_style_assistant(hot_words_folders_path, agent_logger)

                    return ret
                research_button.click(fn=research_hot_word, inputs=[hotword_folders],
                                      outputs=gr.Textbox(label=""))

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
                            ret = write_style_assistant(hot_words_folders_path, agent_logger)
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
                                           every=5)
            image_gallery = gr.Gallery(label="热词-对应图片信息", value=[], interactive=False, columns=5)

        # 修改回调函数，正确更新 hotword_folders 的选项
        task_folders.change(fn=update_hot_word_folders, inputs=task_folders, outputs=hotword_folders)
        hotword_folders.change(fn=get_images, inputs=[hotword_folders], outputs=image_gallery)
    # with gr.Tab("人设及口播（未完成）"):
    #     gr.Markdown("选择任务记录文查看热词对应的叙事")
    #     with gr.Row():
    #         task_folders = gr.Dropdown(label="任务记录", multiselect=False, choices=[''] + get_task_folders(),
    #                                    allow_custom_value=True)
    #         refresh_button = gr.Button("刷新任务记录")  # 新增刷新按钮
    #
    #
    #         def update_drop_down():
    #             return gr.Dropdown(label="任务记录", multiselect=False, choices=[''] + get_task_folders(),
    #                                allow_custom_value=True)
    #
    #
    #         refresh_button.click(update_drop_down, outputs=task_folders)
    #     # 1.显示文件夹下的csv文件内容，并且可以支持选择指定行。
    #     # 2.设置多个提示词文本，支持每个提示词的结果试跑
    #     # 3.生成的文本转



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
    if os.getenv('PLATFORM', '') == 'local':
        app.launch(share=False,
                   allowed_paths=[os.getenv('ROOT', ''), os.getenv('ZIP_DIR', ''), os.getenv('TASK_DIR', ''), "tmp",
                                  os.path.join(os.getcwd(), 'Log')],
                   server_port=args.port, favicon_path="favicon.ico")
    elif os.getenv('PLATFORM', '') == 'server':
        app.launch(share=False, server_name="0.0.0.0",
                   allowed_paths=[os.getenv('ROOT', ''), os.getenv('ZIP_DIR', ''), os.getenv('TASK_DIR', ''), "tmp",
                                  os.path.join(os.getcwd(), 'Log')],
                   server_port=args.port, favicon_path="favicon.ico")
