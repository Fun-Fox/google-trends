# 新增 Gradio Web 页面
import datetime
import os

from dotenv import load_dotenv

from core import get_logger, init_browser, crawl_google_trends_page, close_browser
from webui.utils.conf import load_regions_choices
from webui.utils.constant import task_root_dir, root_dir

load_dotenv()

async def run_crawler(to_download_image, origin, category, nums=25):
    """
    运行采集任务
    :return: 爬取任务完成的消息
    """
    url = "https://trends.google.com/trending"

    await start_crawler(url, to_download_image, origin=origin, category=category, nums=nums)
    return "热点采集任务已完成"


async def start_crawler(url, to_download_image, origin="", category="", nums=25):
    """
    启动采集任务
    :param to_download_image:
    :type origin: string
    :param category:
    :param url: 目标URL
    """
    task_date = datetime.datetime.now().strftime("%Y年%m月%d日%H时%M分")
    task_log_file_path = os.path.join(f"task_{task_date}.log")
    os.makedirs(os.path.join(root_dir, "logs"), exist_ok=True)
    # 获取当前时间并创建任务文件夹
    task_dir_file_name = os.path.join(task_root_dir, task_date + f'_{origin}_{category}')
    os.makedirs(task_root_dir, exist_ok=True)

    logger = get_logger(__name__, task_log_file_path)

    p, browser, context, page = await init_browser(logger)

    choices = load_regions_choices()
    origin_code = choices['regions'].get(origin, "US")  # 默认值为 "US"
    category_code = int(choices['category_names'].get(category, "0"))  # 默认值为 "0"

    await crawl_google_trends_page(page, logger, origin=origin_code, category=category_code, url=url,
                                   task_dir=task_dir_file_name,
                                   to_download_image=to_download_image, nums=nums)

    # 关闭页面和上下文
    await page.close()
    await context.close()

    # 关闭浏览器
    await close_browser(p, browser, logger)