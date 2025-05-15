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
        language = shared["language"]
        # 返回问题和上下文，供 exec 步骤使用
        return hot_word, context, relation_news, links_count, language, logger

    def exec(self, inputs):
        """调用 LLM 决定是搜索还是回答。"""
        hot_word, context, relation_news, links_count, language, logger = inputs

        logger.info(f"代理正在决定下一步操作...")
        # 创建一个提示，帮助 LLM 决定下一步操作，并使用适当的 yaml 格式
        prompt = f"""
            你是一个可以搜索网络的热点新闻深度搜索助手
            现在给你一个时下网络流行热词，你需要参考查询维度、先前的研究进行深度搜索，深度思考并理解该热词对应的叙事内容。
            使用{language}回答
            
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
        if exec_res["action"].strip() == "search":
            shared["search_query"] = exec_res["search_query"].strip()
            logger.info(f"🔍 代理决定搜索: {exec_res['search_query']}")
        else:
            shared["context"] = exec_res["answer"].strip()
            logger.info(f"💡 代理决定回答问题")
            global total_links_count
            total_links_count = 0

        # 返回操作以确定流程中的下一个节点
        return exec_res["action"].strip()


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
        return shared["hot_word"], shared.get("context"), shared.get("language"), shared["logger"]

    def exec(self, inputs):
        """调用 LLM 编制草稿。"""
        hot_word, context, language, logger = inputs

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
1. 请根据研究内容撰写如下两部分叙事文案：
   - 中文叙事 (`chinese`)
   - {language}叙事 (`output`)
   - 内容要求：
     * 使用日常语言，避免术语
     * 涵盖核心事实、舆情脉络、发酵点及趋势预判等维度
     * 每段保持结构清晰，逻辑通顺

2. 同时，请从研究内容中提取 **2个最相关的优质报道摘要**，并返回以下结构：

```yaml
highlights: 
  - title: <报道标题1,使用{language}> 
    summary: <摘要,使用{language}> 
    link: "<来源链接,链接使用引号>"
  - title: <报道标题2,使用{language}> 
    summary: <摘要,使用{language}> 
    link: "<来源链接,链接使用引号>"
chinese: |
    <中文叙事文案>
output: |
    <{language}叙事文案,注意此部分文案使用{language}>
```

重要：请确保：
⚠️ YAML 格式要求：
- 所有字段使用英文冒号 `:` + **一个空格** 开始值
- 多行字段使用 `|` 表示，并至少比键名多一级缩进（推荐 4 个空格）
- 列表项（`-`）需统一缩进
- 不允许在 `title:`、`summary:`、`link:` 后直接嵌套新结构
- 避免使用中文冒号 `：` 或省略空格
- 不要对 `chinese` 和 `output` 字段进行嵌套或添加额外结构
        """
        # 调用 LLM 生成草稿
        draft, success = call_llm(prompt, logger)
        if "```yaml" not in draft:
            logger.error("LLM 响应格式不正确，请检查你的响应格式。")
            return {"action": "finish", "reason": "LLM 响应格式不正确"}
        try:
            yaml_str = draft.split("```yaml")[1].split("```")[0].strip()
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
        shared['output'] = response['output']
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


if __name__ == "__main__":
    import re

    response = """
```yaml
highlights:
  - title: 《实习完美》安娜·坎普公开新恋情，甜蜜互动引发关注
    summary: 美国演员安娜·坎普（Anna Camp）确认了与造型师Jade Whipkey的恋爱关系，她在Instagram上分享了两人甜蜜的约会照片，并配有爱心表情。Jade Whipkey的回应“她的笑容是诗”也进一步确认了关系的甜蜜。此次公开恋情引发了粉丝的祝福和关注。
    link: "https://www.sohu.com/a/6726511775362662839"
  - title: 《实习完美》女演员安娜·坎普恋爱了？甜蜜合影秀出新恋情
    summary: 演员安娜·坎普（Anna Camp）公开了与造型师Jade Whipkey的恋情，她在Instagram上分享了与Jade Whipkey的合影，甜蜜互动引发了网络热议。她此前曾与演员Sylar Astin结婚，离婚近六年，这次是她离婚后的首次公开恋情。
    link: "https://news.caijing.com.cn/20240120/1234648653.html"
```
    """

    yaml_str = response.split("```yaml")[1].split("```")[
        0].strip()
    # 插入换行符，强制每行一个字段
    yaml_str = re.sub(r":(\S)", r": \1", yaml_str)
    # 强制为 YAML 标记字段添加换行
    yaml_str = re.sub(r'(highlights:|chinese:|output:)', r'\n\1', yaml_str)

    print(f"LLM 响应: {yaml_str}")
    decision = yaml.safe_load(yaml_str)
