# 使用官方 Python 基础镜像
FROM chinayin/playwright:1.41.2-chromium-python3.11

# 设置工作目录
WORKDIR /app

# 安装 tzdata 包
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*

# 设置时区为 Asia/Shanghai
ENV TZ=Asia/Shanghai
# 复制项目文件
COPY core /app/core
COPY requirements.txt /app
COPY .env /app
COPY main.py /app
# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN  playwright install chromium
# 暴露端口
EXPOSE 7861