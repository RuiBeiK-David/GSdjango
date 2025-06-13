from django.urls import path
from .views import (
    dashboard,
    device_details,
    alert_details,
    profile_view,
    edit_profile,
    about_view,
    api_logout_view,
)

urlpatterns = [
    # Main app views
    path('', dashboard, name='dashboard'),
    path('device/<str:device_id>/', device_details, name='device_details'),
    path('alert/<int:alert_id>/', alert_details, name='alert_details'),
    path('about/', about_view, name='about'),
    
    # Profile URLs are still part of the app
    path('accounts/profile/', profile_view, name='profile-page'),
    path('accounts/profile/edit/', edit_profile, name='profile-edit'),
    
    # API URLs
    path('api/logout/', api_logout_view, name='api-logout'),
] 