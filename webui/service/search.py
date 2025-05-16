import datetime
import os

from agent import hot_word_research_assistant
from core import get_logger
from webui.func.constant import task_root_dir


def research_all_hot_word(task_folders, language):
    agent_log_file_path = f"agent_{datetime.datetime.now().strftime('%Y年%m月%d日%H时%M分')}.log"

    agent_logger = get_logger(__name__, agent_log_file_path)

    task_dir = os.path.join(task_root_dir, task_folders)
    # 修改逻辑：只扫描 task_root_dir 下的一层目录
    hot_words_folders = [os.path.join(task_dir, d) for d in os.listdir(task_dir) if
                         os.path.isdir(os.path.join(task_dir, d))]

    result = []
    print(f"开始处理热词文件夹：{hot_words_folders}")
    for hot_words_folders_path in hot_words_folders:
        try:
            ret = hot_word_research_assistant(hot_words_folders_path, language, agent_logger)
        except Exception as e:
            print(f"正在处理热词：{hot_words_folders_path}发生异常，下一个热词")
            continue
        result.append(ret)
    return result


def research_hot_word(hot_words_folders_path, language):
    print(f"开始处理热词文件夹：{hot_words_folders_path},输出语言{language}")
    agent_log_file_path = f"agent_{datetime.datetime.now().strftime('%Y年%m月%d日%H时%M分')}.log"

    agent_logger = get_logger(__name__, agent_log_file_path)

    ret = hot_word_research_assistant(hot_words_folders_path, language, agent_logger)
    return ret
