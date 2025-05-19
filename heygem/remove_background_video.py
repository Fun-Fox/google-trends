import shutil

from backgroundremover.bg import remove
from PIL import Image
import cv2
import os
import glob
from moviepy import ImageSequenceClip


def remove_bg_pil(image: Image.Image, model_name="u2net"):
    """
    使用 backgroundremover 移除图像背景，返回 RGBA 格式的图像
    """
    import io
    img_data = io.BytesIO()
    image.save(img_data, format=image.format)
    result_bytes = remove(
        img_data.getvalue(),
        model_name=model_name,
        alpha_matting=True,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_structure_size=10,
        alpha_matting_base_size=1000
    )
    return Image.open(io.BytesIO(result_bytes)).convert("RGBA")


def extract_frames(video_path, output_dir, every_n_frame=1):
    """
    提取视频帧并保存为 PNG
    """
    cap = cv2.VideoCapture(video_path)
    os.makedirs(output_dir, exist_ok=True)

    frame_count = 0
    success, image = cap.read()

    while success:
        if frame_count % every_n_frame == 0:
            frame_path = os.path.join(output_dir, f"frame_{frame_count:05d}.png")
            cv2.imwrite(frame_path, image)
        success, image = cap.read()
        frame_count += 1

    cap.release()
    print(f"✅ 已提取 {frame_count} 帧到 {output_dir}")
    return frame_count


def process_frames(input_dir, output_dir, replace_background=False, bg_image=None):
    """
    处理每一帧图像：
    - 默认只去背景（保留透明通道）
    - 若 replace_background=True 并提供 bg_image，则替换背景
    """
    os.makedirs(output_dir, exist_ok=True)

    bg = None
    if replace_background and bg_image:
        bg = Image.open(bg_image).convert("RGBA")

    for src in glob.glob(os.path.join(input_dir, "*.png")):
        img = Image.open(src).convert("RGBA")
        fg = remove_bg_pil(img)

        if replace_background and bg:
            resized_bg = bg.resize(fg.size)
            combined = Image.alpha_composite(resized_bg, fg)
        else:
            combined = fg

        out_path = os.path.join(output_dir, os.path.basename(src))
        combined.save(out_path)  # 保留透明通道（PNG）

    print(f"✅ 所有帧已处理完成 -> {output_dir}")


def create_video_from_frames(frame_dir, output_video, fps=24, keep_audio=False):
    """
    将图片序列合成视频，并可选择保留原视频音频
    """
    frames = sorted(glob.glob(os.path.join(frame_dir, "*.png")))
    clip = ImageSequenceClip(frames, fps=fps)

    if keep_audio:
        from moviepy.editor import VideoFileClip
        original_clip = VideoFileClip(frame_dir)
        clip = clip.set_audio(original_clip.audio)

    clip.write_videofile(output_video, codec="libx264", audio_codec="aac", audio=keep_audio)
    print(f"✅ 视频已生成: {output_video}")


current_dir = os.path.dirname(__file__)


def remove_background(video_path,output_video, replace_background=False, new_bg_image=None, fps=24, keep_audio=True):
    # 临时目录
    frames_dir = os.path.join(current_dir,"frames")
    processed_dir = os.path.join(current_dir,"processed_frames")

    # Step 1: 提取帧
    extract_frames(video_path, frames_dir)

    # Step 2: 处理帧（去除/替换背景）
    process_frames(frames_dir, processed_dir, replace_background=replace_background, bg_image=new_bg_image)

    # Step 3: 合成视频
    create_video_from_frames(processed_dir, output_video, fps=fps, keep_audio=keep_audio)

    # 主流程中判断：
    if not args.keep_temp:
        for temp_dir in [frames_dir, processed_dir]:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"🗑️ 已清理临时目录: {temp_dir}")
    else:
        print("📌 临时文件已保留，请手动清理")


# =============================================
#           主程序入口（支持命令行调用）
# =============================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="视频背景去除/替换工具")
    parser.add_argument("video", help="输入视频文件路径")
    parser.add_argument("--bg", "--background", default=None, help="新背景图片路径（可选）")
    parser.add_argument("--output", "-o", default="output.mp4", help="输出视频路径")
    parser.add_argument("--no-bg-replace", action="store_true", help="关闭背景替换（仅去除背景）")
    parser.add_argument("--fps", type=int, default=24, help="输出视频帧率")
    parser.add_argument("--keep-audio", action="store_true", help="保留原始视频音频轨道")

    args = parser.parse_args()

    video_path = args.video
    new_bg_image = args.bg or None
    output_video = args.output
    replace_background = not args.no_bg_replace
    fps = args.fps
    keep_audio = args.keep_audio

    # 临时目录
    frames_dir = "frames"
    processed_dir = "processed_frames"

    # Step 1: 提取帧
    extract_frames(video_path, frames_dir)

    # Step 2: 处理帧（去除/替换背景）
    process_frames(frames_dir, processed_dir, replace_background=replace_background, bg_image=new_bg_image)

    # Step 3: 合成视频
    create_video_from_frames(processed_dir, output_video, fps=fps, keep_audio=keep_audio)
