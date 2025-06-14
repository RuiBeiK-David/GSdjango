from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Device, HealthData, HealthAlert, UserProfile, UserSettings
from .forms import SignUpForm, UserProfileForm
from django.contrib.auth import login, logout, authenticate
from django.urls import reverse_lazy
from django.views import generic
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics, permissions
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.http import require_http_methods
from .serializers import (
    DeviceSerializer,
    HealthDataSerializer,
    HealthAlertSerializer,
    UserSerializer
)
from .tasks import process_health_data
import json
from rest_framework.views import APIView
from django.views.generic.edit import CreateView
from django.contrib.auth.models import User
import uuid

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
    # Pass the first device to the template context if it exists, otherwise None
    first_device = devices.first()
    
    # Get heart rate and blood pressure data for charts
    heart_rate_data = []
    blood_pressure_data = []
    
    if first_device:
        # Get the latest 5 health data points for the first device
        latest_health_data = HealthData.objects.filter(device=first_device).order_by('-timestamp')[:5]
        
        # Process data for charts (reverse to show in chronological order)
        for data_point in reversed(list(latest_health_data)):
            # Format timestamp for display
            formatted_time = data_point.timestamp.strftime('%H:%M')
            
            # Add heart rate data if available
            if data_point.heart_rate is not None:
                heart_rate_data.append({
                    'time': formatted_time,
                    'value': data_point.heart_rate
                })
            
            # Add blood pressure data if available
            if data_point.blood_pressure_systolic is not None and data_point.blood_pressure_diastolic is not None:
                blood_pressure_data.append({
                    'time': formatted_time,
                    'systolic': data_point.blood_pressure_systolic,
                    'diastolic': data_point.blood_pressure_diastolic
                })
    
    context = {
        'devices': devices,
        'alerts': alerts,
        'first_device': first_device,
        'heart_rate_data': json.dumps(heart_rate_data),
        'blood_pressure_data': json.dumps(blood_pressure_data)
    }
    return render(request, 'health_monitor/dashboard.html', context)

@login_required
def settings_view(request):
    """
    Display and handle updates for user settings.
    """
    settings, _ = UserSettings.objects.get_or_create(user=request.user)

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

    return render(request, 'health_monitor/settings.html')

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
    
    devices = Device.objects.filter(user=request.user)
    
    context = {
        'alerts': alerts_list,
        'devices': devices,
        'selected_device': device_filter,
        'selected_status': status_filter,
    }
    
    return render(request, 'health_monitor/alerts.html', context)

@login_required
@require_http_methods(['POST'])
def add_device(request):
    """
    添加新设备的视图函数。
    接收设备名称和设备类型，自动生成唯一的设备ID，并将设备信息保存到数据库中。
    """
    try:
        data = json.loads(request.body)
        device_name = data.get('device_name')
        device_type = data.get('device_type', '')
        
        # 生成唯一的设备ID / Generate unique device ID
        unique_device_id = str(uuid.uuid4())
        
        # 创建新设备 / Create new device
        device = Device.objects.create(
            user=request.user,
            device_id=unique_device_id,
            name=device_name,
            device_type=device_type,
            is_active=True
        )
        
        return JsonResponse({
            'success': True, 
            'device_id': device.device_id,
            'message': 'Device added successfully'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(['POST'])
def edit_device(request):
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        device_name = data.get('device_name')
        device_type = data.get('device_type', '')
        
        # Get the device and check ownership
        device = get_object_or_404(Device, id=device_id, user=request.user)
        
        # Update device fields
        device.name = device_name
        device.device_type = device_type
        device.save()
        
        return JsonResponse({
            'success': True, 
            'device_id': device.id,
            'message': 'Device updated successfully'
        })
    except Device.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Device not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(['DELETE'])
def delete_device(request):
    try:
        device_id = request.GET.get('device_id')
        device = get_object_or_404(Device, id=device_id, user=request.user)
        device_name = device.name
        device.delete()
        return JsonResponse({
            'success': True,
            'message': f'Device "{device_name}" deleted successfully'
        })
    except Device.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Device not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(['POST'])
def save_alert_settings(request):
    try:
        data = json.loads(request.body)
        threshold, created = HealthThreshold.objects.get_or_create(user=request.user)
        
        # 更新阈值设置 / Update threshold settings
        threshold.min_heart_rate = data.get('min_heart_rate', 60)
        threshold.max_heart_rate = data.get('max_heart_rate', 100)
        threshold.min_systolic = data.get('min_systolic', 90)
        threshold.max_systolic = data.get('max_systolic', 140)
        threshold.min_diastolic = data.get('min_diastolic', 60)
        threshold.max_diastolic = data.get('max_diastolic', 90)
        threshold.min_temperature = data.get('min_temperature', 36.0)
        threshold.max_temperature = data.get('max_temperature', 37.5)
        
        # 更新通知设置 / Update notification settings
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
        # 这里可以保存到用户配置或系统设置中 / This can be saved to user configuration or system settings
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
def api_logout_view(request):
    """
    API endpoint for user logout.
    """
    try:
        # 不再删除令牌 / No longer delete the token
        logout(request)
        return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    context = {
        'profile': profile,
    }
    return render(request, 'health_monitor/profile.html', context)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_login_status(request):
    return JsonResponse({'is_logged_in': True, 'username': request.user.username})

@login_required
def alert_detail(request, alert_id):
    alert = get_object_or_404(HealthAlert, pk=alert_id, device__user=request.user)
    return render(request, 'health_monitor/alert_detail.html', {'alert': alert})

def logout_view(request):
    """
    自定义登出视图，处理用户登出请求并重定向到登录页面
    Custom logout view that processes user logout requests and redirects to the login page
    """
    logout(request)
    return redirect('login')

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
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'

    def form_valid(self, form):
        # 保存用户对象 / Save user object
        response = super().form_valid(form)
        user = self.object
        
        # 确保创建用户资料和设置 / Ensure user profile and settings are created
        profile, created = UserProfile.objects.get_or_create(user=user)
        settings, created = UserSettings.objects.get_or_create(user=user)
        
        return response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_heart_rate_data(request):
    """
    Get the latest 5 heart rate data points for the user's devices.
    """
    try:
        # Get user's devices
        devices = Device.objects.filter(user=request.user)
        
        if not devices.exists():
            return Response({'error': 'No devices found'}, status=404)
        
        # Use the first device by default
        first_device = devices.first()
        
        # Get the latest 5 health data points with heart rate for the device
        latest_data = HealthData.objects.filter(
            device=first_device,
            heart_rate__isnull=False
        ).order_by('-timestamp')[:5]
        
        # Format the data for the chart
        chart_data = []
        for data_point in reversed(list(latest_data)):
            chart_data.append({
                'time': data_point.timestamp.strftime('%H:%M'),
                'value': data_point.heart_rate
            })
        
        return Response(chart_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_blood_pressure_data(request):
    """
    Get the latest 5 blood pressure data points for the user's devices.
    """
    try:
        # Get user's devices
        devices = Device.objects.filter(user=request.user)
        
        if not devices.exists():
            return Response({'error': 'No devices found'}, status=404)
        
        # Use the first device by default
        first_device = devices.first()
        
        # Get the latest 5 health data points with blood pressure for the device
        latest_data = HealthData.objects.filter(
            device=first_device,
            blood_pressure_systolic__isnull=False,
            blood_pressure_diastolic__isnull=False
        ).order_by('-timestamp')[:5]
        
        # Format the data for the chart
        chart_data = []
        for data_point in reversed(list(latest_data)):
            chart_data.append({
                'time': data_point.timestamp.strftime('%H:%M'),
                'systolic': data_point.blood_pressure_systolic,
                'diastolic': data_point.blood_pressure_diastolic
            })
        
        return Response(chart_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def add_heart_rate_data(request):
    """
    API endpoint to add new heart rate data for a user's device by username.
    No authentication required for testing purposes.
    """
    try:
        # Get username from request data
        username = request.data.get('username')
        if not username:
            return Response({'error': 'Username is required'}, status=400)
        
        # Get heart rate from request data
        heart_rate = request.data.get('heart_rate')
        if heart_rate is None:
            return Response({'error': 'Heart rate value is required'}, status=400)
        
        # Find user by username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': f'User {username} not found'}, status=404)
        
        # Get user's devices
        devices = Device.objects.filter(user=user)
        
        if not devices.exists():
            # Create a default device for the user if none exists
            device = Device.objects.create(
                user=user,
                name=f"{username}'s Default Device",
                is_active=True
            )
        else:
            # Use the first device
            device = devices.first()
        
        # Create new health data entry
        health_data = HealthData.objects.create(
            device=device,
            heart_rate=heart_rate
        )
        
        return Response({
            'success': True,
            'heart_rate': heart_rate,
            'timestamp': health_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }, status=201)
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def add_blood_pressure_data(request):
    """
    API endpoint to add new blood pressure data for a user's device by username.
    No authentication required for testing purposes.
    """
    try:
        # Get username from request data
        username = request.data.get('username')
        if not username:
            return Response({'error': 'Username is required'}, status=400)
        
        # Get blood pressure values from request data
        systolic = request.data.get('systolic')
        diastolic = request.data.get('diastolic')
        
        if systolic is None or diastolic is None:
            return Response({'error': 'Both systolic and diastolic values are required'}, status=400)
        
        # Find user by username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': f'User {username} not found'}, status=404)
        
        # Get user's devices
        devices = Device.objects.filter(user=user)
        
        if not devices.exists():
            # Create a default device for the user if none exists
            device = Device.objects.create(
                user=user,
                name=f"{username}'s Default Device",
                is_active=True
            )
        else:
            # Use the first device
            device = devices.first()
        
        # Create new health data entry
        health_data = HealthData.objects.create(
            device=device,
            blood_pressure_systolic=systolic,
            blood_pressure_diastolic=diastolic
        )
        
        return Response({
            'success': True,
            'systolic': systolic,
            'diastolic': diastolic,
            'timestamp': health_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }, status=201)
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@login_required
@require_http_methods(['POST'])
def update_profile(request):
    """
    更新用户个人资料的视图函数。
    接收用户的电子邮件、全名、性别、电话号码和ID号码，并将其保存到数据库中。
    用户名不可修改。
    
    View function for updating user profile.
    Receives user's email, full name, gender, phone number and ID number, and saves them to the database.
    Username cannot be modified.
    """
    try:
        data = json.loads(request.body)
        
        # 获取当前用户和其个人资料 / Get current user and their profile
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # 更新电子邮件（如果提供） / Update email (if provided)
        email = data.get('email')
        if email:
            user.email = email
            user.save()
        
        # 更新个人资料信息 / Update profile information
        profile.name = data.get('name', profile.name)
        profile.gender = data.get('gender', profile.gender)
        profile.phone_number = data.get('phone_number', profile.phone_number)
        profile.id_number = data.get('id_number', profile.id_number)
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500) 