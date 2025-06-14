from django.urls import path
from .views import (
    check_login_status, 
    api_logout_view, 
    UserProfileAPI,
    DeviceListCreateAPIView,
    get_latest_health_data,
    get_health_data_history,
    AlertListAPIView,
    get_heart_rate_data,
    get_blood_pressure_data,
    add_heart_rate_data,
    add_blood_pressure_data,
)
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Device, HealthData

app_name = 'health_monitor_api'

# 为测试数据输入API创建特殊的URL模式，不需要认证
add_heart_rate_data_view = permission_classes([AllowAny])(add_heart_rate_data)
add_blood_pressure_data_view = permission_classes([AllowAny])(add_blood_pressure_data)

# 创建特殊的测试端点，完全不需要认证
@api_view(['POST'])
@permission_classes([AllowAny])
def test_add_heart_rate_data(request):
    """
    特殊的测试API端点，用于添加心率数据，不需要任何认证。
    """
    try:
        # 获取用户名
        username = request.data.get('username')
        if not username:
            return Response({'error': '需要提供用户名'}, status=400)
        
        # 获取心率值
        heart_rate = request.data.get('heart_rate')
        if heart_rate is None:
            return Response({'error': '需要提供心率值'}, status=400)
        
        # 查找用户
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': f'用户 {username} 不存在'}, status=404)
        
        # 获取用户的设备
        devices = Device.objects.filter(user=user)
        
        if not devices.exists():
            # 如果用户没有设备，创建一个默认设备
            device = Device.objects.create(
                user=user,
                name=f"{username}的默认设备",
                is_active=True
            )
        else:
            # 使用第一个设备
            device = devices.first()
        
        # 创建新的健康数据记录
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
def test_add_blood_pressure_data(request):
    """
    特殊的测试API端点，用于添加血压数据，不需要任何认证。
    """
    try:
        # 获取用户名
        username = request.data.get('username')
        if not username:
            return Response({'error': '需要提供用户名'}, status=400)
        
        # 获取血压值
        systolic = request.data.get('systolic')
        diastolic = request.data.get('diastolic')
        
        if systolic is None or diastolic is None:
            return Response({'error': '需要同时提供收缩压和舒张压值'}, status=400)
        
        # 查找用户
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': f'用户 {username} 不存在'}, status=404)
        
        # 获取用户的设备
        devices = Device.objects.filter(user=user)
        
        if not devices.exists():
            # 如果用户没有设备，创建一个默认设备
            device = Device.objects.create(
                user=user,
                name=f"{username}的默认设备",
                is_active=True
            )
        else:
            # 使用第一个设备
            device = devices.first()
        
        # 创建新的健康数据记录
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

urlpatterns = [
    # Authentication APIs
    path('check-login/', check_login_status, name='check-login'),
    path('logout/', api_logout_view, name='logout'),
    
    # Profile API
    path('profile/', UserProfileAPI.as_view(), name='user-profile'),

    # Device and Health Data APIs
    path('devices/', DeviceListCreateAPIView.as_view(), name='device-list-create'),
    path('devices/<str:device_id>/latest/', get_latest_health_data, name='latest-health-data'),
    path('devices/<str:device_id>/history/', get_health_data_history, name='health-data-history'),
    path('alerts/', AlertListAPIView.as_view(), name='alert-list'),
    
    # Chart Data APIs
    path('chart/heart-rate/', get_heart_rate_data, name='heart-rate-data'),
    path('chart/blood-pressure/', get_blood_pressure_data, name='blood-pressure-data'),
    
    # Data Input APIs - 使用特殊的视图函数，不需要认证
    path('data/heart-rate/add/', add_heart_rate_data_view, name='add-heart-rate'),
    path('data/blood-pressure/add/', add_blood_pressure_data_view, name='add-blood-pressure'),
    
    # 特殊测试API端点 - 完全不需要认证
    path('test/heart-rate/add/', test_add_heart_rate_data, name='test-add-heart-rate'),
    path('test/blood-pressure/add/', test_add_blood_pressure_data, name='test-add-blood-pressure'),
] 