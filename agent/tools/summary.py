import datetime
import os
import random
from typing import Dict
from agent.utils import call_llm


def generate_news_summary_report(highlights: str, output: str, hot_word_path: str, hot_word_info, logger,
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
    prompt = _build_prompt(output, highlights, language, hot_word_info)
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
        md_file_path = _write_to_markdown_file(response_with_image, hot_word_path,language)
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

def _build_prompt(output: str, highlights: str, language: str, hot_word_info) -> str:
    search_volume = hot_word_info["search_volume"]
    search_growth_rate = hot_word_info["search_growth_rate"]
    search_active_time = hot_word_info["search_active_time"]
    current_date = hot_word_info["current_date"]
    # desc = f"此内容从{search_active_time}开始搜索活跃,搜索量上升{search_growth_rate},搜索总量达到{search_volume}"
    # """构建 LLM 所需的 Prompt"""
    prompt = f"""
你是一位专业热点新闻海报设计师，请根据以下信息生成具有传播力的新闻海报内容。

# 内容定位
- 目标平台：{language}社交媒体平台
- 核心诉求：在{hot_word_info["search_active_time"]}时段抓住{hot_word_info["search_growth_rate"]}的爆发性增长
- 传播目标：引发行业讨论+公众关注

# 视觉风格，可以参考但不限于以下内容
- 使用社交媒体风格的短句表达
- 重要数据用🎉🔥💥🌟等emoji标注
- 关键时间节点用📅⏳⏰等时间符号强调
- 使用💡小贴士标注
- 采用阶梯式信息递进结构

# 核心要素
当前时间：{current_date}
内容叙述：
{output}
相关优质报道:
{highlights}
搜索热度：🔥{hot_word_info["search_volume"]} (↑{hot_word_info["search_growth_rate"]})
活跃时段：🕒{hot_word_info["search_active_time"]}

# 内容结构
1. 惊爆标题（使用悬念/数字/对比手法）
    - 要求：必须包含emoji
2. 事件解码（结合内容叙述、相关优质报道），可以参考但不限于以下内容
    - 一句话真相：使用优质报道的真相
    - 专家解读：用「」符号标注权威观点
    - 政策动向：用⚖️标注监管信号
    - 行业影响：用💰标注经济关联
    - 自我观点：用💬标注你对此事的评论

3. 影响预测（使用符号化表达），可以参考但不限于以下内容
   - 经济层面：💰
   - 社会层面：👥
   - 政策层面：⚖️
4. 传播预测（新增模块），可以参考但不限于以下内容
   - 潜在爆点：预测可能引发二次传播的要素
   - 关联热搜：列出3个可能联动的热点话题
   - 传播建议：提供2条互动引导语

# 注意！确保
- 使用{language}输出内容
- Markdown语法
- 只允许一个一级标题
- 清晰的文档结构，有二级标题
- 关键数据用**加粗**
"""
    if "中" in language:
        return prompt + "\n-在末尾添加 #热点追踪 #数据分析 标签"
    else:
        # return prompt + "\n# Hot Tracking #Data Analysis"
        return prompt


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
    print(f"随机选择的图片路径: {image_markdown}")
    return f"{title_line}\n{image_markdown}{rest_lines}"


def _write_to_markdown_file(content: str, output_dir: str,language) -> str:
    """将 Markdown 内容写入指定目录下的 hot_word.md 文件"""
    md_dir = os.path.join(output_dir, "md")
    base_name = os.path.basename(output_dir)
    os.makedirs(md_dir, exist_ok=True)
    file_path = os.path.join(md_dir, f"{base_name}_{language}.md")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return file_path
