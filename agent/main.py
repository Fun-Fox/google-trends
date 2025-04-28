import os

from fastapi import FastAPI, HTTPException
from .flow import create_agent_flow

app = FastAPI()
__all__ = ["write_style_assistant",]

def write_style_assistant(hot_word_path: str,logger) -> str:
    """处理"""
    try:
        if hot_word_path == [] or hot_word_path == "" or hot_word_path == None:
            return "请输入热词"
        # 创建代理流程
        agent_flow = create_agent_flow()
        # 检查 hot_word_path 是否为有效的路径
        if not os.path.exists(hot_word_path):
            return "热词路径不存在"

        # 处理问题
        hot_word = os.path.basename(hot_word_path)
        shared = {"hot_word": hot_word, "hot_word_path": hot_word_path,"logger": logger}
        logger.info(f"正在分析时下网络流行热词: {hot_word}")
        agent_flow.run(shared)
        logger.info(f"[Agent任务完成]-[DONE] ")
    except Exception as e:
        logger.error(f"处理热词时发生异常: {e}")
        return "处理热词时发生异常。"


from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask")
async def ask_question(request: QuestionRequest,logger):
    """API接口，接收问题并返回答案。"""
    if not request.question:
        raise HTTPException(status_code=400, detail="问题不能为空")
    final_article = write_style_assistant(request.question)
    logger.info(f"处理完成: {final_article}")
    return final_article


if __name__ == "__main__":
    # import uvicorn

    # uvicorn.run(app, host="0.0.0.0", port=8000)
    #
    result = write_style_assistant("关税")
    print("\n===== 最终文章 =====\n")
    print(result)

    print("\n========================\n")
    # print(article)
