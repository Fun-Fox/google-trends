import datetime
import os
import random
from typing import Dict
from agent.utils import call_llm


def generate_news_summary_report(highlights: str, output: str, hot_word_path: str, logger,
                                 language: str = "中文") -> Dict:
    """
    这是一个由AI驱动的虚拟新闻报道师，能够基于事件说明和优质报道内容，
    自动生成结构清晰的 Markdown 新闻总结报告，并插入相关图片。

    参数:
        highlights (str): 精选的优质报道内容
        output (str): 事件说明或背景介绍
        hot_word_path (str): 用于保存报告和读取图片的路径
        logger (Logger): 日志记录器
        language (str): 输出语言，默认为中文

    返回:
        dict: 包含执行结果状态、文件路径和消息的字典
    """

    # Step 1: 校验输入
    if not all([highlights, output, hot_word_path]):
        logger.error("缺少必要参数，请检查输入")
        return {"action": "error", "reason": "缺少必要参数"}

    # Step 2: 构建 Prompt 并调用 LLM
    prompt = _build_prompt(output, highlights, language)
    response, success = call_llm(prompt, logger=logger)

    if not success:
        logger.error("LLM 响应失败，请检查你的响应格式。")
        return {"action": "finish", "reason": "LLM 响应失败"}

    # Step 3: 插入随机图片
    try:
        response_with_image = _insert_random_image(response, hot_word_path)
    except Exception as e:
        logger.warning(f"插入图片时发生异常：{e}")
        response_with_image = response

    # Step 4: 写入 Markdown 文件
    try:
        md_file_path = _write_to_markdown_file(response_with_image, hot_word_path)
    except Exception as e:
        logger.error(f"写入 Markdown 文件失败：{e}")
        return {"action": "error", "reason": str(e)}

    logger.info(f"Markdown 报告已成功写入：{md_file_path}")

    return {
        "action": "success",
        "file_path": md_file_path,
        "message": "内容总结并保存成功"
    }


# ----------------------------
# 私有方法区（Private Helpers）
# ----------------------------

def _build_prompt(output: str, highlights: str, language: str) -> str:
    """构建 LLM 所需的 Prompt"""
    return f"""
你是一个专业的新闻分析师，请根据以下信息进行总结。

事件说明:
{output}

优质报道:
{highlights}

请使用{language}输出一个结构清晰的 Markdown 总结报告，包括：
- 事件概要（简明扼要地概括事件）
- 关键点分析（列出3~5个核心要点）
- 影响与趋势（分析该事件可能带来的影响或趋势）
- 引用一些优质报道证明观点

格式要求：
- 使用 Markdown 语法
- 不包含任何解释性语句，只输出内容本身
- 只允许一个一级标题
"""


def _insert_random_image(markdown_content: str, image_dir: str) -> str:
    """在一级标题后插入一张随机图片"""
    lines = markdown_content.strip().split('\n')
    if not lines or not lines[0].startswith('#'):
        return markdown_content

    title_line = lines[0]
    rest_lines = '\n'.join(lines[1:])

    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        return markdown_content

    random_image = random.choice(image_files)
    # image_path = os.path.join(image_dir, random_image).replace('\\', '/')
    image_markdown = f"![图片](../{random_image})\n"
    return f"{title_line}\n{image_markdown}{rest_lines}"


def _write_to_markdown_file(content: str, output_dir: str) -> str:
    """将 Markdown 内容写入指定目录下的 hot_word.md 文件"""
    md_dir = os.path.join(output_dir, "md")
    base_name = os.path.basename(output_dir)
    os.makedirs(md_dir, exist_ok=True)
    file_path = os.path.join(md_dir, f"{base_name}_{datetime.datetime.now().strftime('%Y年%m月%d日%H时%M分')}.md")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return file_path
