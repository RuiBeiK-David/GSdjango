from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render, redirect
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Device, HealthData, HealthAlert, UserProfile, UserSettings
from .serializers import (
    DeviceSerializer,
    HealthDataSerializer,
    HealthAlertSerializer,
    UserSerializer
)
from .tasks import process_health_data
import json
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

# Device Views
class DeviceListCreateAPIView(generics.ListCreateAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DeviceRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'device_id'

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user)

# HealthData Views
class HealthDataListCreateAPIView(generics.ListCreateAPIView):
    queryset = HealthData.objects.all()
    serializer_class = HealthDataSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        device_id = self.kwargs.get('device_id')
        return HealthData.objects.filter(device__device_id=device_id, device__user=self.request.user)

    def perform_create(self, serializer):
        device_id = self.kwargs.get('device_id')
        device = Device.objects.get(device_id=device_id, user=self.request.user)
        serializer.save(device=device)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_latest_health_data(request, device_id):
    """
    Get the latest health data for a specific device.
    """
    try:
        device = Device.objects.get(device_id=device_id, user=request.user)
        latest_data = HealthData.objects.filter(device=device).latest('timestamp')
        serializer = HealthDataSerializer(latest_data)
        return Response(serializer.data)
    except Device.DoesNotExist:
        return Response({'error': 'Device not found'}, status=404)
    except HealthData.DoesNotExist:
        return Response({'error': 'No health data available for this device'}, status=404)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_health_data_history(request, device_id):
    """
    Get the health data history for a specific device.
    """
    try:
        device = Device.objects.get(device_id=device_id, user=request.user)
        # Limit to the last 50 records for performance
        history_data = HealthData.objects.filter(device=device).order_by('-timestamp')[:50]
        serializer = HealthDataSerializer(history_data, many=True)
        return Response(serializer.data)
    except Device.DoesNotExist:
        return Response({'error': 'Device not found'}, status=404)


# Alert Views
class AlertListAPIView(generics.ListAPIView):
    queryset = HealthAlert.objects.all()
    serializer_class = HealthAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return HealthAlert.objects.filter(device__user=self.request.user)

class AlertRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = HealthAlert.objects.all()
    serializer_class = HealthAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return HealthAlert.objects.filter(device__user=self.request.user)

def index(request):
    return render(request, 'health_monitor/index.html')

@login_required
def dashboard(request):
    devices = Device.objects.filter(user=request.user)
    alerts = HealthAlert.objects.filter(device__user=request.user).order_by('-timestamp')[:10]
    token, _ = Token.objects.get_or_create(user=request.user)
    return render(request, 'health_monitor/dashboard.html', {
        'devices': devices,
        'alerts': alerts,
        'token': token.key
    })

@login_required
def settings_view(request):
    """
    Display and handle updates for user settings.
    """
    settings, _ = UserSettings.objects.get_or_create(user=request.user)
    token, _ = Token.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Notifications
        settings.email_notifications = 'emailNotifications' in request.POST
        settings.sms_notifications = 'smsNotifications' in request.POST
        settings.emergency_alerts = 'emergencyAlerts' in request.POST

        # Health Thresholds
        settings.heart_rate_min = request.POST.get('heartRateMin', 60)
        settings.heart_rate_max = request.POST.get('heartRateMax', 100)
        settings.systolic_bp_min = request.POST.get('bloodPressureSysMin', 90)
        settings.systolic_bp_max = request.POST.get('bloodPressureSysMax', 140)
        settings.diastolic_bp_min = request.POST.get('bloodPressureDiaMin', 60)
        settings.diastolic_bp_max = request.POST.get('bloodPressureDiaMax', 90)
        settings.body_temp_min = request.POST.get('bodyTempMin', 36.5)
        settings.body_temp_max = request.POST.get('bodyTempMax', 37.5)

        # Privacy
        settings.share_with_staff = 'shareHealthData' in request.POST
        settings.share_with_family = 'shareFamilyMembers' in request.POST
        settings.contribute_research_data = 'anonymousData' in request.POST

        # Data Management
        settings.data_retention_period = request.POST.get('dataRetention', 12)
        
        settings.save()
        messages.success(request, 'Your settings have been saved successfully!')
        return redirect('health_monitor:settings')

    return render(request, 'health_monitor/settings.html', {
        'settings': settings,
        'token': token.key
    })

def about(request):
    return render(request, 'health_monitor/about.html')

@login_required
def devices(request):
    devices = Device.objects.filter(user=request.user)
    return render(request, 'health_monitor/devices.html', {'devices': devices})

@login_required
def alerts(request):
    # Handle marking alert as read
    if request.method == 'POST':
        alert_id = request.POST.get('alert_id')
        if alert_id:
            alert = get_object_or_404(HealthAlert, id=alert_id, device__user=request.user)
            alert.is_active = False
            alert.save()
            return redirect('health_monitor:alerts') # Redirect to avoid re-posting

    # Handle filtering
    queryset = HealthAlert.objects.filter(device__user=request.user)
    
    device_filter = request.GET.get('device', '')
    if device_filter:
        queryset = queryset.filter(device__device_id=device_filter)

    status_filter = request.GET.get('status', '')
    if status_filter == 'new':
        queryset = queryset.filter(is_active=True)
    elif status_filter == 'read':
        queryset = queryset.filter(is_active=False)

    alerts_list = queryset.order_by('-timestamp')
    
    return render(request, 'health_monitor/alerts.html', {'alerts': alerts_list})

@login_required
@require_http_methods(['POST'])
def add_device(request):
    try:
        data = json.loads(request.body)
        device = Device.objects.create(
            user=request.user,
            name=data['device_name'],
            device_type=data['device_type']
        )
        return JsonResponse({'success': True, 'device_id': device.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(['DELETE'])
def delete_device(request):
    try:
        device_id = request.GET.get('device_id')
        device = Device.objects.get(id=device_id, user=request.user)
        device.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(['POST'])
def save_alert_settings(request):
    try:
        data = json.loads(request.body)
        threshold, created = HealthThreshold.objects.get_or_create(user=request.user)
        
        # 更新阈值设置
        threshold.min_heart_rate = data.get('min_heart_rate', 60)
        threshold.max_heart_rate = data.get('max_heart_rate', 100)
        threshold.min_systolic = data.get('min_systolic', 90)
        threshold.max_systolic = data.get('max_systolic', 140)
        threshold.min_diastolic = data.get('min_diastolic', 60)
        threshold.max_diastolic = data.get('max_diastolic', 90)
        threshold.min_temperature = data.get('min_temperature', 36.0)
        threshold.max_temperature = data.get('max_temperature', 37.5)
        
        # 更新通知设置
        threshold.email_notifications = data.get('email_notifications', False)
        threshold.sms_notifications = data.get('sms_notifications', False)
        
        threshold.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(['POST'])
def save_storage_settings(request):
    try:
        data = json.loads(request.body)
        # 这里可以保存到用户配置或系统设置中
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'registration/login.html')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.user.auth_token.delete()
    logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@login_required
def profile_view(request):
    return render(request, 'health_monitor/profile.html')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_login_status(request):
    return JsonResponse({'is_logged_in': True, 'username': request.user.username})

@login_required
def alert_detail(request, alert_id):
    alert = get_object_or_404(HealthAlert, pk=alert_id, device__user=request.user)
    return render(request, 'health_monitor/alert_detail.html', {'alert': alert})


# API Views
class UserProfileAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
            settings = UserSettings.objects.get(user=request.user)
            user_data = UserSerializer(request.user).data
            user_data['profile'] = {
                'bio': profile.bio,
                'location': profile.location,
                'birth_date': profile.birth_date
            }
            user_data['settings'] = {
                # Add settings fields here
            }
            return Response(user_data)
        except (UserProfile.DoesNotExist, UserSettings.DoesNotExist):
            return Response({'error': 'Profile or settings not found.'}, status=404)

    def post(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.save()

        profile.bio = request.data.get('bio', profile.bio)
        profile.location = request.data.get('location', profile.location)
        profile.birth_date = request.data.get('birth_date', profile.birth_date)
        profile.save()

        return Response(UserSerializer(user).data)


class DeviceListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        devices = Device.objects.filter(user=request.user)
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data)

class LatestHealthDataAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, device_id):
        try:
            device = Device.objects.get(device_id=device_id, user=request.user)
            latest_data = HealthData.objects.filter(device=device).latest('timestamp')
            serializer = HealthDataSerializer(latest_data)
            return Response(serializer.data)
        except (Device.DoesNotExist, HealthData.DoesNotExist):
            return Response(status=404)

class HealthDataHistoryAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, device_id):
        try:
            device = Device.objects.get(device_id=device_id, user=request.user)
            history_data = HealthData.objects.filter(device=device).order_by('-timestamp')[:50]
            serializer = HealthDataSerializer(history_data, many=True)
            return Response(serializer.data)
        except Device.DoesNotExist:
            return Response(status=404)


class AlertListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_devices = Device.objects.filter(user=request.user)
        alerts = HealthAlert.objects.filter(device__in=user_devices, is_active=True)
        serializer = HealthAlertSerializer(alerts, many=True)
        return Response(serializer.data)

class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html' 