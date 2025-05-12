from typing import Dict, List
from agent.utils.call_llm import call_llm

__all__ = ["analyze_results", "analyze_content", "analyze_site"]
def analyze_results(query: str, results: List[Dict]) -> Dict:
    """使用大语言模型分析搜索结果

    参数:
        query (str): 原始搜索查询
        results (List[Dict]): 要分析的搜索结果

    返回:
        Dict: 包含总结、关键点和后续建议查询的分析结果
    """
    # 格式化结果以便构建提示词
    formatted_results = []
    for i, result in enumerate(results, 1):
        formatted_results.append(f"""
结果 {i}:
标题: {result['title']}
摘要: {result['snippet']}
链接: {result['link']}
""")
    formatted_results_str = '\n'.join(formatted_results)
    prompt = f"""
请分析以下针对查询 "{query}" 的搜索结果：

{formatted_results_str}

请提供：
1. 简要总结（2-3句话）
2. 关键要点或事实（最多5个条目）
3. 建议的后续问题（2-3个）

输出格式为 YAML：
```yaml
summary: <总结>
key_points:
  - <关键点1>
  - <关键点2>
follow_up_queries:
  - <建议的问题1>
  - <建议的问题2>
```
    """

    try:
        response = call_llm(prompt)
        # 提取代码块中的YAML内容
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()


        import yaml

        analysis = yaml.safe_load(yaml_str)

        # 验证必要字段是否存在
        assert "summary" in analysis
        assert "key_points" in analysis
        assert "follow_up_queries" in analysis
        assert isinstance(analysis["key_points"], list)
        assert isinstance(analysis["follow_up_queries"], list)

        return analysis

    except Exception as e:
        print(f"分析结果时出错: {str(e)}")
        return {
            "summary": "分析结果时出错",
            "key_points": [],
            "follow_up_queries": []
        }


def analyze_content(content: Dict) -> Dict:
    """使用大语言模型分析网页内容

    参数:
        content (Dict): 包含网址、标题和文本的网页内容

    返回:
        Dict: 包含总结和主题的分析结果
    """
    prompt = f"""
请分析以下网页内容：

标题: {content['title']}
链接: {content['url']}
内容: {content['text'][:2000]}  # 限制内容长度

请提供：
1. 简要总结（2-3句话）
2. 主题或关键词（最多5个）
3. 内容类型（文章、产品页面等）

输出格式为 YAML：
```yaml
summary: >
    <在这里填写简要总结>
topics:
    - 主题1 
    - 主题2
content_type: <填写内容类型>
```
"""

    try:
        response = call_llm(prompt)
        # 提取代码块中的YAML内容
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()

        import yaml
        analysis = yaml.safe_load(yaml_str)

        # 验证必要字段是否存在
        assert "summary" in analysis
        assert "topics" in analysis
        assert "content_type" in analysis
        assert isinstance(analysis["topics"], list)

        return analysis

    except Exception as e:
        print(f"分析网页内容时出错: {str(e)}")
        return {
            "summary": "分析网页内容时出错",
            "topics": [],
            "content_type": "未知"
        }


def analyze_site(crawl_results: List[Dict]) -> List[Dict]:
    """分析所有爬取的网页内容

    参数:
        crawl_results (List[Dict]): 爬取的网页内容列表

    返回:
        List[Dict]: 包含分析结果的原始内容
    """
    analyzed_results = []

    for content in crawl_results:
        if content and content.get("text"):
            analysis = analyze_content(content)
            content["analysis"] = analysis
            analyzed_results.append(content)

    return analyzed_results