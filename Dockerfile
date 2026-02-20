# AI交易机器人Dockerfile
# 基于Python 3.12

FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app

# 创建虚拟环境
RUN python3 -m venv venv

# 激活虚拟环境并安装依赖
RUN /bin/bash -c "source venv/bin/activate && pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt"

# 复制配置文件
COPY user_data/config.json /app/user_data/config.json

# 创建数据目录
RUN mkdir -p /app/user_data/data/processed

# 暴露端口
EXPOSE 8080

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV FREQTRADE_USERDIR=/app/user_data

# 启动命令
CMD ["/bin/bash", "-c", "source venv/bin/activate && freqtrade trade --config user_data/config.json --strategy AI_Strategy"]
