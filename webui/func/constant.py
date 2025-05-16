# 动态生成日志文件路径
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
task_root_dir = os.path.join(root_dir, os.getenv("TASK_DIR", "tasks"))
task_date = datetime.datetime.now().strftime("%Y年%m月%d日%H时%M分")
task_log_file_path = os.path.join(f"task_{task_date}.log")
os.makedirs(os.path.join(root_dir, "logs"), exist_ok=True)

