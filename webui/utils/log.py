import os
from webui.utils.constant import root_dir

# 新增函数：获取 logs 目录下时间戳最新的日志文件
def get_latest_log_file(log_dir, start_str="task_"):
    """
    获取最新的日志文件
    :return: 最新的日志文件路径
    """

    if not os.path.exists(log_dir):
        return None
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.log') and f.startswith(start_str)]
    if not log_files:
        return None
    latest_log = max(log_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
    return os.path.join(log_dir, latest_log)

# 更新 Gradio 接口中的日志读取逻辑
def update_task_log_textbox():
    """
    更新日志文本框内容
    :return: 日志内容
    """
    log_dir = os.path.join(root_dir, "logs")
    start_str = "task_"
    latest_log_file = get_latest_log_file(log_dir, start_str)
    if latest_log_file:
        with open(latest_log_file, 'r', encoding='utf-8-sig') as f:
            log_content = f.read()
        return log_content
    return "暂无日志文件"


# 更新 Gradio 接口中的日志读取逻辑
def update_agent_log_textbox():
    """
    更新日志文本框内容
    :return: 日志内容
    """
    log_dir = os.path.join(root_dir, "logs")
    start_str = "agent_"
    latest_log_file = get_latest_log_file(log_dir, start_str)
    if latest_log_file:
        with open(latest_log_file, 'r', encoding='utf-8-sig') as f:
            log_content = f.read()
        return log_content
    return "暂无日志文件"