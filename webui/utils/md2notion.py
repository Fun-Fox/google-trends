from datetime import datetime

from dotenv import load_dotenv
from notion_client import Client
from typing import Tuple, List, Optional
from pyimgur import Imgur
import os
import requests

load_dotenv()

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def is_supported_image_format(file_path: str) -> bool:
    ext = os.path.splitext(file_path)[1].lower()
    return ext in SUPPORTED_EXTENSIONS


from PIL import Image
import io
import os


def validate_and_convert_image(image_path: str) -> Optional[str]:
    """
    使用 Pillow 验证图片是否为有效图像，并尝试转换为标准 JPG/PNG 格式。
    返回新的图片路径，失败返回 None。
    """
    try:
        with Image.open(image_path) as img:
            # 如果成功打开，则为有效图像
            print(f"✅ 图像已成功打开: {image_path}")

            # 如果已经是 JPEG 或 PNG 并且后缀正确，直接返回原路径
            ext = os.path.splitext(image_path)[1].lower()
            if img.format in ["JPEG", "PNG"] and ext == f".{img.format.lower()}":
                return image_path

            # 否则统一转为 .jpg
            new_path = os.path.splitext(image_path)[0] + ".jpg"
            img = img.convert("RGB")  # 确保为 RGB 模式
            img.save(new_path, "JPEG")
            print(f"🔁 图像已转换为标准 JPG 格式: {new_path}")
            return new_path
    except Exception as e:
        print(f"❌ 无法打开图像，请检查文件是否损坏: {e}")
        return None


def upload_image_to_imgur(image_path: str, client_id: str) -> Optional[str]:
    """
    将本地图片上传到 Imgur 并返回图片 URL
    """
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return None

    # 检查文件格式是否支持
    if not is_supported_image_format(image_path):
        print(f"Unsupported image format: {image_path}")
        return None

    # 验证并转换图片格式
    converted_path = validate_and_convert_image(image_path)
    if not converted_path:
        return None

    print(f"🖼️ 正在上传图片到 Imgur: {converted_path}")

    try:
        im = Imgur(client_id=client_id)
        uploaded_image = im.upload_image(path=converted_path, title="Uploaded by Notion Tool")
        return uploaded_image.link  # 返回图片外链地址
    except Exception as e:
        print(f"❌ Imgur upload failed: {e}")
        return None



def upload_local_image_to_notion(image_path: str, parent_page_id: str, notion_token: str) -> Optional[str]:
    """
    将本地图片上传到 Notion，并返回可访问的 secure_url
    """
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return None

    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28"
    }

    # 自动识别 MIME 类型
    mime_type = "image/jpeg" if image_path.lower().endswith((".jpg", ".jpeg")) else \
        "image/png" if image_path.lower().endswith(".png") else "application/octet-stream"

    payload = {
        "caption": "",
        "parent_page_id": parent_page_id
    }

    with open(image_path, "rb") as f:
        files = {
            "file": (os.path.basename(image_path), f, mime_type)
        }
        response = requests.post(
            "https://api.notion.com/v1/upload",
            headers=headers,
            data=payload,
            files=files
        )

    if response.status_code == 200:
        return response.json()["secure_url"]
    else:
        print(f"Upload failed: {response.status_code} - {response.text}")
        return None


class MarkdownProcessor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.title = "Untitled"
        self.body_blocks: List[dict] = []
        self.notion_token = os.getenv("NOTION_API_KEY") or "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"

    def parse(self) -> Tuple[str, List[dict]]:
        """仅解析 Markdown 标题和内容块，不上传图片"""
        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        self.title = self._extract_title(lines)
        self.body_blocks = self._parse_content_blocks_without_upload(lines)

        return self.title, self.body_blocks

    def parse_with_upload(self, page_id: str) -> Tuple[str, List[dict]]:
        """解析 Markdown 文件，并上传本地图片"""
        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        self.title = self._extract_title(lines)
        self.body_blocks = self._parse_content_blocks_with_upload(lines, page_id)

        return self.title, self.body_blocks

    def _extract_title(self, lines: list) -> str:
        """尝试从前5行中找到标题"""
        for line in lines[:5]:
            if line.strip().startswith("# "):
                return line.strip()[2:].strip()
        return "Untitled"

    def _parse_content_blocks_without_upload(self, lines: list) -> List[dict]:
        """解析正文内容为多个 Notion block，不处理图片上传"""
        content_lines = [line.rstrip('\n') for line in lines]
        body_blocks = []

        # 移除标题行
        try:
            title_index = next(i for i, line in enumerate(content_lines) if line.startswith("# "))
            content_lines.pop(title_index)
        except StopIteration:
            pass

        while content_lines:
            line = content_lines[0]

            # 处理图片行（忽略上传）
            if line.strip().startswith("!["):
                url = line.split("(", 1)[1].split(")", 1)[0].strip()
                body_blocks.append({
                    "object": "block",
                    "type": "image",
                    "image": {
                        "type": "external",
                        "external": {"url": url}
                    }
                })
                content_lines.pop(0)
                continue

            # 默认作为段落处理
            paragraph_text = ""
            while content_lines and not content_lines[0].strip().startswith("!["):
                paragraph_text += content_lines.pop(0) + "\n"

            if paragraph_text.strip():
                body_blocks.append(self._create_paragraph_block(paragraph_text))

        return body_blocks

    def _parse_content_blocks_with_upload(self, lines: list, page_id: str) -> List[dict]:
        """解析正文内容为多个 Notion block，支持本地图片上传"""
        content_lines = [line.rstrip('\n') for line in lines]
        body_blocks = []

        # 移除标题行
        try:
            title_index = next(i for i, line in enumerate(content_lines) if line.startswith("# "))
            content_lines.pop(title_index)
        except StopIteration:
            pass

        while content_lines:
            line = content_lines[0]

            # 处理图片行
            if line.strip().startswith("!["):
                image_block = self._parse_and_upload_image_line(content_lines.pop(0), page_id)
                if image_block:
                    body_blocks.append(image_block)
                continue

            # 默认作为段落处理
            paragraph_text = ""
            while content_lines and not content_lines[0].strip().startswith("!["):
                paragraph_text += content_lines.pop(0) + "\n"

            if paragraph_text.strip():
                body_blocks.append(self._create_paragraph_block(paragraph_text))

        return body_blocks

    def _parse_and_upload_image_line(self, line: str, page_id: str) -> Optional[dict]:
        """解析类似 ![alt](url_or_local_path) 的图片行，并自动上传本地图片"""
        if "(" in line and ")" in line:
            try:
                path_or_url = line.split("(", 1)[1].split(")", 1)[0].strip()

                # 如果是本地路径，则上传
                if '../' in path_or_url:
                    path_or_url = os.path.join(os.path.dirname(os.path.dirname(self.file_path)),
                                               os.path.basename(path_or_url))
                    print(f"当前图片地址：{path_or_url}")

                if os.path.exists(path_or_url):
                    # 使用 Imgur 上传图片
                    imgur_client_id = os.getenv("IMGUR_CLIENT_ID")  # 替换为你自己的 Client ID
                    url = upload_image_to_imgur(path_or_url, imgur_client_id)

                    if not url:
                        return None
                else:
                    url = path_or_url  # 外链直接使用

                return {
                    "object": "block",
                    "type": "image",
                    "image": {
                        "type": "external",
                        "external": {"url": url}
                    }
                }
            except Exception as e:
                print(f"Error parsing image line: {e}")
        return None

    @staticmethod
    def _create_paragraph_block(text: str) -> dict:
        """创建段落 block"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "text": {"content": text.strip()}
                }]
            }
        }


# 初始化 Notion 客户端
notion = Client(
    client=None,
    auth=os.getenv("NOTION_API_KEY")
)


def create_notion_page(database_id: str, title: str, body_blocks: List[dict]) -> Optional[dict]:
    """在指定数据库中创建新页面，并插入多个 block"""
    try:
        page = notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "title": {"title": [{"text": {"content": title}}]},
                "type": {"select": {"name": "Post"}},
                "category": {"select": {"name": "热点追踪"}},
                "status": {"select": {"name": "Draft"}},
                "create_time": {"date": {"start": datetime.now().isoformat()}}
            },
            children=body_blocks
        )
        return page
    except Exception as e:
        print(f"Error creating Notion page: {e}")
        return None


def create_page_from_markdown(database_id: str, file_path: str) -> Optional[dict]:
    """
    从指定的 Markdown 文件创建 Notion 页面，并自动上传本地图片。

    参数:
        database_id (str): Notion 数据库 ID
        file_path (str): Markdown 文件路径

    返回:
        Optional[dict]: 创建成功的页面对象（包含 page['url']），失败则返回 None
    """
    # 初始化 Markdown 处理器
    processor = MarkdownProcessor(file_path)

    # Step 1: 解析 Markdown 获取标题（不处理图片）
    title, _ = processor.parse()

    # Step 2: 在数据库中创建一个空页面
    print(f"正在使用标题 '{title}' 创建新页面...")
    page = create_notion_page(database_id, title, [])

    if not page:
        print("❌ 页面创建失败")
        return None

    page_id = page["id"]
    print(f"✅ 页面已创建，ID: {page_id}")

    # Step 3: 解析 Markdown 并上传本地图片
    print("🔄 正在解析内容并上传本地图片...")
    _, body_blocks = processor.parse_with_upload(page_id)

    # Step 4: 将解析后的内容（包括图片）插入到页面中
    print("📦 正在将内容插入到 Notion 页面中...")
    notion.blocks.children.append(block_id=page_id, children=body_blocks)

    print(f"🎉 页面创建成功！访问地址: {page['url']}")
    return page


if __name__ == "__main__":
    db_id = "c765b50a1c924967b7ad49461bb0ce27"
    md_file = "D:\\Code\\google-trends\\tasks\\2025年05月21日19时20分_美国_所有分类\\george wendt\\md\\george wendt_2025年05月21日19时30分.md"

    result_page = create_page_from_markdown(db_id, md_file)
    if result_page:
        print("页面 URL:", result_page["url"])
    else:
        print("页面创建失败。")
