import os

__all__ =["get_images"]
def get_images(hot_word_folder):
    """
    获取图片列表
    :param task_folders:
    :param hot_word_folder: 热词文件夹名称
    :return: 图片列表
    """
    # 确保 hotword_folder 是字符串类型
    if isinstance(hot_word_folder, list) and hot_word_folder:
        hot_word_folder = hot_word_folder[0]
    elif not isinstance(hot_word_folder, str):
        return []

    image_dir = hot_word_folder
    if not os.path.exists(hot_word_folder):
        return []
    images = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith(('.jpg', '.png'))]
    return images