from django.urls import path
from .views import (
    dashboard,
    profile_view,
    settings_view,
    about,
    devices,
    alerts,
    alert_detail,
    add_device,
    edit_device,
    delete_device,
    update_profile,
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
    
    # Device Management API
    path('api/devices/add/', add_device, name='add_device'),
    path('api/devices/edit/', edit_device, name='edit_device'),
    path('api/devices/delete/', delete_device, name='delete_device'),
    
    # User Profile API
    path('api/profile/update/', update_profile, name='update_profile'),
] 