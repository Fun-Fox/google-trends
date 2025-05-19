import os
import paramiko
from dotenv import load_dotenv
from scp import SCPClient

load_dotenv()
def create_ssh_client():
    """创建 SSH 客户端连接"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(
            hostname=os.getenv('HEY_GEN_IP'),
            port=22,
            username="root",
            password="password",
            timeout=10  # 设置为10秒
        )
        return ssh
    except paramiko.ssh_exception.SSHException as e:
        print(f"SSH 连接失败: {e}")
        return None


def progress(filename, size, sent):
    """传输进度回调函数"""
    print(f"📊 正在传输: {filename} | {sent}/{size} 字节")


def remote_path_exists(ssh, remote_path):
    """检查远程路径是否存在"""
    stdin, stdout, stderr = ssh.exec_command(f'test -e "{remote_path}" && echo exists')
    return "exists" in stdout.read().decode()


def upload_files(local_paths, remote_dir, ssh=None):
    close_ssh = False
    if ssh is None:
        ssh = create_ssh_client()
        close_ssh = True
    try:
        with SCPClient(ssh.get_transport(), progress=progress) as scp:
            for path in local_paths:
                scp.put(path, remote_dir)
        print(f"✅ 已上传 {len(local_paths)} 个文件到 {remote_dir}")
    except Exception as e:
        print(f"❌ 批量上传失败: {e}")
    finally:
        if close_ssh:
            ssh.close()


def download_file(remote_path, local_path, ssh=None):
    """下载单个文件"""
    close_ssh = False
    if ssh is None:
        ssh = create_ssh_client()
        close_ssh = True
    try:
        with SCPClient(ssh.get_transport()) as scp:
            scp.get(remote_path, local_path)
        print(f"✅ 文件 {remote_path} 成功下载至 {local_path}")
    except Exception as e:
        print(f"❌ 文件下载失败: {e}")
    finally:
        if close_ssh:
            ssh.close()


def download_files(remote_path, local_path, ssh=None):
    """从远程目录下载所有文件到本地（递归）"""
    close_ssh = False
    if ssh is None:
        ssh = create_ssh_client()
        close_ssh = True
    try:
        with SCPClient(ssh.get_transport()) as scp:
            scp.get(remote_path, local_path, recursive=True)
        print(f"✅ 已从 {remote_path} 下载文件到 {local_path}")
    except Exception as e:
        print(f"❌ 文件下载失败: {e}")
    finally:
        if close_ssh:
            ssh.close()


if __name__ == "__main__":
    # 示例文件路径
    audio_file = "example/audio.wav"
    remote_audio_dir = ''
    remote_video_dir = ''
    local_download_dir = "downloads"

    os.makedirs(local_download_dir, exist_ok=True)

    # 创建 SSH 连接（复用）
    ssh = create_ssh_client()

    # 1. 测试上传音频文件
    if os.path.exists(audio_file):
        print("🎵 开始上传音频文件...")
        upload_files([audio_file], remote_audio_dir, ssh)
    else:
        print(f"⚠️ 音频文件不存在: {audio_file}")

    # 2. 测试下载视频文件
    print("🎬 开始下载远程视频文件...")
    if remote_path_exists(ssh, remote_video_dir):
        download_files(remote_video_dir, local_download_dir, ssh)
    else:
        print(f"⚠️ 远程目录不存在: {remote_video_dir}")

    # 3. 可选：单独下载某个文件
    test_remote_file = f"{remote_video_dir}/test.mp4"
    test_local_file = "downloads/test.mp4"
    if remote_path_exists(ssh, test_remote_file):
        download_file(test_remote_file, test_local_file, ssh)
    else:
        print(f"⚠️ 文件不存在: {test_remote_file}")

    ssh.close()
