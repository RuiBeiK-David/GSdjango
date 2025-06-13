from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/health_data/$', consumers.HealthDataConsumer.as_asgi()),
] 