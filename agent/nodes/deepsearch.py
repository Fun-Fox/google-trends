from time import sleep

from dotenv import load_dotenv
from pocketflow import Node

from agent.tools.parser import analyze_site
from agent.tools.search import search_web
from agent.tools.crawler import WebCrawler
from agent.utils import call_llm
import yaml

load_dotenv()
__all__ = ["DecideAction", "SearchWeb", "AnswerEditor"]

total_links_count = 0


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
        links_count = shared.get("links_count", 0)
        relation_news = shared["relation_news"]
        logger = shared["logger"]
        # 返回问题和上下文，供 exec 步骤使用
        return hot_word, context, relation_news, links_count, logger

    def exec(self, inputs):
        """调用 LLM 决定是搜索还是回答。"""
        hot_word, context, relation_news, links_count, logger = inputs

        logger.info(f"代理正在决定下一步操作...")
        # 创建一个提示，帮助 LLM 决定下一步操作，并使用适当的 yaml 格式
        prompt = f"""
            你是一个可以搜索网络的热点新闻深度搜索助手
            现在给你一个时下网络流行热词，你需要参考查询维度、先前的研究进行深度搜索，深度思考并理解该热词对应的叙事内容。
            
            ### 查询维度
            
            - 发生时间：最近48小时内
            - 事件基本信息 : 确认热词对应的具体事件、时间、地点、主要人物
            - 事件发展脉络 : 事件起因、关键节点、最新进展
            - 社会影响范围 : 受众群体、地域影响、行业影响
            - 争议焦点 : 各方观点分歧、争论核心问题
            - 官方回应 : 相关权威机构/人物的正式表态
            - 关联事件 : 与此热点相关的历史/并行事件
            
            并非所有查询条件都需满足，可使用优先级进行排序
            查询优先级：事件基本信息>事件发展脉络>社会影响范围>争议焦点>官方回应>关联事件
            
            ## 上下文
            - 时下流行热词: 
            
            {hot_word}
            
            - 相关新闻报导标题：
            
            {relation_news}
            
            - 先前的研究,总计为{links_count}条,具体如下：
            
            {context}

            ## 操作空间
            [1] search
              描述: 在网络上查找更多信息
              参数:
                - query (str): 搜索内容

            [2] answer
              描述: 用当前知识回答问题
              参数:
                - answer (str): 问题的最终回答

            ### 下一步操作
            根据上下文、查询维度和可用操作决定下一步操作。
            重要：请确保：
            如先前的研究，总计大于10条，则结合已有的研究进行回答操作，不再进行深度搜索，
            
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
            
            如先前的研究，总计大于10条，则结合已有的研究进行回答操作，不再进行深度搜索，
            1. 使用|字符表示多行文本字段
            2. 多行字段使用缩进（4个空格）
            3. 单行字段不使用|字符
            4. 不允许直接在键后嵌套另一个键（如 answer: search_query:)
            5. 非键值对不允许随意使用冒号: 
            """
        # 调用 LLM 进行决策
        response, success = call_llm(prompt, logger)
        if not success:
            logger.error("LLM 响应失败，请检查你的响应格式。")
            return {"action": "finish", "reason": "LLM 响应失败"}

        # 解析响应以获取决策
        if "```yaml" not in response:
            logger.error("LLM 响应格式不正确，请检查你的响应格式。")
            return {"action": "finish", "reason": "LLM 响应格式不正确"}
        try:
            yaml_str = response.replace("\"", "").replace("\'", "").split("```yaml")[1].split("```")[0].strip()
            logger.info(f"LLM 响应: {yaml_str}")
            decision = yaml.safe_load(yaml_str)
        except Exception as e:
            return {"action": "finish", "reason": "LLM 响应格式不正确"}

        return decision

    def post(self, shared, prep_res, exec_res):
        """保存决策并确定流程中的下一步。"""
        # 如果 LLM 决定搜索，则保存搜索查询
        logger = shared["logger"]
        if exec_res["action"] == "search":
            shared["search_query"] = exec_res["search_query"]
            logger.info(f"🔍 代理决定搜索: {exec_res['search_query']}")
        else:
            shared["context"] = exec_res["answer"]
            logger.info(f"💡 代理决定回答问题")
            global total_links_count
            total_links_count = 0

        # 返回操作以确定流程中的下一个节点
        return exec_res["action"]


class SearchWeb(Node):
    def prep(self, shared):
        """从共享存储中获取搜索查询。"""
        return shared["search_query"], shared["hot_word_path"], shared["language"], shared["logger"]

    def exec(self, inputs):
        """搜索网络上的给定查询。"""
        # 调用搜索实用函数
        global total_links_count  # 声明使用全局变量
        search_query, hot_word_path, language, logger = inputs
        logger.info(f"🌐 在网络上搜索: {search_query}")
        sleep(5)
        _, results_dict = search_web(search_query, hot_word_path, logger)
        analyzed_results = []
        if results_dict is None:
            logger.info(f"🌐 深度搜索失败。")
            return {"action": "finish", "reason": "搜索失败"}
        for i in results_dict:
            title = i['title']
            snippet = i['snippet']
            link = i['link']

            logger.info(f"🌐 对搜索的内容进项深度扫描")
            logger.info(f"🌐 标题:{title}")
            logger.info(f"🌐 摘要:{snippet}")

            logger.info(f"🌐 源链接:{link}")
            content_list = WebCrawler(link).crawl()

            analyzed_results.append(analyze_site(content_list, logger, language))

        results = []
        for analyzed_result in analyzed_results:
            for content in analyzed_result:
                total_links_count += 1

                result = (
                    # f"标题：{content.get('title', '无')}\n" +
                    # f"链接：{content.get('url', '无')}\n" +
                        f"🌐 报道{total_links_count}: {content['analysis']['title']}\n" +
                        # f"类型：{content['analysis']['content_type']}\n" +
                        # f"话题：{','.join(content['analysis']['topics'])}\n" +
                        f"{content['analysis']['summary']}\n\n"

                )
                results.append(result)
                # 统计链接数量

        logger.info(f"✅ 当前已采集链接总数: {total_links_count}")

        return '\n\n'.join(results), total_links_count

    def post(self, shared, prep_res, exec_res):
        """保存搜索结果并返回决策节点。"""
        # 将搜索结果添加到共享存储中的上下文中
        results, links_count = exec_res
        previous = shared.get("context", "")
        search_history_previous = shared.get("search_history", "").strip()
        # 搜索记忆功能
        shared["context"] = previous + "\n\n搜索条件: " + shared[
            "search_query"] + "\n搜索结果(多条):\n " + results.strip()
        shared["search_history"] = search_history_previous.strip() + results.strip()
        logger = shared["logger"]
        shared["links_count"] = links_count
        logger.info(f"📚 找到信息，分析结果...")

        # 搜索后始终返回决策节点
        return "decide"


class AnswerEditor(Node):
    def prep(self, shared):
        """获取用于回答的问题和上下文。"""
        return shared["hot_word"], shared.get("context"), shared["logger"]

    def exec(self, inputs):
        """调用 LLM 编制草稿。"""
        hot_word, context, logger = inputs

        logger.info(f"编制草稿...")

        # 为 LLM 创建一个提示以基于网络研究内容编写草稿
        prompt = f"""
        ## 上下文
        
        你是一个热点信息精炼助手，基于以下信息，回答问题。
        
        ### 精炼维度
        
        - 核心事实提取: 从海量信息中提取关键事实要素
        - 舆情脉络梳理: 梳理公众情绪变化与讨论焦点转移路径
        - 发酵点识别: 识别推动话题扩散的关键节点与触发因素
        - 趋势预判: 基于现有信息预测话题可能的发展方向
        
        ### 输入格式:
        
        时下网络流行热词: {hot_word}
        相关研究: 
        
        {context}

        ### 你的回答:
        结合热词对应的研究进行理解
        - 使用精炼维度撰写叙事文案
        - 使用中文和英文。
        - 用简单易懂的语言解释想法
        - 使用日常语言，避免术语
        
        同时，请从相关研究中提取 **2个最相关的优质报道摘要**，包含：
        - 报道标题 (title) 翻译为中文
        - 内容摘要 (summary) 翻译为中文
        - 来源链接 (link)
                
        请以以下格式返回你的响应：
        
        ```yaml
        chinese: |
            <中文叙事文案>
        english: |
            <英文叙事文案>
        highlights: 
          - title: <报道标题1> 
            summary: <摘要> 
            link: <来源链接>
          - title: <报道标题2> 
            summary: <摘要> 
            link: <来源链接> 
        ```

        重要：请确保：
        1. 使用|字符表示多行文本字段
        2. 多行字段使用缩进（4个空格）
        3. 单行字段不使用|字符
        4. 保证 chinese 和 english 的缩进一致，并且 | 后的内容至少比键多一级缩进即可。
        """
        # 调用 LLM 生成草稿
        draft, success = call_llm(prompt, logger)
        if "```yaml" not in draft:
            logger.error("LLM 响应格式不正确，请检查你的响应格式。")
            return {"action": "finish", "reason": "LLM 响应格式不正确"}
        try:
            yaml_str = draft.replace("\"", "").replace("\'", "").split("```yaml")[1].split("```")[0].strip()
        except Exception as e:
            return {"action": "finish", "reason": "LLM 响应格式不正确"}
        logger.info(f"LLM 响应: \n {yaml_str}")
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
        highlights = response.get('highlights', [])
        if highlights:
            highlights_str = "\n".join([
                f"🌐报道{index}:\n{highlight['title']}\n摘要：\n{highlight['summary']}\n来源：\n{highlight['link']}\n\n"
                for index, highlight in enumerate(highlights, start=1)
            ])
        else:
            highlights_str = ""
        shared['highlights'] = highlights_str  # 存入优质报道列表
        logger = shared["logger"]
        logger.info(f"✅ 草稿生成成功：\n{draft}")

        # 我们完成了 - 不需要继续流程
        # return "done"


#
# class AnalyzeResultsNode(Node):
#     """使用LLM分析搜索结果"""
#
#     def prep(self, shared):
#         return shared.get("query"), shared.get("search_results", [])
#
#     def exec(self, inputs):
#         query, results = inputs
#         if not results:
#             return {
#                 "summary": "没有搜索结果进项分析",
#                 "key_points": [],
#                 "follow_up_queries": []
#             }
#
#         return analyze_results(query, results)
#
#     def post(self, shared, prep_res, exec_res):
#         shared["analysis"] = exec_res
#
#         # Print analysis
#         print("\n搜索结果:")
#         print("\n汇总:", exec_res["summary"])
#
#         print("\n关键点:")
#         for point in exec_res["key_points"]:
#             print(f"- {point}")
#
#         print("\n推荐后续搜索内容:")
#         for query in exec_res["follow_up_queries"]:
#             print(f"- {query}")
#
#         return "default"


if __name__ == "__main__":
    response = """
    ```yaml
thinking: |
  The user is interested in RuPaul's initial response to Jiggly Caliente's death and the criticism that followed.  Several sources mention RuPaul's initial statement, but the details and the extent of the criticism aren't fully clear. A focused search about RuPaul's specific initial response and the subsequent backlash would clarify the situation.
action: search
reason: To gather more specific information about RuPaul's initial reaction and the associated criticism.
search_query: "RuPaul initial response Jiggly Caliente death criticism"
```
    """

    yaml_str = response.replace("\"", "").replace("\'", "").split("```yaml")[1].split("```")[0].strip()
    print(f"LLM 响应: {yaml_str}")
    decision = yaml.safe_load(yaml_str)
