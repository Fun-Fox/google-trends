import os
import time
import asyncio
import threading
import schedule
import gradio as gr

from webui.func.conf import load_regions_choices
from webui.service.crawler import run_crawler
from webui.service.search import research_all_hot_word

# ========== 新增全局变量 ==========
_SCHEDULE_STARTED = False  # 标记是否已启动定时任务


def get_latest_task_folder():
    """获取 tasks 目录下最新的文件夹"""
    task_root = os.getenv("TASK_ROOT_DIR", "tasks")
    folders = [os.path.join(task_root, f) for f in os.listdir(task_root)
               if os.path.isdir(os.path.join(task_root, f))]
    if not folders:
        return None
    latest = max(folders, key=os.path.getmtime)
    return os.path.basename(latest)


async def scheduled_task(to_download_image, origin, category, nums, language="zh"):
    """
    定时执行的任务，接收用户输入参数
    """
    print("⏰ 开始执行定时任务...")

    # 执行爬虫任务
    result = await run_crawler(to_download_image=to_download_image,
                               origin=origin,
                               category=category,
                               nums=nums)
    print(f"✅ 爬虫执行完成: {result}")

    # 获取最新任务文件夹
    latest_folder = get_latest_task_folder()
    if latest_folder:
        print(f"📁 最新任务文件夹: {latest_folder}")
        # 执行热词研究
        research_all_hot_word(latest_folder, language)
    else:
        print("⚠️ 未找到任务文件夹")


# ========== 后台调度器线程 ==========
def run_schedule_in_background():
    """启动后台定时任务线程"""
    def run_schedule():
        while getattr(run_schedule_in_background, "is_running", True):
            schedule.run_pending()
            time.sleep(1)

    setattr(run_schedule_in_background, "is_running", True)
    thread = threading.Thread(target=run_schedule)
    thread.daemon = True
    thread.start()


# ========== 设置定时任务 ==========
def set_scheduled_task(run_time, to_download_image, origin, category, nums, language="zh"):
    global _SCHEDULE_STARTED
    try:
        # 清除已有任务
        schedule.clear()

        # 构建带参数的异步任务
        job_func = lambda: asyncio.run(
            scheduled_task(to_download_image, origin, category, nums, language)
        )

        # 设置每日定时任务
        schedule.every().day.at(run_time).do(job_func)
        _SCHEDULE_STARTED = True

        return f"✅ 定时任务已设定于每天 {run_time} 执行"
    except Exception as e:
        return f"❌ 设置定时任务失败: {e}"


# ========== 停止定时任务 ==========
def stop_scheduled_task():
    global _SCHEDULE_STARTED
    try:
        # 清除所有定时任务
        schedule.clear()
        setattr(run_schedule_in_background, "is_running", False)
        _SCHEDULE_STARTED = False
        return "⏹️ 定时任务已停止"
    except Exception as e:
        return f"❌ 停止定时任务失败: {e}"


# ===== 新增 Gradio UI 组件 =====
def build_tab():
    gr.Markdown("## ⏰ 设置定时任务（每日执行）")

    with gr.Row():
        with gr.Column():
            # 复用 trend_crawler 中的控件
            to_download_image = gr.Checkbox(label="下载Google Trends上的三张图片", value=False)
            choices_data = load_regions_choices()
            origin = gr.Dropdown(label="地区", choices=list(choices_data['regions'].keys()), value="美国")
            category = gr.Dropdown(label="分类", choices=list(choices_data['category_names'].keys()),
                                   value="所有分类")
            nums = gr.Slider(minimum=1, maximum=25, step=1, label="热词采集数量（最大25）", value=25)
            time_input = gr.Textbox(label="请输入执行时间（格式：HH:MM）", value="08:00")
            lang_dropdown = gr.Dropdown(label="选择语言", choices=["zh", "en"], value="zh")
            set_button = gr.Button("设置定时任务")
            stop_button = gr.Button("停止定时任务", variant="secondary")
        output_text = gr.Textbox(label="状态输出")

    set_button.click(fn=set_scheduled_task,
                     inputs=[time_input, to_download_image, origin, category, nums, lang_dropdown],
                     outputs=output_text)

    stop_button.click(fn=stop_scheduled_task,
                      inputs=[],
                      outputs=output_text)

# 启动后台定时器
run_schedule_in_background()
