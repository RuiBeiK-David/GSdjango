from django.urls import path
from .views import (
    check_login_status, 
    logout_view, 
    UserProfileAPI,
    DeviceListCreateAPIView,
    get_latest_health_data,
    get_health_data_history,
    AlertListAPIView,
)

app_name = 'health_monitor_api'

urlpatterns = [
    # Authentication APIs
    path('check-login/', check_login_status, name='check-login'),
    path('logout/', logout_view, name='logout'),
    
    # Profile API
    path('profile/', UserProfileAPI.as_view(), name='user-profile'),

    # Device and Health Data APIs
    path('devices/', DeviceListCreateAPIView.as_view(), name='device-list-create'),
    path('devices/<str:device_id>/latest/', get_latest_health_data, name='latest-health-data'),
    path('devices/<str:device_id>/history/', get_health_data_history, name='health-data-history'),
    path('alerts/', AlertListAPIView.as_view(), name='alert-list'),
] 