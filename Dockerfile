# 使用 Python 3.11 作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 复制并设置入口脚本权限
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建日志目录并设置权限
RUN mkdir -p /app/logs && \
    touch /app/logs/app.log && \
    chmod -R 777 /app/logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=GSsite.settings

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "GSsite.wsgi:application", "--bind", "0.0.0.0:8000"] 