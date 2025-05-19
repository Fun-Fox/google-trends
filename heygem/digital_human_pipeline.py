# 主流程
import os

from heygem.easy_submit import call_easy_submit, query_easy_status
from heygem.remove_background_video import remove_background
from heygem.sftp_sync import create_ssh_client, upload_files, remote_path_exists, download_file

'''
## .video与audio存储位置

将video 和audio放到容器code/data/temp目录下，或者宿主机D:\heygem_data\\face2face\\temp目录下

## 从视频文件中提取并复制视频流（不包含音频）

ffmpeg -loglevel warning -i /code/data/temp/女主播.mp4 -crf 15 \
-vcodec copy -an -y /code/data/temp/eb11d2c2-480e-4877-b099-65ae8904bef6_format.mp4

## 将一个音频文件转换为指定格式（单声道、16kHz 采样率、PCM 16-bit 小端格式），用于后续处理（如语音识别、数字人合成等）。

ffmpeg -loglevel warning -i /code/data/temp/热点词_カローラツーリング_口播稿ID_[1]_角色_甲_2025年05月19日13时00分56秒.wav -ac 1 -ar \
16000 -acodec pcm_s16le -y /code/data/temp/eb11d2c2-480e-4877-b099-65ae8904bef6_format.wav

## 创建视频帧队列
## 使用下面的进行视频和语言的合成

       ffmpeg -loglevel warning -y \
 -i "热点词_カローラツーリング_口播稿ID_[1]_角色_甲_2025年05月19日13时00分56秒.wav" \
 -i "eb11d2c2-480e-4877-b099-65ae8904bef6-t.mp4" \
 -c:v libx264 -crf 18 \
 -c:a libmp3lame \
 -vsync 2 -async 1 \
 "eb11d2c2-480e-4877-b099-65ae8904bef6-r.mp4"
 
## 任务最终合成结果为/code/data/temp {code}-r.mp4

 {'code': 10000, 'data': {'code': 'eb11d2c2-480e-4877-b099-65ae8904bef6', 'msg': '任务完成', 'progress': 100, 'result': '/eb11d2c2-480e-4877-b099-65ae8904bef6-r.mp4', 'status': 2}, 'msg': '', 'success': True}

'''


def digital_human_pipeline(audio_url, video_url, hot_word_path):
    code = os.path.splitext(audio_url)[0]

    # 创建 SSH 连接（复用）
    ssh = create_ssh_client()
    remote_dir = "code/data/temp"

    # 1. 测试上传音频文件
    if os.path.exists(audio_url) or os.path.exists(video_url):
        print("🎵 开始上传参考视频以及合成音频文件...")
        upload_files([audio_url, video_url], remote_dir, ssh)
    else:
        print(f"⚠️ 合成音频或参考视频文件不存在: {audio_url}、{video_url}")

    call_easy_submit(audio_url, video_url, code)

    result = query_easy_status(code)
    print("🎉 合成结果:", result)

    remote_file = f"{code}-r.mp4"
    os.makedirs(f"{hot_word_path}/video", exist_ok=True)
    if remote_path_exists(ssh, remote_file):
        download_file(f"{remote_dir}/{remote_file}", f"{hot_word_path}/video/{remote_file}", ssh)
    else:
        print(f"⚠️ 文件不存在: {remote_file}")

    video_path = f"{hot_word_path}/video/{remote_file}"
    if os.path.exists(video_path):
        print(f"🎉 合成视频文件已存在,开始抠像: {video_path}")
        output_video = f"{hot_word_path}/video/已抠像_{remote_file}"
        remove_background(video_path, output_video, replace_background=False, new_bg_image=None, fps=24,
                          keep_audio=True)


if __name__ == "__main__":
    try:
        # code = str(uuid.uuid4())
        # # 调用音频数字人合成接口
        # submit_result = call_easy_submit(
        #     audio_url="热点词_カローラツーリング_口播稿ID_[1]_角色_甲_2025年05月19日13时00分56秒.wav",
        #     video_url="女主播.mp4",
        #     code=code  # 替换为实际的唯一 key
        # )
        # print("Submit Result:", submit_result)

        # 查询状态
        query_easy_status("eb11d2c2-480e-4877-b099-65ae8904bef6")
        # 第 1 次查询结果: {'code': 10000, 'data': {'code': 'eb11d2c2-480e-4877-b099-65ae8904bef6', 'msg': '任务完成', 'progress': 100, 'result': '/eb11d2c2-480e-4877-b099-65ae8904bef6-r.mp4', 'status': 2}, 'msg': '', 'success': True}

    except Exception as e:
        print(f"Error: {e}")
