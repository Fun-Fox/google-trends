import os

import pandas as pd

from webui.service.search import convert_to_img, load_summary_and_paths
# from fastapi import FastAPI, HTTPException
from .flow import deepsearch_flow, content_flow

# app = FastAPI()
__all__ = ["hot_word_research_assistant", "write_in_style_assistant"]


def get_relation_news_by_hot_word(hot_word_path: str) -> str | None:
    """
    根据 hot_word_path 获取对应的 relation_news 内容
    :param hot_word_path: 热词文件夹路径
    :return: relation_news 字符串 或 None
    """
    # 获取热词名称（即文件夹名）
    hot_word = os.path.basename(hot_word_path)

    # 获取该热词所在的任务目录
    task_dir = os.path.dirname(hot_word_path)

    # 查找该任务目录下的所有 .csv 文件
    csv_files = [f for f in os.listdir(task_dir) if f.endswith('.csv')]
    # print(csv_files)
    if not csv_files:
        print(f"未找到 CSV 文件在目录: {task_dir}")
        return None

    # 使用第一个 CSV 文件（假设只有一个有效 CSV）
    csv_file_path = os.path.join(task_dir, csv_files[0])

    try:
        # 读取 CSV 文件
        df = pd.read_csv(csv_file_path, encoding="utf-8-sig")

        # 检查必要列是否存在
        if 'hot_word' not in df.columns or 'relation_news' not in df.columns:
            print(f"CSV 文件缺少必要列: {csv_file_path}")
            return None

        # 查找匹配的行
        row = df[df['hot_word'] == hot_word]

        if row.empty:
            print(f"未找到 hot_word 为 '{hot_word}' 的记录")
            return None

        # 返回 relation_news 字段内容
        relation_news = row.iloc[0]['relation_news']
        print(f"relation_news: {relation_news}")
        return str(relation_news) if pd.notna(relation_news) else None

    except Exception as e:
        print(f"relation_news_by_hot_word:读取 CSV 文件时发生错误: {e}")
        return None


def hot_word_research_assistant(hot_word_path: str, language,logger) -> str | None:
    """处理"""
    try:
        if hot_word_path == [] or hot_word_path == "" or hot_word_path is None:
            return "请输入热词"
        # 创建代理流程
        agent_flow = deepsearch_flow()
        # 检查 hot_word_path 是否为有效的路径
        if not os.path.exists(hot_word_path):
            return "热词路径不存在"

        relation_news = '\n'.join(get_relation_news_by_hot_word(hot_word_path).split('---'))

        # 处理问题
        hot_word = os.path.basename(hot_word_path)
        shared = {"hot_word": hot_word, "relation_news": relation_news, "hot_word_path": hot_word_path,
                  "logger": logger, "language": language}
        logger.info(f"===正在分析时下网络流行热词===:\n {hot_word},使用语言:\n {language},关联新闻:\n{relation_news}")
        agent_flow.run(shared)

        logger.info(f"[热词深度搜索Agent任务完成]-[DONE] ")
        print(f"查询md汇总文件,：{hot_word_path}")
        input_md_path = load_summary_and_paths(hot_word_path)
        print(f"md生成成功：{input_md_path}")
        convert_to_img(input_md_path)
        print(f"md转图片\转视频\转网页成功")
        return "[热词深度搜索Agent任务完成]-[DONE]"
    except Exception as e:
        logger.error(f"处理热词时发生异常: {e}")
        raise e


def write_in_style_assistant(draft: str, prompt: str, logger) -> str | None:
    try:
        shared = {
            "draft": draft, "prompt": prompt, "logger": logger
        }
        agent_flow = content_flow()
        logger.info(f"\n 正在结合时下热点叙事进行撰写:\n {draft}")
        agent_flow.run(shared)
        final_article = shared.get("final_article", "No answer found")

        logger.info(f"[Agent任务完成]-[DONE]: \n {final_article} ")
        return final_article
    except Exception as e:
        logger.error(f"风格转写出现异常: {e}")
        return "风格转写出现异常。"


#
# from pydantic import BaseModel
#
#
# class QuestionRequest(BaseModel):
#     question: str
#
#
# @app.post("/ask")
# async def ask_question(request: QuestionRequest,logger):
#     """API接口，接收问题并返回答案。"""
#     if not request.question:
#         raise HTTPException(status_code=400, detail="问题不能为空")
#     final_article = hot_word_research_assistant(request.question)
#     logger.info(f"处理完成: {final_article}")
#     return final_article
#

if __name__ == "__main__":
    # import uvicorn

    # uvicorn.run(app, host="0.0.0.0", port=8000)
    #
    # result = hot_word_research_assistant("关税")
    print("\n===== 最终文章 =====\n")
    # print(result)

    print("\n========================\n")
    # print(article)
