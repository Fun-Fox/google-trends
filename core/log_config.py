import logging
from datetime import datetime
from colorlog import ColoredFormatter
import os
import time

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
            file_path = os.path.join(log_dir, file)
            try:
                # 检查文件是否被占用
                if not os.path.exists(file_path) or os.access(file_path, os.W_OK):
                    # 尝试删除文件，最多重试3次
                    for attempt in range(3):
                        try:
                            os.remove(file_path)
                            logging.info(f"成功删除日志文件: {file_path}")
                            break
                        except PermissionError:
                            logging.warning(f"文件 {file_path} 被占用，尝试解锁...")
                            time.sleep(1)  # 等待1秒后重试
                        except Exception as e:
                            logging.error(f"删除日志文件 {file_path} 时发生错误: {e}")
                            break
                else:
                    logging.warning(f"文件 {file_path} 权限不足，无法删除。")
            except Exception as e:
                logging.error(f"处理日志文件 {file_path} 时发生错误: {e}")

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