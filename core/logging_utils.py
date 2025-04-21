import logging
import os
from logging.handlers import RotatingFileHandler

__all__ = ["setup_logger"]


# 自定义日志处理器，用于存储日志到内存
class LogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logs = []

    def emit(self, record):
        log_entry = self.format(record)
        self.logs.append(log_entry)


def setup_logger(log_file_path):
    logger = logging.getLogger()
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

    # 使用 RotatingFileHandler 实现日志回滚
    file_handler = RotatingFileHandler(log_file_path, maxBytes=1024 * 1024, backupCount=5, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 新增自定义日志处理器
    log_handler = LogHandler()
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

    return logger
