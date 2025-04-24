import logging
from datetime import datetime
from colorlog import ColoredFormatter
import os

__all__ = ["get_logger"]
# 判断logs文件夹是否存在，不存在则创建
if not os.path.exists("../logs"):
    os.makedirs("../logs")


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
    return logger
