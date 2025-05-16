import logging
from colorlog import ColoredFormatter
import os
import time

from dotenv import load_dotenv

from webui.func.constant import root_dir

load_dotenv()
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
                            print(f"文件 {file_path} 被占用，尝试解锁...")
                            time.sleep(1)  # 等待1秒后重试
                        except Exception as e:
                            print(f"删除日志文件 {file_path} 时发生错误: {e},跳出")
                else:
                    print(f"文件 {file_path} 权限不足，无法删除。")
                    continue
            except Exception as e:
                print(f"处理日志文件 {file_path} 时发生错误: {e}")
                continue


def get_logger(name=__name__, log_file_path=''):
    # 在每次创建日志文件后调用管理函数
    logger = logging.getLogger(name)

        # 配置日志
    formatter = ColoredFormatter(
        "%(asctime)s - %(levelname)s - %(message)s",
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

    # 创建文件处理器
    file_handler = logging.FileHandler(os.path.join(root_dir, "logs", log_file_path), encoding='utf-8-sig')
    # if os.getenv("PLATFORM") == "local":
    #     file_handler.setFormatter(formatter)
    # 配置日志记录器
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # 创建控制台处理器
    # if os.getenv("PLATFORM") =="local":
    #
    #     console_handler = logging.StreamHandler()
    #     console_handler.setFormatter(formatter)
    #     logger.addHandler(console_handler)

    # 检查日志文件数量
    manage_log_files("logs")

    return logger
