import asyncio
import base64
import random
import re
from PIL import Image
import markdown2

from moviepy import *
import os
from playwright.async_api import async_playwright
from webui.utils.constant import root_dir


def rewrite_images(html_content, md_path):
    """
    将 HTML 内容中的 <img> 标签替换为 Base64 数据
    :param html_content: HTML 字符串
    :param base_dir: 本地图片基础目录（用于解析相对路径）
    :return: 新的 HTML 内容
    """

    def replace_img(match, md_path):
        src = match.group(1)
        # 相对路径转为绝对路径
        # print(f"md文件路径：{md_path},图片路径:{src}")
        if '../' in src:
            full_path = os.path.join(os.path.dirname(os.path.dirname(md_path)), src.split("../")[1]).replace("\\", "/")
            print(f'开始替换md中的相对图片地址为绝对图片地址:{full_path}')
        else:
            full_path = os.path.join(root_dir, src).replace("\\", "/")
        # print(f"图片全路径:{full_path}")
        if not os.path.exists(full_path):
            print(f"图片路径不存在：{full_path}")
        # print(full_path)
        new_src = get_image_as_base64(full_path)

        return f'<img src="{new_src}" alt="Embedded Image" style="max-width:100%; height:auto; border-radius:10px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); margin: 20px 0;">'

    # 正则匹配 <img> 标签中的 src 属性
    # img_pattern = r'<img.*?src="(.*?)".*?>'
    img_pattern = r'<img\b[^>]*?src="([^"]+)"[^>]*>'
    print(f"开始替换md中的图片地址为Base64")
    rewritten_html = re.sub(img_pattern, lambda m: replace_img(m, md_path), html_content)

    return rewritten_html


def get_random_bgm(bgm_folder_path):
    """
    获取指定目录下的随机音频文件（.mp3/.ogg）的 Base64 数据 URI
    :param bgm_folder_path: 背景音乐文件夹路径
    :return: Base64 数据 URI 字符串
    """
    if not os.path.exists(bgm_folder_path):
        print(f"⚠️ 背景音乐目录不存在: {bgm_folder_path}")
        return None

    audio_files = [
        f for f in os.listdir(bgm_folder_path)
        if f.lower().endswith((".mp3", ".ogg"))
    ]

    if not audio_files:
        print(f"⚠️ 背景音乐目录中未找到音频文件")
        return None

    selected_file = random.choice(audio_files)
    full_path = os.path.join(bgm_folder_path, selected_file)

    with open(full_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(full_path)[1].lower()
    mime = "audio/mpeg" if ext == ".mp3" else "audio/ogg"
    return f"data:{mime};base64,{encoded}"


def md_to_html(md_text, md_path, background_image=None, custom_font=None):
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
    print(f"开始转换md为html")

    # 重写图片 src 为 Base64
    html = rewrite_images(html, md_path)

    print(f"替换图片完成")
    html = html.replace("<h1>", '<h1 class="color-flow">') \
        .replace("<h2>", '<h2 class="color-flow">') \
        .replace("<h3>", '<h3 class="color-flow">')
    # 替换<img> 默认被<p>包裹
    html = html.replace("></p>", '>') \
        .replace("<p><img", '<img') \
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
        width: 800px; /* 固定宽度 */
        margin: 0 auto; /* 水平居中 */
        word-wrap: break-word; /* 自动换行 */
        overflow-x: hidden; /* 禁止横向滚动 */
    }
    /*  > 引用块（blockquotes）*/
    .markdown-content blockquote {
        font-size: 20px;      /* 比 h1 小一点 */
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
        font-size: 30px;
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
    /*  段落逐字显示动画 */
    
    .typing-text {
        /* 移除 white-space: nowrap; 允许文本自动换行 */
        /* white-space: nowrap; */
        overflow: hidden; /* 隐藏超出内容 */
        border-right: 2px solid #333; /* 显示光标方便观察 */
        animation: typing 5s steps(40, end), blink-caret 0.75s step-end infinite;
    }
    
    
    @keyframes typing {
        from { width: 0 }
        to { width: 100% }
    }
    
    @keyframes blink-caret {
        from, to { border-color: transparent }
        50% { border-color: #333 }
    }
    .markdown-content code,
    .markdown-content li {
        opacity: 0;
        animation: fadeIn 4s ease-in forwards;
        animation-delay: calc(0.1s * var(--i));
    }
    
    /* 渐现动画 */
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
        padding-left: 22px;
    }
    
    .markdown-content li, .markdown-content p{
        margin: 8px 0;
        font-size: 22px; /* 调整为你需要的字体大小 */
    }
    /*CSS 渐变动效 + 背景裁剪\应用到标题或段落*/
    .color-flow {
        color: #4e54c8; /* 默认颜色 */
    }
    
    """

    # # 添加背景图片（如果提供）
    if background_image:
        css += f"""

        .background-frame {{
            width: calc(100% + 60px); /* 比内容区宽 40px */
            max-width: 900px;         /* 卡片宽 800px + 左右各 20px 边距 */
            margin: 0 auto;
            padding: 30px;
            # box-sizing: border-box;
            background-image: url("{get_base64_image(background_image)}");
            background-size: cover;
            background-position: center;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
        }}
        """

    # 添加自定义字体（如果提供）
    if custom_font:
        css += f"@import url('{custom_font}');\n"
        css += "body { font-family: 'YourCustomFont', sans-serif; }\n"

    # 获取随机背景音乐数据

    # 完整 HTML 模板
    template = f"""<!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>Markdown Poster</title>
        <style>
            {css}
            .disclaimer {{
                margin-top: 40px;
                font-size: 14px;
                color: #999;
                text-align: center;
                padding: 15px;
                border-top: 1px solid #eee;
            }}
        </style>
    </head>
    <body class="gradient-bg">
         <div class="background-frame">
            <div class="markdown-content">
                {html}
                <div class="disclaimer">
                    ⚠️ 内容来源于互联网，仅供参考，请遵守相关法律法规。
                </div>
            </div>
        </div>


        <script>
            function typeText(element, index) {{
                const text = element.innerText;
                let charIndex = 0;
            
                element.innerHTML = ''; // 清空元素内容
            
                const interval = setInterval(() => {{
                    if (charIndex < text.length) {{
                        element.innerHTML += text.charAt(charIndex);
                        charIndex++;
                    }} else {{
                        clearInterval(interval); // 结束定时器
                    }}
                }}, 100); // 每 100ms 打印一个字符
            }}
            document.addEventListener("DOMContentLoaded", function () {{
                const paragraphs = document.querySelectorAll(".markdown-content p");
            
                paragraphs.forEach((p, index) => {{
                     // 移除 .typing-text 类的自动添加，改为手动控制
                // p.classList.add("typing-text");
        
                // 设置不同的动画延迟（按顺序）
                p.style.animationDelay = `${{index * 1}}s`; // 每段间隔1秒

                // 手动触发逐字打印效果
                typeText(p, index);
                }});
            }});
            document.querySelectorAll(".markdown-content p, .markdown-content li, .markdown-content code").forEach((el, idx) => {{
                el.style.setProperty('--i', idx);
            }});
            document.querySelectorAll('.markdown-content img').forEach(img => {{
                img.addEventListener('load', () => {{
                    img.style.opacity = '1';
                    if (img.naturalHeight > 400) {{
                        img.style.cursor = 'zoom-in';
                        img.addEventListener('click', () => {{
                            // 实现点击放大功能
                        }});
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    """

    return template


def get_base64_image(path):
    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:image/webp;base64,{encoded}"


def get_image_as_base64(full_path):
    """
    将图片文件或 URL 转为 Base64 编码
    :param path: 图片路径（本地路径或远程 URL）
    :return: Base64 字符串
    """
    # 处理本地图片
    # print(f"图片路径: {full_path}")
    try:
        with open(full_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
            ext = os.path.splitext(full_path)[1].lower()
            mime = "image/png" if ext == ".png" else "image/webp" if ext == ".webp" else "image/jpeg"
            base64_data = f"data:{mime};base64,{encoded}"
            # image_data = base64.b64decode(encoded)
            #
            # with open("test_image.png", "wb") as img_file:
            #     img_file.write(image_data)
            return base64_data
    except Exception as e:
        print(f"⚠️ 获取图片失败: {e}")


def save_html(html_content, output_path):
    """保存 HTML 到指定路径"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 已生成 HTML 文件: {output_path}")


async def convert_md_to_output(md_path, html_path, image_path=None, video_path=None, background_image=None,
                               custom_font=None, duration=7000):
    """
    统一接口：将 Markdown 转为 HTML 并可选输出图像
    """
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        print(f"正在读取md文件: {md_path}")

        if os.path.exists(html_path):
            print(f"✅ html文件已存在: {html_path}, 无需重复生成")
        else:
            print(f"❌ html文件不存在: {html_path}, 进行生成")
            html_content = md_to_html(md_text, md_path, background_image, custom_font)
            # 输出 HTML
            save_html(html_content, html_path)

        # 输出图像（如果提供路径）
        # if os.path.exists(image_path):
        # 使用 playwright 截图
        # 修改为异步调用方式：
        await html_to_image_with_playwright(html_path, image_path, video_path, mobile=True, duration=duration)

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


async def scroll_to_bottom(page, viewport_height=1920):
    """
    滚动到页面底部
    :param page: Playwright 页面对象
    :param viewport_height: 视口高度
    :return: 实际滚动的距离
    """
    last_scroll_position = await page.evaluate("window.pageYOffset")
    doc_height = await page.evaluate("document.body.scrollHeight")

    # 计算剩余高度
    remaining_height = doc_height - last_scroll_position - viewport_height
    if remaining_height <= 0:
        return 0

    # 执行滚动
    scroll_amount = min(remaining_height, 200)  # 每次最多滚动1000px
    scroll_duration = max(1000, int(scroll_amount * 1.5))

    await page.evaluate(f"""
        () => {{
            const start = window.pageYOffset;
            const end = start + {scroll_amount};
            const duration = {scroll_duration};
            let startTime = null;

            const animateScroll = (currentTime) => {{
                if (!startTime) startTime = currentTime;
                const elapsed = currentTime - startTime;

                // 使用缓动函数控制速度
                const progress = Math.min(elapsed / duration, 1);
                const easing = 1 - Math.pow(1 - progress, 3);  // cubic ease-out

                window.scrollTo({{
                    top: start + ({scroll_amount} * easing),
                    left: 0,
                    behavior: 'auto'
                }});

                if (progress < 1) {{
                    requestAnimationFrame(animateScroll);
                }}
            }};

            requestAnimationFrame(animateScroll);
        }}
    """)

    # 等待滚动完成
    await page.wait_for_timeout(scroll_duration + 500)

    # 返回实际滚动距离
    return scroll_amount


async def html_to_image_with_playwright(html_path, image_path=None, video_path=None, mobile=False, duration=7000):
    """
    使用 Playwright 将 HTML 内容转为 PNG 图像并录制视频
    :param html_path: HTML 文件路径
    :param image_path: 输出图像路径（.png）
    :param video_path: 输出视频路径（.webm），若不指定则不录屏
    :param mobile: 是否启用移动端视口
    """
    print("🚀 正在将 HTML 转为 PNG...")
    print(html_path, image_path, video_path, mobile, duration)
    abs_html_path = os.path.abspath(html_path)

    async with async_playwright() as p:
        # 启动浏览器（headless=True 用于无头模式）
        browser = await p.chromium.launch(headless=True)

        # 设置上下文（启用录屏）
        context_args = {}
        if video_path:
            os.makedirs(os.path.dirname(video_path), exist_ok=True)
            context_args.update(
                record_video_dir=os.path.dirname(video_path),
                record_video_size={"width": 1080, "height": 1920}
            )

        # 创建带录屏功能的上下文
        context = await browser.new_context(**context_args)
        page = await context.new_page()

        # 加载 HTML 页面
        await page.goto(f"file://{abs_html_path}")

        if mobile:
            # 设置为 iPhone 12 视口 + 移动端 UA
            await page.set_viewport_size({"width": 1080, "height": 1920})
            await page.add_init_script("""
                Object.defineProperty(navigator, 'userAgent', {
                    value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.4 (KHTML, like Gecko) Version/14.0 Mobile/15A5370a Safari/604.1',
                    configurable: false,
                    writable: false,
                    enumerable: true
                })
            """)
        else:
            await page.set_viewport_size({"width": 900, "height": 1080})

        # 增加 10s 停顿再开始录制
        await page.wait_for_timeout(timeout=duration)
        # 多次滚动直到所有内容可见
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts:

            # 尝试滚动更多
            scrolled = await scroll_to_bottom(page, viewport_height=1920)

            await page.wait_for_timeout(2000)

            # 如果没有滚动或内容已完全显示则退出
            if scrolled == 0:
                break

            attempt += 1
            print(f"🔄 第 {attempt} 次滚动完成，继续检查是否有更多内容")

        # 新增：等待图片加载完成

        # 截图
        if image_path:
            await page.screenshot(path=image_path, full_page=True)

        # 如果指定了视频路径，则保存视频（注意顺序）
        if video_path:
            tmp_video_path = video_path.replace(".mp4", '') + str(duration) + '_tmp.mp4'
            await page.close()  # 🔥 先关闭页面
            video = page.video
            if video:
                await video.save_as(tmp_video_path)
                print(f"🎥 已生成{'移动端' if mobile else '桌面'}视频文件: {tmp_video_path}")
                directory = os.path.dirname(tmp_video_path)
                for f in os.listdir(directory):
                    if f.lower().endswith(".webm"):
                        try:
                            os.remove(os.path.join(directory, f))
                            print(f"🗑️ 清理 .webm 文件: {f}")
                        except Exception as e:
                            print(f"❌ 清理失败: {f}, 错误: {e}")
        # 关闭资源
        await context.close()
        await browser.close()
        # time.sleep(3)

    # 👇 新增：裁剪最后 1 秒
    process_video_with_first_frame(tmp_video_path, output_path=video_path)
    # 图片裁剪
    if image_path:
        crop_image_with_gray_area(image_path, image_path)


def hex_to_rgb(hex_color):
    """
    将十六进制颜色值转换为 RGB 格式。
    :param hex_color: 十六进制颜色值（例如：'#f2f2f2'）
    :return: RGB 格式（例如：(242, 242, 242)）
    """
    # 去掉开头的 '#' 号
    hex_color = hex_color.lstrip('#')

    # 将十六进制字符串每两个字符一组，转换为十进制
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return (r, g, b)


def find_gray_area_height(image_path):
    """
    找到图像最底部中间区域的灰色部分高度。
    """
    # 打开图像
    img = Image.open(image_path)
    width, height = img.size

    # 定义灰色的阈值范围
    hex_color = "#f2f2f2"
    rgb_color = hex_to_rgb(hex_color)
    gray_threshold = rgb_color
    tolerance = 50  # 灰色值的容差范围

    # 遍历图像的每一行，从底部向上找到灰色区域的起始位置
    for y in range(height - 1, -1, -1):
        gray_row = True
        for x in range(width // 4, width * 3 // 4):  # 只检查中间区域
            pixel = img.getpixel((x, y))
            if not (gray_threshold[0] - tolerance <= pixel[0] <= gray_threshold[0] + tolerance and
                    gray_threshold[1] - tolerance <= pixel[1] <= gray_threshold[1] + tolerance and
                    gray_threshold[2] - tolerance <= pixel[2] <= gray_threshold[2] + tolerance):
                gray_row = False
                break
        if not gray_row:
            return height - y - 1  # 返回灰色区域的高度

    return 0  # 如果没有找到灰色区域，返回 0


def crop_image_with_gray_area(image_path, output_path):
    """
    根据灰色区域的高度裁剪图像，并预留 20px 的距离。
    """
    # 打开图像
    img = Image.open(image_path)
    width, height = img.size

    # 找到灰色区域的高度
    gray_height = find_gray_area_height(image_path)

    # 确定裁剪的底部位置（预留 20px）
    crop_bottom = height - gray_height + 20

    # 裁剪图像
    cropped_img = img.crop((0, 0, width, crop_bottom))

    # 保存裁剪后的图像
    cropped_img.save(output_path)


def process_video_with_first_frame(video_path, output_path):
    """
    使用 MoviePy 将 image_path 的图片作为视频第一帧，并裁剪最后 1 秒。
    :param image_path: 图片路径 (用于作+为首帧)
    :param video_path: 原始视频路径 (.mp4/.webm 等)
    :param output_path: 最终输出视频路径（默认覆盖原文件）
    """
    image_clip = None
    video_clip = None
    trimmed_clip = None

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"找不到视频文件: {video_path}")

    try:
        # Step 1: 加载图片并生成 2 秒的图片视频片段
        # print("🖼️ 正在生成首帧视频...")
        # image_clip = ImageClip(image_path)
        # image_clip.duration = 2
        # image_clip.resized(new_size=(1080, 1920))

        # Step 2: 加载原始视频
        print("🎥 正在加载原始视频...")
        video_clip = VideoFileClip(video_path)

        # Step 3: 裁剪第2秒到最后 1 秒
        if video_clip.duration > 1:
            trimmed_clip = video_clip.subclipped(2, video_clip.duration - 1)
        else:
            print("⚠️ 视频太短，无法裁剪最后 1 秒")
            trimmed_clip = video_clip

        # Step 5: 输出最终视频
        print("✅ 正在编码最终视频...")
        trimmed_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",  # 推荐使用更通用的 aac 编码
            fps=24,
            preset="fast",
        )

        print(f"🎉 视频处理完成: {output_path}")

    except Exception as e:
        print(f"❌ 视频处理失败: {e}")
    finally:
        if image_clip is not None:
            image_clip.close()
        if video_clip is not None:
            video_clip.close()
        if trimmed_clip is not None:
            trimmed_clip.close()


if __name__ == "__main__":
    # 示例配置
    print(os.path.exists("D:/PycharmProjects/google-trends/tasks/2025年05月26日14时59分_美国_所有分类/10-knicks vs pacers/10-kicks vs pacers playoff series analysis_4.jpg"))
    # input_md_path = os.path.join(root_dir, "README.md")
    # output_html = os.path.join(root_dir, "output.html")
    # output_image = os.path.join(root_dir, "output.png")
    # output_video = os.path.join(root_dir, "output.mp4")
    # # 随机选择背景图
    # bg_folder = os.path.join(root_dir, "webui", "bg")  # 本地磁盘路径
    # bg_image_path = get_random_bg_image(bg_folder)
    #
    # if bg_image_path:
    #     # bg_image_url = bg_image_path.replace(root_dir, "")  # 转为相对路径
    #     bg_image_url = bg_image_path.replace("\\", "/")
    # else:
    #     bg_image_url = None
    # print(f"随机选择的背景图路径: {bg_image_url}")
    # font_url = "https://fonts.googleapis.com/css2?family=Roboto&display=swap"
    #
    # asyncio.run(convert_md_to_output(
    #     md_path=input_md_path,
    #     html_path=output_html,
    #     image_path=output_image,
    #     video_path=output_video,
    #     background_image=bg_image_url,
    #     custom_font=font_url
    # ))
