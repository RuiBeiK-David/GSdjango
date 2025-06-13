#!/bin/sh

# Change to the directory containing manage.py
cd /app/GSsite

# 收集静态文件
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 运行数据库迁移 (可选，但推荐)
echo "Applying database migrations..."
python manage.py migrate --noinput

# 启动 Gunicorn 服务器
echo "Starting Gunicorn..."
gunicorn GSsite.wsgi:application --bind 0.0.0.0:8000 