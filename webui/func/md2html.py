# md2html.py
import os.path
import random

import markdown2
import sys
import io

from webui.func.constant import root_dir

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def md_to_html(md_text, background_image=None, custom_font=None):
    """
    将 Markdown 字符串转换为 HTML 字符串，并应用自定义样式
    :param md_text: Markdown 格式文本
    :param background_image: 背景图片路径（可选）
    :param custom_font: 自定义字体 URL 或路径（可选）
    :return: HTML 字符串
    """
    # 使用 markdown2 转换，启用常见扩展
    html = markdown2.markdown(
        md_text,
        extras=[
            "tables",  # 表格支持
            "fenced-code-blocks",  # 围栏代码块
            "code-friendly",  # 更友好的代码格式
            "footnotes",  # 脚注
            "cuddled-lists",  # 松散列表格式
            "metadata",  # 支持 YAML Front Matter 元数据
            "numbering",  # 自动编号标题
            "pyshell",  # Python shell 风格代码块
            "wiki-tables",  # Wiki 风格表格
            "task_list",  # 支持任务列表 [-] [x]
        ]
    )

    # 构建自定义 CSS
    css = """
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin: 0;
        padding: 0;
        min-height: 100vh;
        background-color: #f2f2f2;
        display: flex;
        justify-content: center;
        align-items: start;
        overflow-y: auto;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-size: cover;
    }

    .markdown-content {
        background-color: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        text-align: justify;
        animation: fadeIn 1.2s ease-in-out;
        color: #333;
        overflow-y: auto; /* 内容过长时允许内部滚动 */
        max-height: 90vh; /* 设置最大高度 */
        width: 800px; /* 固定宽度 */
        margin: 0 auto; /* 水平居中 */
        word-wrap: break-word; /* 自动换行 */
        overflow-x: hidden; /* 禁止横向滚动 */
    }
    /*  > 引用块（blockquotes）*/
    .markdown-content blockquote {
        font-size: 18px;      /* 比 h1 小一点 */
        font-weight: 500;     /* 不加粗 */
        color: #555;          /* 淡化文字颜色 */
        background-color: #f9f9f9; /* 浅灰色背景 */
        border-left: 4px solid #007BFF; /* 左边蓝色条 */
        padding: 16px 20px;
        margin: 20px 0;
        border-radius: 6px;
        box-shadow: inset 0 0 4px rgba(0, 0, 0, 0.03);
        font-style: italic;   /* 斜体，突出引用风格 */
    }
    
    /* 悬浮标题 */
    .markdown-content h1:first-of-type {
        position: sticky;
        top: -30px;
        background: white;
        padding-top: 10px;
        z-index: 999;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        border-left: 4px solid #007BFF;
        padding-left: 12px;
        margin-left: -12px;
    }
    
    /* 滚动条隐藏（桌面） */
    .markdown-content::-webkit-scrollbar {
        display: none;
    }

    /* 图片处理 */
    .markdown-content img {
        max-width: 100%;
        height: auto;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin: 20px 0;
    }
    
    
    /* 代码块美化 */
    .markdown-content code {
        background-color: #f8f8f8;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        color: #d63384;
    }

    .markdown-content pre {
        background-color: #f1f1f1;
        padding: 16px;
        border-radius: 8px;
        overflow-x: auto;
        white-space: pre-wrap;
        box-shadow: inset 0 0 4px rgba(0, 0, 0, 0.05);
        font-size: 15px;
        font-family: 'Courier New', monospace;
        color: #333;
    }
    
    /* 动画效果 */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* 表格样式 */
    .markdown-content table {
        border-collapse: collapse;
        width: 100%;
        margin: 20px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    .markdown-content th, .markdown-content td {
        text-align: left;
        padding: 12px;
        border-bottom: 1px solid #ddd;
    }
    
    .markdown-content tr:hover {
        background-color: #f5f5f5;
    }
    
    /* 引用样式 */
    .markdown-content blockquote {
        border-left: 4px solid #007bff;
        margin: 20px 0;
        padding: 10px 20px;
        background-color: #f9f9f9;
        font-style: italic;
        color: #555;
    }
    
    /* 列表样式增强 */
    .markdown-content ul, .markdown-content ol {
        padding-left: 20px;
    }
    
    .markdown-content li {
        margin: 6px 0;
    }
    
    /* 响应式设计 */
    @media (max-width: 820px) {
        .background-frame {
            width: calc(100% + 20px);
            max-width: 100%;
            padding: 15px;
        }
    
        .markdown-content {
            width: 100%;
            max-width: 100%;
            padding: 20px;
            font-size: 16px;
            line-height: 1.6;
        }
    
        .markdown-content h1 {
            font-size: 24px;
        }
    
        .markdown-content h2 {
            font-size: 20px;
        }
    
        .markdown-content img {
            border-radius: 8px;
        }
    }
    """

    # # 添加背景图片（如果提供）
    if background_image:
        css += f"""

        .background-frame {{
            width: calc(100% + 60px); /* 比内容区宽 40px */
            max-width: 860px;         /* 卡片宽 800px + 左右各 20px 边距 */
            margin: 0 auto;
            padding: 30px;
            # box-sizing: border-box;
            background-image: url("{background_image}");
            background-size: cover;
            background-position: center;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
        }}
        """

    # 添加自定义字体（如果提供）
    if custom_font:
        css += f"@import url('{custom_font}');\n"
        css += "body { font-family: 'YourCustomFont', sans-serif; }\n"

    # 完整 HTML 模板
    template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Markdown Poster</title>
    <style>
        {css}
    </style>
</head>
<body>
     <div class="background-frame">
        <div class="markdown-content">
            {html}
        </div>
    </div>
</body>
</html>
"""

    return template


def save_html(html_content, output_path):
    """保存 HTML 到指定路径"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 已生成 HTML 文件: {output_path}")


def convert_md_to_output(md_path, html_path, image_path=None, background_image=None, custom_font=None):
    """
    统一接口：将 Markdown 转为 HTML 并可选输出图像
    """
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        html_content = md_to_html(md_text, background_image, custom_font)

        # 输出 HTML
        save_html(html_content, html_path)

        # 输出图像（如果提供路径）
        if image_path:
            # html_to_image(html_content, image_path)
            pass

    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

def get_random_bg_image(bg_folder_path):
    """
    获取指定目录下的随机 .webp 图像文件路径
    :param bg_folder_path: 背景图文件夹路径
    :return: 随机选择的图片路径（相对于 Web 访问路径）
    """
    if not os.path.exists(bg_folder_path):
        print(f"⚠️ 背景图目录不存在: {bg_folder_path}")
        return None

    webp_files = [
        f for f in os.listdir(bg_folder_path)
        if f.lower().endswith(".webp")
    ]

    if not webp_files:
        print(f"⚠️ 背景图目录中未找到 .webp 文件")
        return None

    selected_file = random.choice(webp_files)
    full_path = os.path.join(bg_folder_path, selected_file)

    # 返回相对路径或用于 HTML 的 URL 路径（根据你项目结构决定）
    return full_path  # 或者返回 "/webui/bg/xxx.webp" 格式
if __name__ == "__main__":
    # 示例配置

    input_md_path = os.path.join(root_dir, "README.md")
    output_html = os.path.join(root_dir, "output.html")
    output_image = os.path.join(root_dir, "output.png")
    # 随机选择背景图
    bg_folder = os.path.join(root_dir, "webui", "bg")  # 本地磁盘路径
    bg_image_path = get_random_bg_image(bg_folder)
    if bg_image_path:
        bg_image_url = bg_image_path.replace(root_dir, "")  # 转为相对路径
        bg_image_url = bg_image_url.replace("\\", "/")
    else:
        bg_image_url = None
    font_url = "https://fonts.googleapis.com/css2?family=Roboto&display=swap"

    convert_md_to_output(
        md_path=input_md_path,
        html_path=output_html,
        image_path=output_image,
        background_image=bg_image_url,
        custom_font=font_url
    )
