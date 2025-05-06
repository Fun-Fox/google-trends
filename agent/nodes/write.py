from dotenv import load_dotenv
from pocketflow import Node
from agent.utils import call_llm

__all__ = ["WriteInStyle", "WriteSupervisorNode"]
load_dotenv()


class WriteInStyle(Node):
    def prep(self, shared):
        """
        从共享数据中获取草稿
        """
        return shared["draft"], shared["prompt"], shared["logger"]

    def exec(self, inputs):
        """
        对文章应用特定风格
        """
        draft, prompt, logger = inputs

        # 将 draft 插入到 style_note 中
        prompt = (prompt +
                  '\n ## 时下热点详细叙事如下：\n'
                  + draft +
                  '\n ## 输出内容要求\n '
                  + """
                    - 只有一个角色则只输出一段话
                    - 有多个角色则以（角色名称：一段话）形式输出
                    - 不包含换行符\n
                    - 只包含纯文本
                    - 不包含语气描述词
                    """)

        logger.info(f"===已拿到风格撰写提示===\n{prompt}\n,===正在进行风格撰写===")

        # 调用 LLM 生成最终文章
        response, success = call_llm(prompt, logger)
        if not success:
            logger.error("LLM 响应失败，请检查你的响应格式。")
            return {"action": "finish", "reason": "LLM 响应失败"}
        logger.info(f"LLM 响应成功:{response}")
        return response

    def post(self, shared, prep_res, exec_res):
        """
        将最终文章存储在共享数据中
        """
        shared["final_article"] = exec_res
        logger = shared["logger"]
        logger.info(f"风格撰写结果:\n {exec_res}")

        return "final_article"


class WriteSupervisorNode(Node):
    def prep(self, shared):
        """获取当前回答以进行评估。"""
        return shared["final_article"], shared["logger"]

    def exec(self, inputs):
        """检查回答是否有效或无意义。"""
        final_article, logger = inputs
        logger.info(f"监督员正在检查回答质量...")

        # 检查无意义回答的明显标记
        nonsense_markers = [
            "coffee break",
            "purple unicorns",
            "made up",
            "42",
            "Who knows?"
        ]

        # 检查回答是否包含任何无意义标记
        is_nonsense = any(marker in final_article for marker in nonsense_markers)

        if is_nonsense:
            return {"valid": False, "reason": "回答似乎无意义或无帮助"}
        else:
            return {"valid": True, "reason": "回答似乎是合法的"}

    def post(self, shared, prep_res, exec_res):
        logger = shared["logger"]
        """决定是否接受回答或重新启动流程。"""
        if exec_res["valid"]:
            logger.info(f"监督员通过了回答: {exec_res['reason']}")
        else:
            logger.info(f"监督员拒绝了回答: {exec_res['reason']}")
            # 清理错误的回答
            shared["final_article"] = None
            # 添加关于被拒绝回答的注释
            context = shared.get("draft", "")
            shared["draft"] = context + "\n\n注意: 之前的撰写内容尝试被监督员拒绝了。"

            return "retry"
