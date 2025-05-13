# tabs/cookie_settings.py
import os
import gradio as gr

def save_cookie(cookie_str):
    try:
        with open(".env", "r") as f:
            lines = f.readlines()
        with open(".env", "w") as f:
            for line in lines:
                if not line.startswith("COOKIE_STRING="):
                    f.write(line)
            f.write(f"COOKIE_STRING=\"{cookie_str}\"\n")
        return "✅ COOKIE_STRING 已保存"
    except Exception as e:
        return f"❌ 保存失败: {e}"

def build_tab():
    cookie_input = gr.Textbox(label="输入 COOKIE_STRING", lines=3)
    status_text = gr.Textbox(label="状态", interactive=False)
    save_button = gr.Button("保存并应用")

    save_button.click(fn=save_cookie, inputs=cookie_input, outputs=status_text)

    gr.Markdown("### 设置说明")
    gr.Markdown("在 `.env` 文件中配置 `COOKIE_STRING`，以支持采集访问 Google Trends 页面。")
    gr.Markdown("```plaintext\nCOOKIE_STRING=\"SID=...; HSID=...; SSID=...\"\n```")
