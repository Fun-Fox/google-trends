# utils/ui_utils.py
#
import os

from dotenv import load_dotenv

from webui.utils.constant import root_dir

load_dotenv()

def read_cookie(status_text):
    # 加载 .env 文件中的 COOKIE_STRING 并回显
    initial_cookie = ""
    try:

        initial_cookie = os.getenv('COOKIE_STRING', '')

    except Exception as e:
        status_text.value = f"加载 COOKIE_STRING 失败: {e}"
    return initial_cookie


def save_cookie(cookie_str):
    try:
        # 读取现有 .env 文件内容
        with open(os.path.join(root_dir, ".env"), "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 写入时过滤掉旧的 COOKIE_STRING 行，并在最后插入新的
        with open(os.path.join(root_dir, ".env"), "w", encoding="utf-8") as f:
            for line in lines:
                if not line.startswith("COOKIE_STRING="):
                    f.write(line)
            # 写入新的 COOKIE_STRING
            f.write(f'COOKIE_STRING="{cookie_str}"\n')

        return "COOKIE_STRING 已成功保存"
    except Exception as e:
        return f"保存 COOKIE_STRING 失败: {e}"
