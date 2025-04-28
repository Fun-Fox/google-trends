from dotenv import load_dotenv
from pocketflow import Node
from .utils import call_llm, search_web
import yaml

load_dotenv()


class DecideAction(Node):
    def prep(self, shared):
        """准备上下文和问题，用于决策过程。

        参数:
            shared (dict): 共享存储，包含上下文和问题。

        返回:
            tuple: 包含问题和上下文的元组。
        """
        # 获取当前上下文（如果不存在，则默认为“无先前搜索”）
        context = shared.get("context", "无先前搜索")
        # 从共享存储中获取问题
        hot_word = shared["hot_word"]
        logger = shared["logger"]
        # 返回问题和上下文，供 exec 步骤使用
        return hot_word, context, logger

    def exec(self, inputs):
        """调用 LLM 决定是搜索还是回答。"""
        hot_word, context, logger = inputs

        logger.info(f"代理正在决定下一步操作...")
        # 创建一个提示，帮助 LLM 决定下一步操作，并使用适当的 yaml 格式
        prompt = f"""
            ### 上下文
            你是一个可以搜索网络的研究助手
            现在给你一个时下网络流行热词，你需要进行深度查询，确保最终理解并能够全面的回答该热词对应的叙事内容。
            时下流行热词: {hot_word}
            先前的研究: 
            {context}

            ### 操作空间
            [1] search
              描述: 在网络上查找更多信息
              参数:
                - query (str): 搜索内容

            [2] answer
              描述: 用当前知识回答问题
              参数:
                - answer (str): 问题的最终回答

            ## 下一步操作
            根据上下文和可用操作决定下一步操作。
            请以以下格式返回你的响应：

            ```yaml
            thinking: |
                <你的逐步推理过程>
            action: search OR answer
            reason: <为什么选择这个操作>
            answer: <如果操作是回答>
            search_query: <具体的搜索查询如果操作是搜索>
            ```
            重要：请确保：
            1. 对所有多行字段使用适当的缩进（4个空格）
            2. 使用|字符表示多行文本字段
            3. 保持单行字段不使用|字符
            4. 正确使用YAML格式
            5. 不允许直接在键后嵌套另一个键（如 answer: search_query:)
            """
        # 调用 LLM 进行决策
        response, success = call_llm(prompt, logger)
        if not success:
            logger.error("LLM 响应失败，请检查你的响应格式。")
            return {"action": "finish", "reason": "LLM 响应失败"}
        logger.info(f"LLM 响应: {response}")
        # 解析响应以获取决策
        if "```yaml" not in response:
            logger.error("LLM 响应格式不正确，请检查你的响应格式。")
            return {"action": "finish", "reason": "LLM 响应格式不正确"}
        yaml_str = response.replace("\"", "").replace("\'", "").split("```yaml")[1].split("```")[0].strip()
        decision = yaml.safe_load(yaml_str)

        return decision

    def post(self, shared, prep_res, exec_res):
        """保存决策并确定流程中的下一步。"""
        # 如果 LLM 决定搜索，则保存搜索查询
        logger = shared["logger"]
        if exec_res["action"] == "search":
            shared["search_query"] = exec_res["search_query"]
            logger.info(f"🔍 代理决定搜索: {exec_res['search_query']}")
        else:
            shared["context"] = exec_res["answer"]  # 保存上下文，如果 LLM 在不搜索的情况下给出回答。
            logger.info(f"💡 代理决定回答问题")

        # 返回操作以确定流程中的下一个节点
        return exec_res["action"]


class SearchWeb(Node):
    def prep(self, shared):
        """从共享存储中获取搜索查询。"""
        return shared["search_query"], shared["hot_word_path"], shared["logger"]

    def exec(self, inputs):
        """搜索网络上的给定查询。"""
        # 调用搜索实用函数
        search_query, hot_word_path, logger = inputs
        logger.info(f"🌐 在网络上搜索: {search_query}")
        results = search_web(search_query, hot_word_path, logger)
        return results

    def post(self, shared, prep_res, exec_res):
        """保存搜索结果并返回决策节点。"""
        # 将搜索结果添加到共享存储中的上下文中
        previous = shared.get("context", "")
        # 搜索记忆功能
        shared["context"] = previous + "\n\nSEARCH: " + shared["search_query"] + "\nRESULTS: " + exec_res
        logger = shared["logger"]
        logger.info(f"📚 找到信息，分析结果...")

        # 搜索后始终返回决策节点
        return "decide"


class AnswerEditor(Node):
    def prep(self, shared):
        """获取用于回答的问题和上下文。"""
        return shared["hot_word"], shared.get("context", ""), shared["logger"]

    def exec(self, inputs):
        """调用 LLM 编制草稿。"""
        hot_word, context, logger = inputs

        logger.info(f"编制草稿...")

        # 为 LLM 创建一个提示以基于网络研究内容编写草稿
        prompt = f"""
        ### 上下文
        基于以下信息，回答问题。
        时下网络流行热词: {hot_word}
        研究: 
        {context}

        ### 你的回答:
        结合热词对应的研究进行理解，撰写关于此部分的叙事文案，并且使用中文和英文。
        
        请以以下格式返回你的响应：
        
        ```yaml
        chinese: <中文叙事文案>
        english: <英文叙事文案>
        ```

        要求：
        - 用简单易懂的语言解释想法
        - 使用日常语言，避免术语
        - 正确使用YAML格式
        """
        # 调用 LLM 生成草稿
        draft, success = call_llm(prompt, logger)
        if "```yaml" not in draft:
            logger.error("LLM 响应格式不正确，请检查你的响应格式。")
            return {"action": "finish", "reason": "LLM 响应格式不正确"}
        yaml_str = draft.replace("\"", "").replace("\'", "").split("```yaml")[1].split("```")[0].strip()
        response = yaml.safe_load(yaml_str)
        if not success:
            logger.error("LLM 响应失败，请检查你的响应格式。")
            return {"action": "finish", "reason": "LLM 响应失败"}

        return draft, response

    def post(self, shared, prep_res, exec_res):
        """保存最终回答并完成流程。"""
        # 在共享存储中保存回答

        draft, response = exec_res
        shared['draft'] = draft
        shared['chinese'] = response['chinese']
        shared['english'] = response['english']
        logger = shared["logger"]
        logger.info(f"✅ 草稿生成成功：\n{draft}")

        # 我们完成了 - 不需要继续流程
        # return "done"
