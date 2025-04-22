import argparse
import asyncio
import logging
import os
import datetime
import zipfile

from dotenv import load_dotenv

from core import init_browser, close_browser, setup_logger
from core import crawl_google_trends_page
import gradio as gr

# 动态生成日志文件路径
task_date = datetime.datetime.now().strftime("%Y年%m月%d日%H时%M分")
log_file_path = os.path.join("logs", f"{task_date}.log")
os.makedirs("logs", exist_ok=True)
load_dotenv()
task_dir = os.getenv("TASK_DIR", "tasks")
current_dir = os.path.dirname(os.path.abspath(__file__))
# # 配置日志
# logger = logging.getLogger()
# logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


async def start_crawler(url):
    """
    启动采集任务
    :param url: 目标URL
    """
    # 获取当前时间并创建任务文件夹
    task_dir_now = os.path.join(task_dir, task_date)
    os.makedirs(task_dir, exist_ok=True)

    logger = setup_logger(log_file_path)

    p, browser, context, page = await init_browser(logger)

    await crawl_google_trends_page(page, logger, url=url, task_dir=task_dir_now)

    # 关闭页面和上下文
    await page.close()
    await context.close()

    # 关闭浏览器
    await close_browser(p, browser, logger)


# 新增 Gradio Web 页面
def run_crawler():
    """
    运行采集任务
    :return: 爬取任务完成的消息
    """
    url = "https://trends.google.com/trending?geo=US&hours=168&sort=search-volume"
    asyncio.run(start_crawler(url))
    return "爬取任务已完成"


def get_task_folders():
    """
    获取任务文件夹列表
    :return: 任务文件夹列表
    """
    # task_dir = task_dir
    if not os.path.exists(task_dir):
        return []
    folders = os.listdir(task_dir)
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

    hotword_dir = os.path.join(task_dir, task_folder)
    if not os.path.exists(hotword_dir):
        return []
    folders = os.listdir(hotword_dir)
    return folders


def get_images(task_folder, hotword_folder):
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

    image_dir = os.path.join(task_dir, task_folder, hotword_folder)
    if not os.path.exists(image_dir):
        return []
    images = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith(('.jpg', '.png'))]
    return gr.Gallery(label="图片", value=images, interactive=False)


# 新增函数：获取 logs 目录下时间戳最新的日志文件
def get_latest_log_file():
    """
    获取最新的日志文件
    :return: 最新的日志文件路径
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        return None
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
    if not log_files:
        return None
    latest_log = max(log_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
    return os.path.join(log_dir, latest_log)


# 更新 Gradio 接口中的日志读取逻辑
def update_log_textbox():
    """
    更新日志文本框内容
    :return: 日志内容
    """
    latest_log_file = get_latest_log_file()
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
def update_hotword_folders(task_folder):
    if isinstance(task_folder, list) and task_folder:
        task_folder = task_folder[0]
    elif not isinstance(task_folder, str):
        return []
    hotword_dir = os.path.join(task_dir, task_folder)
    if not os.path.exists(hotword_dir):
        return []
    folders = os.listdir(hotword_dir)
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

    with gr.Tab("执行及日志显示"):
        gr.Markdown("### 执行与日志")
        gr.Markdown("点击“开始爬取”按钮启动任务，日志将实时更新。")
        with gr.Row():
            with gr.Column():
                button = gr.Button("开始爬取")
                button.click(fn=run_crawler, inputs=None, outputs=gr.Textbox(label="爬取结果"))
                log_textbox = gr.Textbox(label="日志", value=update_log_textbox, lines=10, interactive=False)

    with gr.Tab("任务与图片"):
        gr.Markdown("### 任务与图片")
        gr.Markdown("选择任务文件夹以查看热词文件夹及对应图片。")
        with gr.Row():
            with gr.Column():
                task_folders = gr.Dropdown(label="任务文件夹", multiselect=False, choices=get_task_folders(),
                                           allow_custom_value=True)
                hotword_folders = gr.Dropdown(label="热词文件夹", multiselect=False, choices=[],
                                              allow_custom_value=True)
                refresh_button = gr.Button("刷新任务文件夹")  # 新增刷新按钮


                def update_drop_down():
                    return gr.Dropdown(label="任务文件夹", multiselect=False, choices=get_task_folders(),
                                       allow_custom_value=True)


                refresh_button.click(update_drop_down, outputs=task_folders)

            with gr.Column():
                image_gallery = gr.Gallery(label="图片", value=[], interactive=False, columns=4)

        # 修改回调函数，正确更新 hotword_folders 的选项
        task_folders.change(fn=update_hotword_folders, inputs=task_folders, outputs=hotword_folders)
        hotword_folders.change(fn=get_images, inputs=[task_folders, hotword_folders], outputs=image_gallery)
    with gr.Tab("下载"):
        gr.Markdown("### 查看历史记录\n支持单个文件夹或多个文件压缩后下载。")
        with gr.Row():
            with gr.Column():
                file_explorer = gr.FileExplorer(
                    label="任务文件夹",
                    glob="**/*",
                    root_dir=task_dir,
                    every=1,
                    height=300,
                )
                refresh_btn = gr.Button("刷新")


                def update_file_explorer():
                    return gr.FileExplorer(root_dir="")


                def update_file_explorer_2():
                    return gr.FileExplorer(root_dir=task_dir)


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
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        cname = os.path.relpath(str(file_path), str(folder_path))
                        zipf.write(str(file_path), cname)


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
            if not os.path.isdir(folder_path):
                return None

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
    parser.add_argument('--port', type=int, default=7862, help='Gradio 应用监听的端口号')
    args = parser.parse_args()
    if os.getenv('PLATFORM', '') == 'local':
        app.launch(share=False,
                   allowed_paths=[os.getenv('ROOT', ''), os.getenv('ZIP_DIR', ''), os.path.join(os.getcwd(), 'Log')],
                   server_port=args.port,favicon_path="favicon.ico")
    elif os.getenv('PLATFORM', '') == 'server':
        app.launch(share=False, server_name="0.0.0.0",
                   allowed_paths=[os.getenv('ROOT', ''), os.getenv('ZIP_DIR', ''), os.path.join(os.getcwd(), 'Log')],
                   server_port=args.port,favicon_path="favicon.ico")
