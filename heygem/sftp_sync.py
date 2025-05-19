
# sftp_sync.py
import os
import time
import paramiko
from scp import SCPClient


# 加载配置
from config import remote_sync as config

def create_ssh_client():
    """创建 SSH 客户端连接"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=config['server_ip'],
        username=config['username'],
        password=config['password']
    )
    return ssh

def upload_file(local_path, remote_path):
    """上传本地文件到远程目录"""
    try:
        ssh = create_ssh_client()
        with SCPClient(ssh.get_transport()) as scp:
            scp.put(local_path, remote_path)
        print(f"✅ 文件 {local_path} 成功上传至 {remote_path}")
    except Exception as e:
        print(f"❌ 文件上传失败: {e}")
    finally:
        ssh.close()

def download_files(remote_path, local_path):
    """从远程目录下载所有文件到本地"""
    try:
        ssh = create_ssh_client()
        with SCPClient(ssh.get_transport()) as scp:
            scp.get(remote_path, local_path, recursive=True)
        print(f"✅ 已从 {remote_path} 下载文件到 {local_path}")
    except Exception as e:
        print(f"❌ 文件下载失败: {e}")
    finally:
        ssh.close()

def make_audio(audio_file_path):
    """模拟音频生成后上传"""
    print("🎵 开始上传音频文件...")
    upload_file(audio_file_path, config['audio_remote_dir'])

def loop_pending(remote_video_dir, local_video_dir, interval_seconds=60):
    """定时检查并下载合成后的视频"""
    print("🎬 启动定时任务，开始轮询下载合成视频...")
    while True:
        download_files(remote_video_dir, local_video_dir)
        time.sleep(interval_seconds)

if __name__ == "__main__":
    # 示例调用
    audio_file = "example/audio.wav"
    if os.path.exists(audio_file):
        make_audio(audio_file)
    else:
        print(f"⚠️ 音频文件不存在: {audio_file}")

    # 启动定时下载任务（可注释掉以单独测试上传）
    loop_pending(config['video_remote_dir'], "downloads/videos", interval_seconds=30)