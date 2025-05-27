# upload_image_to_notion.py
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client
from typing import Optional, List, Dict
from pyimgur import Imgur
import os
from PIL import Image

# 加载环境变量
load_dotenv()

# 初始化 Notion 客户端
notion = Client(auth=os.getenv("NOTION_API_KEY"))

# 支持的图像格式
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def is_supported_image_format(file_path: str) -> bool:
    ext = os.path.splitext(file_path)[1].lower()
    return ext in SUPPORTED_EXTENSIONS


def validate_and_convert_image(image_path: str) -> Optional[str]:
    """
    验证图片是否有效，并尝试转换为标准 JPG 格式。
    返回新路径，失败返回 None。
    """
    try:
        with Image.open(image_path) as img:
            ext = os.path.splitext(image_path)[1].lower()
            if img.format in ["JPEG", "PNG"] and ext == f".{img.format.lower()}":
                return image_path

            new_path = os.path.splitext(image_path)[0] + ".jpg"
            img.convert("RGB").save(new_path, "JPEG")
            print(f"🔁 图像已转换为标准 JPG 格式: {new_path}")
            return new_path
    except Exception as e:
        print(f"❌ 无法打开图像，请检查文件是否损坏: {e}")
        return None


def upload_image_to_imgur(image_path: str) -> Optional[str]:
    """
    将图片上传到 Imgur 并返回外链 URL
    """
    converted_path = validate_and_convert_image(image_path)
    if not converted_path:
        return None

    client_id = os.getenv("IMGUR_CLIENT_ID")
    try:
        im = Imgur(client_id=client_id)
        uploaded_image = im.upload_image(path=converted_path, title="Uploaded by Tool")
        return uploaded_image.link
    except Exception as e:
        print(f"❌ Imgur 上传失败: {e}")
        return None


def create_notion_page(database_id: str, title: str) -> Optional[Dict]:
    """创建空页面"""
    try:
        page = notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "title": {"title": [{"text": {"content": title}}]},
                "type": {"select": {"name": "Post"}},
                "category": {"select": {"name": "热点追踪"}},
                "status": {"select": {"name": "Draft"}},
                "create_time": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}}
            },
            children=[]
        )
        print(f"✅ create_notion_page 页面 '{title}' 创建成功，ID: {page['id']}")
        return page
    except Exception as e:
        print(f"❌ create_notion_page 页面创建失败: {e}")
        return None


def add_image_block_to_page(page_id: str, image_url: str):
    """在指定页面中添加图片块"""
    try:
        notion.blocks.children.append(
            block_id=page_id,
            children=[
                {
                    "object": "block",
                    "type": "image",
                    "image": {
                        "type": "external",
                        "external": {"url": image_url}
                    }
                }
            ]
        )
        print("🖼️ 图片已成功插入页面")
    except Exception as e:
        print(f"❌ 插入图片失败: {e}")


def upload_image_and_create_notion_page(database_id: str, title: str, image_path: str):
    # Step 1: 创建页面
    page = create_notion_page(database_id, title)
    if not page:
        return

    page_id = page["id"]

    # Step 2: 上传图片到 Imgur
    image_url = upload_image_to_imgur(image_path)
    if not image_url:
        print("❌ 图片上传失败")
        return

    # Step 3: 插入图片块到页面
    add_image_block_to_page(page_id, image_url)

    print(f"🎉 页面创建完成，访问地址: {page['url']}")
    return page


def extract_title(file_path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    """尝试从前5行中找到标题"""
    for line in lines[:5]:
        if line.strip().startswith("# "):
            return line.strip()[2:].strip()
    return "Untitled"


if __name__ == "__main__":
    # import argparse

    # parser = argparse.ArgumentParser(description="上传一张图片到 Notion 页面")
    # parser.add_argument("--database_id", required=True, help="Notion 数据库 ID")
    # parser.add_argument("--title", required=True, help="页面标题")
    # parser.add_argument("--image_path", required=True, help="本地图片路径")
    #
    # args = parser.parse_args()
    database_id = os.getenv("DATABASE_ID")
    # "c765b50a1c924967b7ad49461bb0ce27"
    md_file = r"D:\Code\google-trends\tasks\2025年05月21日19时20分_美国_所有分类\george wendt\md\george wendt_2025年05月21日19时30分.md"
    image_path = r"D:\Code\google-trends\tasks\2025年05月21日19时20分_美国_所有分类\george wendt\md\george wendt_2025年05月21日19时30分.png"
    title = extract_title(md_file)
    upload_image_and_create_notion_page(database_id, title, image_path)
