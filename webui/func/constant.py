# 动态生成日志文件路径
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
task_root_dir = os.path.join(root_dir, os.getenv("TASK_DIR", "tasks"))