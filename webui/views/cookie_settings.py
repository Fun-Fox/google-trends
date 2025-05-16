# tabs/cookie_settings.py
import gradio as gr
from webui.service.cookie import save_cookie, read_cookie


def build_tab():
    # 使用 Tab 方式组织界面
    gr.Markdown("### 设置说明")
    gr.Markdown("在 `.env` 文件中配置 `COOKIE_STRING`，以支持采集访问 Google Trends 页面。")
    gr.Markdown("示例：")
    gr.Markdown("```plaintext\nCOOKIE_STRING=\"SID=...; HSID=...; SSID=...\"\n```")

    # 新增输入框和按钮
    cookie_input = gr.Textbox(label="输入 COOKIE_STRING", lines=3)
    save_button = gr.Button("保存并应用")
    status_text = gr.Textbox(label="状态", lines=1, interactive=False)

    initial_cookie = read_cookie(status_text)

    cookie_input.value = initial_cookie

    save_button.click(fn=save_cookie, inputs=cookie_input, outputs=status_text)



