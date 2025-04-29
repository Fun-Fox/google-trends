import os

from dotenv import load_dotenv
from pocketflow import Node
from agent.utils import call_llm
import yaml

__all__ = ["NoteStyle"]
load_dotenv()

def load_prompt(prompt_path, logger):
    """加载纯文本文件中的提示词"""
    try:
        with open(prompt_path, 'r', encoding='utf-8') as file:
            style_note = file.read()
        return style_note
    except Exception as e:
        logger.error(f"加载提示词文件时发生异常: {e}")
        return None


class NoteStyle(Node):
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
        logger.info(f"已拿到草稿内容{draft}\n,正在进行风格撰写")
        # 加载配置文件
        # 加载提示词文件
        prompt_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),'', os.getenv("PROMPT_FILE"))
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
        logger = shared["logger"]
        logger.info(f"风格撰写结果:\n {exec_res}")
        hot_word_path = shared["hot_word_path"]
        hot_word = shared["hot_word"]
        current_path = os.path.dirname(os.path.dirname(os.path.dirname(__name__)))
        hot_words_csv = os.path.join(current_path,os.path.dirname(hot_word_path), os.getenv("HOT_WORDS"))
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
                    fieldnames = reader.fieldnames
                    # 检查是否包含 'final_article' 列
                    # 检查是否包含 'final_article' 列
                    for row in reader:
                        if row['hot_word'] == hot_word:

                            # 如果 hot_word 存在，追加 final_article
                            row['final_article'] += "\n" + exec_res
                        data.append(row)
            else:
                # 如果文件不存在，创建文件并写入表头
                data.append({'hot_word': hot_word, 'final_article': exec_res})

            # 写入数据
            with open(hot_words_csv, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['hot_word', 'final_article']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"数据已写入 CSV 文件: {hot_words_csv}")
        except Exception as e:
            logger.error(f"写入 CSV 文件时发生异常: {e}")
            return "final-article"

        return "final-article"
