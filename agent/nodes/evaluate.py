import csv
import os
from time import sleep

from dotenv import load_dotenv
from pocketflow import Node
from agent.utils import get_images, call_llm
import yaml

load_dotenv()

__all__ = ["SupervisorNode", "EvaluateImage"]


# 监督节点
class SupervisorNode(Node):
    def prep(self, shared):
        """获取当前回答以进行评估。"""
        return shared["draft"], shared["logger"]

    def exec(self, inputs):
        """检查回答是否有效或无意义。"""
        draft, logger = inputs
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
        is_nonsense = any(marker in draft for marker in nonsense_markers)

        if is_nonsense:
            return {"valid": False, "reason": "回答似乎无意义或无帮助"}
        else:
            return {"valid": True, "reason": "回答似乎是合法的"}

    def post(self, shared, prep_res, exec_res):
        logger = shared["logger"]
        """决定是否接受回答或重新启动流程。"""
        if exec_res["valid"]:
            logger.info(f"监督员批准了回答: {exec_res['reason']}")
            hot_word_path = shared["hot_word_path"]
            hot_word = shared["hot_word"]
            relation_news = shared["relation_news"]
            search_history = shared["search_history"]
            highlights = shared['highlights']
            current_path = os.path.dirname(os.path.dirname(os.path.dirname(__name__)))
            hot_words_csv = os.path.join(current_path, os.path.dirname(hot_word_path), os.getenv("HOT_WORDS_FILE_NAME"))
            # 确保 hot_word_path 是有效的路径
            # 将 hot_word_path、hot_word 和 exec_res 写入 CSV 文件
            try:
                # 检查文件是否存在，如果不存在则创建文件并写入表头
                file_exists = os.path.isfile(hot_words_csv)
                data = []

                if file_exists:
                    # 读取现有数据
                    with open(hot_words_csv, 'r', newline='', encoding='utf-8-sig') as csvfile:
                        reader = csv.DictReader(csvfile)
                        # 检查是否包含 'final_article' 列
                        # 检查是否包含 'final_article' 列
                        for row in reader:
                            if row['hot_word'] == hot_word:
                                # 如果 hot_word 存在，追加 final_article
                                row_tmp = {
                                    "hot_word": row['hot_word'],
                                    'relation_news': row['relation_news'],
                                    'search_history': shared['search_history'],
                                    'chinese': shared['chinese'],
                                    'output': shared['output'],
                                    'highlights': shared['highlights'],
                                }
                            else:
                                row_tmp = {
                                    "hot_word": row['hot_word'],
                                    'relation_news': row['relation_news'],
                                    'search_history': row['search_history'],
                                    'chinese': row['chinese'],
                                    'output': row['output'],
                                    'highlights': row['highlights']
                                }
                            data.append(row_tmp)
                else:
                    # 如果文件不存在，创建文件并写入表头
                    data.append({'hot_word': hot_word, 'relation_news': relation_news, 'search_history': search_history,
                                 'highlights': highlights,
                                 'chinese': shared['chinese'], 'output': shared['output']})
                logger.info(f"====CSV保存数据：{data}===")

                # 写入数据
                with open(hot_words_csv, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    fieldnames = ['hot_word', 'relation_news', 'search_history', 'highlights', 'chinese', "output"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)

                logger.info(f"====热词新闻、搜索研究历史数据、草稿数据已写入 CSV 文件: {hot_words_csv}===")
            except Exception as e:
                logger.error(f"写入 CSV 文件时发生异常: {e}")
            return "approved"
        else:
            logger.info(f"监督员拒绝了回答: {exec_res['reason']}")
            # 清理错误的回答
            shared["answer"] = None
            # 添加关于被拒绝回答的注释
            context = shared.get("context", "")
            shared["context"] = context + "\n\n注意: 之前的回答尝试被监督员拒绝了。"

            return "retry"


class EvaluateImage(Node):
    def prep(self, shared):
        """
        从共享数据中获取最终文章和热词路径
        """
        return shared["draft"], shared["hot_word_path"], shared["logger"]

    def exec(self, inputs):
        """
        对文章应用特定风格
        """
        draft, hot_word_path, logger = inputs
        prompt = f"""
        ## 上下文
        你是一个内容配图评分助手

        ## 操作空间
        请根据以下指标对内容的配图进行评分
        内容：{draft}

        评分指标（每个指标1-10分 整数）：
        - 相关性：图片是否与文章内容相关。
        - 吸引力：图片是否能吸引用户眼球。
        - 视觉效果：图片的色彩、构图和清晰度如何。
        - 情感共鸣：图片是否能引发观众的情感共鸣。

        ## 下一步操作
         重要：请确保：
         严格以下格式返回你的响应,无需其余信息：
         每个值不为空，且每个字段都包含一个整数值。

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
        if len(images_list) > 8:  # //只评估8张图片
            images_list = images_list[:8]
        for image_path in images_list:
            sleep(5)
            response, success = call_llm(prompt, logger, image_path)
            if not success:
                logger.error("LLM 调用失败，请检查你的配置。")
                return {"action": "finish", "reason": "LLM 调用失败"}
            logger.info(f"LLM 响应: {response}")
            if "```yaml" not in response:
                logger.error("LLM 响应格式不正确，请检查你的响应格式。")
                return {"action": "finish", "reason": "LLM 响应格式不正确"}
            try:
                yaml_str = response.split("```yaml")[1].split("```")[0].strip()
                decision = yaml.safe_load(yaml_str)
            except Exception as e:
                logger.error(f"处理 LLM 响应时发生错误: {e}")
                continue

            if isinstance(decision, dict) and "total_score" in decision:
                # 提取总分并重命名图片
                try:
                    total_score = int(decision["total_score"])
                except ValueError:
                    logger.error(f"无法将 total_score 转换为整数: {decision['total_score']}")
                    continue
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
        logger = shared["logger"]
        logger.info(f"===图片评分已经完成===")
        return "default"


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(current_dir)
    hot_words_csv = os.path.join(current_dir, "tasks/2025年04月27日18时50分/hot_words.csv")
    hot_word = "will howard"
    exec_res = "222"
    # 创建代理流程
    try:
        # 检查文件是否存在，如果不存在则创建文件并写入表头
        file_exists = os.path.isfile(hot_words_csv)
        data = []

        if file_exists:
            # 读取现有数据
            with open(hot_words_csv, 'r', newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                fieldnames = reader.fieldnames
                # 检查是否包含 'final_article' 列
                # 检查是否包含 'final_article' 列
                if 'final_article' not in fieldnames:
                    # 如果缺少 'final_article' 列，创建新的 fieldnames
                    new_fieldnames = fieldnames + ['final_article']
                    for row in reader:
                        # 初始化 'final_article' 列为空字符串
                        row['final_article'] = ''
                        data.append(row)
                    fieldnames = new_fieldnames
                else:
                    # 如果包含 'final_article' 列，正常读取数据
                    for row in reader:
                        if row['hot_word'] == hot_word:
                            # 如果 hot_word 存在，追加 final_article
                            row['final_article'] += "\n" + exec_res
                        data.append(row)
        else:
            # 如果文件不存在，创建文件并写入表头
            fieldnames = ['hot_word', 'final_article']
            data.append({'hot_word': hot_word, 'final_article': exec_res})

        # 写入数据
        with open(hot_words_csv, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['hot_word', 'final_article']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        print(f"数据已写入 CSV 文件: {hot_words_csv}")
    except Exception as e:
        print(f"写入 CSV 文件时发生异常: {e}")
