# 使用官方 Python 基础镜像
#FROM chinayin/playwright:1.41.2-chromium-python3.11
#docker pull swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/nvcr.io/nvidia/pytorch:24.11-py3
#FROM nvidia/cuda:12.8.0-base-ubuntu22.04
FROM nvcr.io/nvidia/pytorch:24.11-py3
# 设置工作目录
WORKDIR /app


# 设置清华源（完整版）
# 更新并安装系统依赖
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*
#  某个 Python 包依赖 Rust 和 Cargo（Rust 的包管理器
#  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# 设置时区为 Asia/Shanghai
ENV TZ=Asia/Shanghai

# 设置环境变量
#ENV HF_ENDPOINT=https://hf-mirror.com
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=true

# 复制项目文件
COPY requirements.txt /app/
COPY .env webui.py favicon.ico conf.ini /app/
COPY core /app/core
COPY agent /app/agent
COPY index-tts /app/index-tts

# 安装 Python 依赖
RUN mkdir -p /root/.pip && \
    echo "[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple\ntrusted-host = files.pythonhosted.org\ntrusted-host = pypi.org\ntrusted-host = files.pythonhosted.org" > /root/.pip/pip.conf \

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --no-deps && \
    pip install --no-cache-dir -r /app/index-tts/requirements.txt --no-deps && \
    pip install deepspeed && \
    playwright install chromium


#  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 暴露端口
EXPOSE 7861

#    # 下载模型

#
#    ## Models  file
#    # bigvgan_generator.pth
#    # bpe.model
#    # gpt.pth
#    # windows: conda  install ffmpeg
#    # apt-get install ffmpeg