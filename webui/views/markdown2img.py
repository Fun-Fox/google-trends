import os

from webui.func.constant import root_dir
from webui.service.md2html import get_random_bg_image, convert_md_to_output


def build_tab():
    # 示例配置

    input_md_path = os.path.join(root_dir, "README.md")
    output_html = os.path.join(root_dir, "output.html")
    output_image = os.path.join(root_dir, "output.png")
    # 随机选择背景图
    bg_folder = os.path.join(root_dir, "webui", "bg")  # 本地磁盘路径
    bg_image_path = get_random_bg_image(bg_folder)

    if bg_image_path:
        # bg_image_url = bg_image_path.replace(root_dir, "")  # 转为相对路径
        bg_image_url = bg_image_path.replace("\\", "/")
    else:
        bg_image_url = None
    print(f"随机选择的背景图路径: {bg_image_url}")
    font_url = "https://fonts.googleapis.com/css2?family=Roboto&display=swap"

    convert_md_to_output(
        md_path=input_md_path,
        html_path=output_html,
        image_path=output_image,
        background_image=bg_image_url,
        custom_font=font_url
    )