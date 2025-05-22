import asyncio
import csv
from dotenv import load_dotenv
import os
from .image_utils import ImageUtils

# 加载.env文件中的环境变量
load_dotenv()
current_path = os.path.dirname(os.path.abspath(__file__))
__all__ = ['crawl_google_trends_page']


async def query_selector_with_retry(page, logging, selector, max_retries=3, delay=2):
    """
    带重试机制的 query_selector_all 封装
    :param page: Playwright 页面对象
    :param selector: CSS 选择器
    :param max_retries: 最大重试次数
    :param delay: 每次重试间隔时间（秒）
    :return: 元素列表或空列表
    """
    for attempt in range(max_retries):
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                logging.debug(f"成功找到元素：{selector}")
                return elements
            else:
                logging.warning(f"第 {attempt + 1} 次尝试未找到元素：{selector}")
        except Exception as e:
            logging.error(f"查询 {selector} 出错: {e}")

        if attempt < max_retries - 1:
            logging.info(f"等待 {delay} 秒后重试...")
            await asyncio.sleep(delay)

    logging.error(f"经过 {max_retries} 次尝试仍未找到元素：{selector}")
    return []


async def crawl_google_trends_page(page, logging, origin="", category=0, url="", task_dir=None,
                                   to_download_image=False, nums=25):
    """
    爬取 Google Trends 页面内容
    :param category:
    :param origin:
    :param to_download_image:
    :param url: 目标 URL
    :param page: Playwright 页面对象
    :param logging: 日志记录器对象
    :param task_dir: 任务文件夹路径
    """
    global hot_words
    if url != "":
        url = url
    if origin != "":
        url += f"?geo={origin}"
    if category != 0:
        url += f"&category={category}"

    # 打开页面
    if not page.is_closed():
        await page.goto(url)
        logging.info(f'页面加载完成：{url}')
    else:
        logging.error("页面已关闭，无法导航")
        return
    await query_selector_with_retry(page, logging, 'div.VfPpkd-dgl2Hf-ppHlrf-sM5MNb > div', max_retries=3, delay=2)

    # 第一次加载图片
    try:
        elements = await query_selector_with_retry(page, logging,
                                                   'tbody:nth-child(3) > tr:nth-child(n)')
        elements_temp = elements[:nums]  # ✅ 在 await 后进行切片

    except Exception as e:
        logging.error(f'未找到 div 元素: {e}')
        elements_temp = []  # ✅ 添加默认空列表防止后续引用错误

    for i, div in enumerate(elements_temp):
        hot_words_elements = await query_selector_with_retry(div, logging,
                                                             'td.enOdEe-wZVHld-aOtOmf.jvkLtd > div.mZ3RIc',
                                                             max_retries=3, delay=2)

        search_volume_element = await query_selector_with_retry(div, logging,
                                                                'td.enOdEe-wZVHld-aOtOmf.dQOTjf > div > div.lqv0Cb',
                                                                max_retries=3, delay=2)

        search_growth_rate_element = await query_selector_with_retry(div, logging,
                                                                     'td.enOdEe-wZVHld-aOtOmf.dQOTjf > div > div.wqrjjc > div',
                                                                     max_retries=3, delay=2)

        search_active_time_element = await query_selector_with_retry(div, logging,
                                                                     'td.enOdEe-wZVHld-aOtOmf.WirRge > div.vdw3Ld',
                                                                     max_retries=3, delay=2)
        if hot_words_elements:
            hot_word_element = hot_words_elements[0]  # 取第一个元素
            search_volume = await search_volume_element[0].text_content()
            search_growth_rate = await search_growth_rate_element[0].text_content()
            search_active_time = await  search_active_time_element[0].text_content()
            text_content = await hot_word_element.text_content()
        else:
            logging.warning("未找到关键词元素，使用默认名称代替")
            continue
        logging.info(f'div {i + 1} 的文本内容: {text_content}')

        try:
            await hot_word_element.click()
            await asyncio.sleep(5)
            logging.debug(f'点击了 div {i + 1}')
        except Exception as e:
            logging.error(f'点击 div {i + 1} 时出错: {e}')
        # 查看关联新闻
        new_titles_selector = 'div.jDtQ5 > div:nth-child(n) > a > div.MEJ15 > div.QbLC8c'
        new_titles = await query_selector_with_retry(page, logging, new_titles_selector)
        title_new = []
        for index, title in enumerate(new_titles):
            title_text = await title.text_content()
            logging.info(f"关键词{text_content}：第{index + 1}个标题：{title_text}")
            title_new.append(title_text)

        if to_download_image:
            # 获取指定路径下的图片的 src 地址
            img_selector = 'div.jDtQ5 > div:nth-child(n) > a > div.yYagic > img'
            img_src_list = await query_selector_with_retry(page, logging, img_selector)
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
                        task_dir=os.path.join(task_dir, text_content, "new_images"),  # 保存在任务文件夹中
                        image_name=f"{text_content}_{index}.jpg"
                    )
                else:
                    logging.error(f'未找到图片元素在 div {i + 1} 中')
        else:
            os.makedirs(os.path.join(task_dir, text_content), exist_ok=True)
            logging.info(f"保存关键词：{text_content}成功")

        # 将 text_content 写入 CSV 文件
        csv_file_path = os.path.join(task_dir, os.getenv("HOT_WORDS_FILE_NAME"))
        file_exists = os.path.isfile(csv_file_path)
        with open(csv_file_path, 'a', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['hot_word',
                          'search_volume',
                          'search_growth_rate',
                          "search_active_time",
                          "relation_news",
                          "search_history",
                          "highlights",
                          "chinese",
                          "output", ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(
                {'hot_word': text_content,
                 'search_volume': search_volume,
                 'search_growth_rate': search_growth_rate,
                 "search_active_time": search_active_time,
                 "relation_news": '---'.join(title_new),
                 "search_history": '',
                 "chinese": '',
                 "output": '',
                 "highlights": "",
                 })
            logging.info(
                f"关键词 {text_content} ,搜索量：{search_volume}，搜索增长率：{search_growth_rate}，搜索活跃时间：{search_active_time}")
            logging.info(f"关键词 {text_content} 已存储至 CSV 文件")

            await asyncio.sleep(5)
    logging.info(f"地区编码：{origin}，分类编码：{category}，采集任务已完成，共采集了{len(hot_words_elements)}个关键词")
