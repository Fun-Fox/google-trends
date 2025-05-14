import re
from typing import Dict, List
from agent.utils.call_llm import call_llm

__all__ = ["analyze_content", "analyze_site"]


def analyze_content(content: Dict, logger, language="中文") -> Dict:
    """使用大语言模型分析网页内容

    参数:
        content (Dict): 包含网址、标题和文本的网页内容

    返回:
        Dict: 包含总结和主题的分析结果
    """
    prompt = f"""
## 请分析以下网页内容：

标题: {content['title']}
链接: {content['url']}
内容: {content['text'][:2000]}  # 限制内容长度

## 请提供：
1. 使用{language}进行简要总结（2-4句话）
2. 主题或关键词（最多5个）
3. 内容类型（文章、产品页面等）

## 请以下格式返回你的响应,无需其余信息：
```yaml
title: <在这里填写标题>
summary: 
    <在这里填写简要总结>
topics: ["关键词1","关键词2"]
content_type: <填写内容类型>
```

## 重要：请确保：
1. 对所有多行字段使用适当的缩进（4个空格）
2. 使用|字符表示多行文本字段
3. 保持单行字段不使用|字符
4. 正确使用YAML字符串格式
5. 使用{language}进行简要总结（2-4句话）
"""

    try:
        response, success = call_llm(prompt, logger=logger)
        if not success:
            logger.error("LLM 响应失败，请检查你的响应格式。")
            return {"action": "finish", "reason": "LLM 响应失败"}

        # 提取代码块中的YAML内容
        if "```yaml" not in response:
            logger.error("LLM 响应格式不正确，请检查你的响应格式。")
            return {"action": "finish", "reason": "LLM 响应格式不正确"}
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        import yaml
        analysis = yaml.safe_load(yaml_str)

        # 验证必要字段是否存在
        assert "summary" in analysis
        assert "topics" in analysis
        assert "content_type" in analysis
        assert "title" in analysis
        assert isinstance(analysis["topics"], list)

        return analysis

    except Exception as e:
        print(f"分析网页内容时出错: {str(e)}")
        return {
            "title": "未知",
            "summary": "分析网页内容时出错",
            "topics": [],
            "content_type": "未知"
        }


def analyze_site(crawl_results: List[Dict], logger, language) -> List[Dict]:
    """分析所有爬取的网页内容

    参数:
        crawl_results (List[Dict]): 爬取的网页内容列表

    返回:
        List[Dict]: 包含分析结果的原始内容
    """
    analyzed_results = []

    for content in crawl_results:
        if content and content.get("text"):
            analysis = analyze_content(content, logger, language=language)
            content["analysis"] = analysis
            analyzed_results.append(content)

    return analyzed_results
