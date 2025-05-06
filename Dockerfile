# 使用官方 Python 基础镜像
FROM chinayin/playwright:1.41.2-chromium-python3.11

# 设置工作目录
WORKDIR /app

# 安装 tzdata 包
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*
#  某个 Python 包依赖 Rust 和 Cargo（Rust 的包管理器
#  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# 设置时区为 Asia/Shanghai
ENV TZ=Asia/Shanghai
# 复制项目文件
COPY core /app/core
COPY requirements.txt /app
COPY .env /app
COPY webui.py /app
COPY favicon.ico /app
COPY prompt/prompt.txt /app
COPY agent /app/agent
COPY conf.ini /app
# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN  playwright install chromium

# export HF_ENDPOINT=https://hf-mirror.com
# huggingface-cli download IndexTeam/Index-TTS  bigvgan_discriminator.pth bigvgan_generator.pth bpe.model dvae.pth gpt.pth unigram_12000.vocab   --local-dir /index-tts/checkpoints
# Models  file
# bigvgan_generator.pth
# bpe.model
# gpt.pth

# apt-get install ffmpeg

# 暴露端口
EXPOSE 7861