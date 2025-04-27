import csv
import os

from dotenv import load_dotenv
from pocketflow import Node
from .utils import call_llm, search_web, get_images, evaluate_image_relevance
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
            你是一个可以搜索网络的研究助手，现在给你一个Google trends美国地区时下流行热词，深度查询理解该热词对应的事件。
            Google trends美国地区时下流行热词: {hot_word}
            先前的研究: {context}
            
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
            4. 正确使用YAML字符串格式
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
        Google trends美国地区时下流行热词: {hot_word}
        研究: {context}
        
        ### 你的回答:
        结合研究进行完全理解，写一段关于此部分的简短段落（最多 100 字）。
        
        要求：
        - 用简单易懂的语言解释想法
        - 使用日常语言，避免术语
        - 保持非常简洁（不超过 100 字）
        - 包括一个简短的例子或类比
        """
        # 调用 LLM 生成草稿
        draft, success = call_llm(prompt, logger)
        if not success:
            logger.error("LLM 响应失败，请检查你的响应格式。")
            return {"action": "finish", "reason": "LLM 响应失败"}

        return draft

    def post(self, shared, prep_res, exec_res):
        """保存最终回答并完成流程。"""
        # 在共享存储中保存回答

        draft = exec_res
        shared['draft'] = draft
        logger = shared["logger"]
        logger.info(f"✅ 草稿生成成功")

        # 我们完成了 - 不需要继续流程
        # return "done"


# 监督节点
class SupervisorNode(Node):
    def prep(self, shared):
        """获取当前回答以进行评估。"""
        return shared["draft"], shared["logger"]

    def exec(self, inputs):
        """检查回答是否有效或无意义。"""
        answer, logger = inputs
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
        is_nonsense = any(marker in answer for marker in nonsense_markers)

        if is_nonsense:
            return {"valid": False, "reason": "回答似乎无意义或无帮助"}
        else:
            return {"valid": True, "reason": "回答似乎是合法的"}

    def post(self, shared, prep_res, exec_res):
        logger = shared["logger"]
        """决定是否接受回答或重新启动流程。"""
        if exec_res["valid"]:
            logger.info(f"监督员批准了回答: {exec_res['reason']}")
            return "approved"
        else:
            logger.info(f"监督员拒绝了回答: {exec_res['reason']}")
            # 清理错误的回答
            shared["answer"] = None
            # 添加关于被拒绝回答的注释
            context = shared.get("context", "")
            shared["context"] = context + "\n\n注意: 之前的回答尝试被监督员拒绝了。"
            return "retry"


def load_prompt(prompt_path, logger):
    """加载纯文本文件中的提示词"""
    try:
        with open(prompt_path, 'r', encoding='utf-8') as file:
            style_note = file.read()
        return style_note
    except Exception as e:
        logger.error(f"加载提示词文件时发生异常: {e}")
        return None


class ApplyStyle(Node):
    def prep(self, shared):
        """
        从共享数据中获取草稿
        """
        return shared["draft"], shared["logger"]

    def exec(self, inputs):
        """
        对文章应用特定风格
        """
        draft, logger = inputs
        print("draft:", draft)
        # 加载配置文件
        # 加载提示词文件
        prompt_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), os.getenv("PROMPT_FILE"))
        prompt_file = load_prompt(prompt_file_path, logger)
        if not prompt_file:
            logger.error("提示词文件未找到或加载失败")
            return {"action": "finish", "reason": "提示词文件未找到或加载失败"}

        # 将 draft 插入到 style_note 中
        prompt = prompt_file.format(draft=draft)

        # 调用 LLM 生成最终文章
        response, success = call_llm(prompt, logger)
        if not success:
            logger.error("LLM 响应失败，请检查你的响应格式。")
            return {"action": "finish", "reason": "LLM 响应失败"}
        return response

    def post(self, shared, prep_res, exec_res):
        """
        将最终文章存储在共享数据中
        """
        shared["final_article"] = exec_res
        hot_word_path = shared["hot_word_path"]
        hot_word = shared["hot_word"]
        hot_words_csv = os.path.join(os.path.dirname(hot_word_path), os.getenv("HOT_WORDS"))
        # 确保 hot_word_path 是有效的路径
        # 将 hot_word_path、hot_word 和 exec_res 写入 CSV 文件
        try:
            # 检查文件是否存在，如果不存在则创建文件并写入表头
            file_exists = os.path.isfile(hot_words_csv)
            data = []

            if file_exists:
                # 读取现有数据
                with open(hot_words_csv, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        if row['hot_word'] == hot_word:
                            # 如果 hot_word 存在，追加 final_article
                            row['final_article'] += "\n" + exec_res
                        data.append(row)

            # 添加新数据
            if not any(row['hot_word'] == hot_word for row in data):
                data.append({'hot_word': hot_word, 'final_article': exec_res})

            # 写入数据
            with open(hot_words_csv, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['hot_word', 'final_article']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            logger = shared["logger"]
            logger.info(f"数据已写入 CSV 文件: {hot_words_csv}")
        except Exception as e:
            logger = shared["logger"]
            logger.error(f"写入 CSV 文件时发生异常: {e}")
            return "final-article"

        return "final-article"


class EvaluateImage(Node):
    def prep(self, shared):
        """
        从共享数据中获取最终文章和热词路径
        """
        return shared["final_article"], shared["hot_word_path"], shared["logger"]

    def exec(self, inputs):
        """
        对文章应用特定风格
        """
        final_article, hot_word_path, logger = inputs
        prompt = f"""
        ## 上下文
        你是一个内容配图评估助手
        
        ## 操作空间
        请根据一下指标对内容的配图进行评估
        内容：{final_article}
        
        评分指标（每个指标1-10分）：
        - 相关性：图片是否与文章内容相关。
        - 吸引力：图片是否能吸引用户眼球。
        - 视觉效果：图片的色彩、构图和清晰度如何。
        - 情感共鸣：图片是否能引发观众的情感共鸣。

        ## 下一步操作
        请以下格式返回你的响应,无需其余信息：
        
        ```yaml
        total_score: <总分>
        relevance: <相关性-指标分数>
        attractiveness: <吸引力-指标分数>
        visual: <视觉效果-指标分数>
        emotional: <情感共鸣-指标分数>
        ```
        重要：请确保：
        1. 对所有多行字段使用适当的缩进（4个空格）
        2. 使用|字符表示多行文本字段
        3. 保持单行字段不使用|字符
        4. 正确使用YAML字符串格式
        """

        result_list = []
        images_list = get_images(hot_word_path)
        if len(images_list) > 8: #//只评估8张图片
            images_list = images_list[:8]
        for image_path in images_list:
            response = evaluate_image_relevance(prompt, image_path, logger)
            logger.info(f"LLM 响应: {response}")
            if "```yaml" not in response:
                logger.error("LLM 响应格式不正确，请检查你的响应格式。")
                return {"action": "finish", "reason": "LLM 响应格式不正确"}
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            decision = yaml.safe_load(yaml_str)

            if isinstance(decision, dict) and "total_score" in decision:
                # 提取总分并重命名图片
                total_score = decision["total_score"]
                image_name = os.path.basename(image_path)
                new_image_name = f"{total_score}_{image_name}"
                new_image_path = os.path.join(hot_word_path, new_image_name)
                try:
                    os.rename(image_path, new_image_path)
                    logger.info(f"图片已重命名为: {new_image_name}")
                except Exception as e:
                    logger.error(f"重命名图片时发生错误: {e}")
            result_list.append(decision)

        return result_list

    def post(self, shared, prep_res, exec_res):
        """
        将最终文章存储在共享数据中
        """
        shared["evaluate_image_result_list"] = exec_res
        return "default"
