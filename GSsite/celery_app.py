import os
from celery import Celery

# 设置默认的 Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GSsite.settings')

# 创建 Celery 实例
app = Celery('GSsite')

# 使用字符串配置，这样 worker 不需要序列化配置对象
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现所有已注册的 Django app 中的任务
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 