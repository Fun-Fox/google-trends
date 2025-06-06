from datetime import datetime
from time import sleep

from dotenv import load_dotenv
from pocketflow import Node

from agent.tools.parser import analyze_site
from agent.tools.search import search_web
from agent.tools.crawler import NewsCrawler
from agent.utils import call_llm
import yaml

load_dotenv()
__all__ = ["DecideAction", "SearchWeb", ]

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
        search_volume = shared["search_volume"]
        search_growth_rate = shared["search_growth_rate"]
        search_active_time = shared["search_active_time"]
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shared["current_date"] = current_date
        logger = shared["logger"]
        language = shared["language"]
        # 返回问题和上下文，供 exec 步骤使用
        return current_date, hot_word, search_volume, search_growth_rate, search_active_time, context, relation_news, links_count, language, logger

    def exec(self, inputs):
        """调用 LLM 决定是搜索还是回答。"""
        current_date, hot_word, search_volume, search_growth_rate, search_active_time, context, relation_news, links_count, language, logger = inputs
        logger.info(f"代理正在决定下一步操作...")
        hot_word=hot_word.split("-",1)[1]
        desc = f"此热词从{search_active_time}开始搜索活跃,搜索量上升{search_growth_rate},搜索总量达到{search_volume}"
        # 创建一个提示，帮助 LLM 决定下一步操作，并使用适当的 yaml 格式
        prompt = f"""
你是一个可以搜索网络的热点新闻深度搜索助手
现在给你一个时下网络流行热词，你需要参考查询维度、先前的研究进行深度搜索，深度思考并理解该热词对应的叙事内容。
使用{language}回答
### 查询维度

- 事件基本信息 : 确认热词对应的具体事件、时间、地点、主要人物
- 事件发展脉络 : 事件起因、关键节点、最新进展
- 社会影响范围 : 受众群体、地域影响、行业影响
- 争议焦点 : 各方观点分歧、争论核心问题
- 官方回应 : 相关权威机构/人物的正式表态
- 关联事件 : 与此热点相关的历史/并行事件

并非所有查询条件都需满足，可使用优先级进行排序
查询优先级：事件基本信息>事件发展脉络>社会影响范围>争议焦点>官方回应>关联事件

## 上下文
- 当前时间: {current_date}
- 时下流行热词: {hot_word}
{desc}
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
如先前的研究，总计大于6条，则结合已有的研究进行回答操作，不再进行深度搜索，

请以以下格式返回你的响应：

```yaml
thinking: |
    <你的逐步推理过程>
action: search OR answer
reason: <为什么选择这个操作>
answer: |
    <如果操作是回答>
search_query: |
    <具体的搜索查询如果操作是搜索>
```
重要：请确保：

如先前的研究，总计大于6条，则结合已有的研究进行回答操作，不再进行深度搜索，
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

            try:
                crawler = NewsCrawler(link)
                crawl_content = crawler.extract_information()
                if crawl_content['text'] != '':
                    crawl_content_analyze = analyze_site(crawl_content, logger, language)
                else:
                    logger.info(f"🌐 深度搜索信息为空或者是二进制视频")
                    crawl_content_analyze = {}
            except Exception as e:
                analyzed_results.append({
                    "results": {},
                    "title": title,
                    "url": link,
                    'snippet': snippet
                })
                logger.error(f"深度搜索失败: {e}")
                continue
            analyzed_results.append({
                "results": crawl_content_analyze,
                "title": title,
                "url": link,
                'snippet': snippet
            })

        results = []
        for ret in analyzed_results:
            print(ret)
            if ret["results"] == {}:
                summary = '无'
                title = ret.get('title', '无')
            else:
                content = ret["results"]
                summary = content['analysis']['summary'].replace('\n', '')
                title = content['analysis']['title'].replace('\n', '')
            total_links_count += 1
            result = (
                # f"标题：{content.get('title', '无')}\n" +
                    f"🌐 报道{total_links_count}: {title}\n" +
                    f"链接：{ret.get('url', '无')}\n" +
                    # f"类型：{content['analysis']['content_type']}\n" +
                    # f"话题：{','.join(content['analysis']['topics'])}\n" +
                    f" 摘要-1：{summary}\n"
                    f" 摘要-2：{ret.get('snippet', '无')}\n"
            )
            results.append(result)
            # 统计链接数量
        # print(results)
        logger.info(f"✅ 当前已采集链接总数: {total_links_count}")

        return '\n'.join(results), total_links_count

    def post(self, shared, prep_res, exec_res):
        """保存搜索结果并返回决策节点。"""
        # 将搜索结果添加到共享存储中的上下文中
        results, links_count = exec_res
        previous = shared.get("context", "")
        search_history_previous = shared.get("search_history", "").strip()
        # 搜索记忆功能
        shared["context"] = previous + "\n\n搜索条件: " + shared[
            "search_query"] + "\n搜索结果(多条):\n " + results.strip()
        print("📚 搜索结果: " + results)
        shared["search_history"] = search_history_previous.strip() + results.strip()
        logger = shared["logger"]
        shared["links_count"] = links_count
        logger.info(f"📚 找到信息，分析结果...")

        # 搜索后始终返回决策节点
        return "decide"


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
