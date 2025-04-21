# Google Trends 爬虫项目

## 项目简介
本项目是一个基于 Python 和 Playwright 的 Google Trends 数据采集工具，支持通过 Gradio 提供的 Web 界面进行交互操作。

## 功能特性
- 动态设置和保存 `COOKIE_STRING` 到 `.env` 文件
- 支持日志记录和实时日志查看
- 自动下载并保存 Google Trends 页面中的热词图片
- 使用 Docker 进行容器化部署

## 快速开始

## 部署

### docker build 镜像

```
   docker build -t google-trends .
```

### docker compose 本地启动

#### 配置修改

- PROXY_URL:修改代理服务器地址

#### 修改volumes配置

E:/Service/docker-volumes为你自己的本地目录

```
    environment:
      - PROXY_URL=http://192.168.1.12:10811
      - ZIP_DIR=/asset/zip
      - TASK_DIR=/asset/task
    volumes:
      - E:/Service/docker-volumes/task:/asset/task
      - E:/Service/docker-volumes/zip:/asset/zip
    command: python main.py --port 7861
```

#### 启动命令

```
    docker compose up -d
```