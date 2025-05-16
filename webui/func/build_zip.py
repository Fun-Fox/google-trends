import os
import zipfile
from webui.func.constant import root_dir

def zip_folder(folder_path, zip_path):
    """
    将文件夹打包为 .zip 文件
    :param folder_path: 文件夹路径
    :param zip_path: .zip 文件路径
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if os.path.isfile(folder_path):
            # 如果 folder_path 是文件，则直接添加到 ZIP 文件中
            file_name = os.path.basename(folder_path)
            zipf.write(folder_path, file_name)
        elif os.path.isdir(folder_path):
            # 如果 folder_path 是文件夹，则遍历文件夹并添加文件
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    cname = os.path.relpath(str(file_path), str(folder_path))
                    zipf.write(str(file_path), cname)
        else:
            raise ValueError(f"路径 {folder_path} 既不是文件也不是文件夹")


def download_folder(folder_paths):
    """
    将选中的文件夹打包为 .zip 文件并提供下载链接
    :param folder_paths: 选中的文件夹路径列表
    :return: .zip 文件路径
    """
    if not folder_paths:
        return None  # 用户未选择任何文件夹

    # 只处理第一个选中的文件夹
    folder_path = folder_paths[0]

    # 读取环境变量指定的目录
    zip_dir = os.getenv("ZIP_DIR")
    zip_path = os.path.join(root_dir, zip_dir, f"{os.path.basename(folder_path)}.zip")
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    zip_folder(folder_path, zip_path)
    return zip_path

def refresh_zip_files():
    """
    刷新 .zip 文件列表
    :return: 返回最新的 .zip 文件列表
    """
    zip_dir = os.getenv("ZIP_DIR", "zips")
    zip_path = os.path.join(root_dir, zip_dir)
    if not os.path.exists(zip_path):
        os.makedirs(zip_path, exist_ok=True)
    return [os.path.join(zip_path, f) for f in os.listdir(zip_path) if f.endswith('.zip')]
