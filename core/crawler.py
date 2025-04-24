import asyncio
from dotenv import load_dotenv
import os
from .image_utils import ImageUtils

# 加载.env文件中的环境变量
load_dotenv()
current_path = os.path.dirname(os.path.abspath(__file__))
__all__ = ['crawl_google_trends_page']


async def crawl_google_trends_page(page, logging, url="", task_dir=None, to_download_image=False):
    """
    爬取 Google Trends 页面内容
    :param to_download_image:
    :param url: 目标 URL
    :param page: Playwright 页面对象
    :param logging: 日志记录器对象
    :param task_dir: 任务文件夹路径
    """
    if url != "":
        url = url

    # 打开页面
    if not page.is_closed():
        await page.goto(url)
        logging.info('页面加载完成')
    else:
        logging.error("页面已关闭，无法导航")
        return

    # 第一次加载图片
    try:
        hot_key = await page.query_selector_all(
            'tbody:nth-child(3) > tr:nth-child(n) > td.enOdEe-wZVHld-aOtOmf.jvkLtd > div.mZ3RIc')
    except Exception as e:
        logging.error(f'未找到 div 元素: {e}')

    for i, div in enumerate(hot_key):
        text_content = await div.text_content()
        logging.debug(f'div {i + 1} 的文本内容: {text_content}')
        if to_download_image:
            try:
                await div.click()
                await asyncio.sleep(5)
                logging.debug(f'点击了 div {i + 1}')
            except Exception as e:
                logging.error(f'点击 div {i + 1} 时出错: {e}')

            # 获取指定路径下的图片的 src 地址
            img_selector = 'div.EMz5P > div.k44Spe > div:nth-child(4) > div > div.jDtQ5 > div:nth-child(n) > a > div.yYagic > img'
            img_src_list = await page.query_selector_all(img_selector)
            logging.info(f"关键词{text_content}：图片数量：{len(img_src_list)}")
            if len(img_src_list) < 3:
                logging.warning(f"关键词{text_content}：图片数量不足3张，请注意")

            for index, img in enumerate(img_src_list):
                if img:
                    src = await img.get_attribute('src')
                    logging.debug(f'图片 {i + 1} 的 src 地址: {src}')
                    image_util = ImageUtils(os.getenv("PROXY_URL"))
                    await image_util.download_and_resize_image(
                        logging,
                        img_url=src,
                        task_dir=os.path.join(task_dir, text_content),  # 保存在任务文件夹中
                        image_name=f"{text_content}_{index}.jpg"
                    )
                else:
                    logging.error(f'未找到图片元素在 div {i + 1} 中')
        else:
            os.makedirs(os.path.join(task_dir, text_content), exist_ok=True)

        await asyncio.sleep(5)
