from django.urls import path
from .views import (
    dashboard,
    profile_view,
    settings_view,
    about,
    devices,
    alerts,
    alert_detail,
)

app_name = 'health_monitor'

urlpatterns = [
    # Page Rendering
    path('', dashboard, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('settings/', settings_view, name='settings'),
    path('about/', about, name='about'),
    path('devices/', devices, name='devices'),
    path('alerts/', alerts, name='alerts'),
    path('alerts/<int:alert_id>/', alert_detail, name='alert_detail'),
] 