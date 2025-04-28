import logging
from datetime import datetime
from colorlog import ColoredFormatter
import os

__all__ = ["get_logger"]
# 判断logs文件夹是否存在，不存在则创建
if not os.path.exists("../logs"):
    os.makedirs("../logs")

# 新增函数：管理日志文件数量
def manage_log_files(log_dir, max_files=3):
    """
    管理日志文件数量，确保不超过指定的最大文件数
    :param log_dir: 日志目录
    :param max_files: 最大文件数
    """
    if not os.path.exists(log_dir):
        return
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
    if len(log_files) > max_files:
        log_files.sort(key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
        for file in log_files[:-max_files]:
            os.remove(os.path.join(log_dir, file))

def get_logger(name=__name__, log_file_path=''):
    logger = logging.getLogger(name)

    # 配置日志
    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler(os.path.join("logs", log_file_path), encoding='utf-8'),
            handler  # 使用带颜色的控制台日志输出
        ],
    )
    
    # 在每次创建日志文件后调用管理函数
    manage_log_files("logs")
    
    return logger