import os
import time
import asyncio
import threading
import schedule
import gradio as gr

from webui.func.conf import load_regions_choices
from webui.func.log import update_agent_log_textbox, update_task_log_textbox
from webui.service.crawler import run_crawler
from webui.service.search import research_all_hot_word



def get_latest_task_folder():
    """获取 tasks 目录下最新的文件夹"""
    task_root = os.getenv("TASK_ROOT_DIR", "tasks")
    folders = [os.path.join(task_root, f) for f in os.listdir(task_root)
               if os.path.isdir(os.path.join(task_root, f))]
    if not folders:
        return None
    latest = max(folders, key=os.path.getmtime)
    return os.path.basename(latest)

def find_mp4_files(directory):
    """
    递归扫描指定目录下的所有 .mp4 文件
    :param directory: 要搜索的根目录
    :return: 包含所有 .mp4 文件路径的列表
    """
    mp4_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith("_p.mp4"):
                mp4_files.append(os.path.join(root, file))
    return mp4_files

from moviepy import VideoFileClip, concatenate_videoclips

def merge_videos(video_paths, output_path):
    """
    拼接多个视频并保存为一个新文件
    :param video_paths: 视频文件路径列表
    :param output_path: 输出文件路径（包括文件名）
    """
    if not video_paths:
        print("⚠️ 没有找到可拼接的视频文件")
        return None

    clips = [VideoFileClip(v) for v in video_paths]
    final_clip = concatenate_videoclips(clips, method="compose")

    # 写入最终视频
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    final_clip.close()

    print(f"🎥 视频已成功合并至：{output_path}")
    return output_path

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
        task_dir = os.path.join(os.getenv("TASK_ROOT_DIR", "tasks"), latest_folder)

        print(f"📁 开始任务深度搜索: {latest_folder}")
        # 执行热词研究
        research_all_hot_word(latest_folder, language)
        print(f"📁 结束任务深度搜索+: {latest_folder}")

        # 新增：整合 MP4 文件
        print(f"📼 正在扫描 {task_dir} 中的 MP4 文件...")
        mp4_files = find_mp4_files(task_dir)

        if mp4_files:
            output_video = os.path.join(task_dir, f"{latest_folder}_merged.mp4")
            merged_result = merge_videos(mp4_files, output_video)
            if merged_result:
                print(f"✅ 视频已成功合并到 {merged_result}")
            else:
                print("❌ 视频合并失败")
        else:
            print("ℹ️ 未发现任何 MP4 文件，跳过合并步骤")

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

_SCHEDULE_STARTED = False
# ========== 设置定时任务 ==========
# ========== 设置定时任务 ==========
def set_scheduled_task(run_time, to_download_image, origin, category, nums, language="简体中文"):
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
# ========== 修改 stop_scheduled_task 函数 ==========
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
            lang_dropdown = gr.Dropdown(label="选择语言",  choices=["简体中文", "繁体中文", "英文", "日文", "韩文", "俄文"],
                value="简体中文")
            set_button = gr.Button("设置定时任务")
            stop_button = gr.Button("停止定时任务", variant="secondary")
        with gr.Column():
            output_text = gr.Textbox(label="状态输出")
            gr.Textbox(label="采集日志", value=update_task_log_textbox, lines=10, max_lines=15,
                       every=5)
            gr.Textbox(label="深度搜索-执行记录", value=update_agent_log_textbox, lines=9,
                       max_lines=15,
                       every=5)

    set_button.click(fn=set_scheduled_task,
                     inputs=[time_input, to_download_image, origin, category, nums, lang_dropdown],
                     outputs=output_text)

    stop_button.click(fn=stop_scheduled_task,
                      inputs=[],
                      outputs=output_text)


# 启动后台定时器
run_schedule_in_background()
