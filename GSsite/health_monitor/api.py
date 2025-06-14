from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
import logging
import json

from .models import (
    Device, 
    HealthData, 
    HealthAlert, 
    UserProfile, 
    UserSettings, 
    HealthThreshold,
    User
)
from .serializers import (
    DeviceSerializer,
    HealthDataSerializer,
    HealthAlertSerializer,
    UserSerializer,
    UserProfileSerializer,
    UserSettingsSerializer,
    HealthThresholdSerializer
)
from .tasks import process_health_data

logger = logging.getLogger(__name__)

# ViewSets
class UserViewSet(viewsets.ModelViewSet):
    """用户管理视图集"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    
    def get_queryset(self):
        # 普通用户只能查看自己的信息，管理员可以查看所有用户
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前登录用户的信息"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """更新当前登录用户的信息"""
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileViewSet(viewsets.ModelViewSet):
    """用户个人资料视图集"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前登录用户的个人资料"""
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """更新当前登录用户的个人资料"""
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class UserSettingsViewSet(viewsets.ModelViewSet):
    """用户设置视图集"""
    queryset = UserSettings.objects.all()
    serializer_class = UserSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserSettings.objects.all()
        return UserSettings.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前登录用户的设置"""
        settings = get_object_or_404(UserSettings, user=request.user)
        serializer = self.get_serializer(settings)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """更新当前登录用户的设置"""
        settings = get_object_or_404(UserSettings, user=request.user)
        serializer = self.get_serializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeviceViewSet(viewsets.ModelViewSet):
    """设备管理视图集"""
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    
    def get_queryset(self):
        """只返回当前用户的设备"""
        user = self.request.user
        print(f"DeviceViewSet.get_queryset - 用户: {user}, 认证状态: {user.is_authenticated}")
        if user.is_staff:
            return Device.objects.all()
        return Device.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """创建设备时自动关联当前用户"""
        print(f"DeviceViewSet.perform_create - 用户: {self.request.user}, 数据: {self.request.data}")
        serializer.save(user=self.request.user)
    
    def initial(self, request, *args, **kwargs):
        """添加调试信息，记录认证过程"""
        try:
            # 记录请求头信息
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            print(f"DeviceViewSet.initial - 认证头信息: {auth_header}")
            print(f"DeviceViewSet.initial - 认证用户: {request.user}, 是否认证: {request.user.is_authenticated}")
            print(f"DeviceViewSet.initial - 认证方法: {request.auth}")
            print(f"DeviceViewSet.initial - 会话ID: {request.session.session_key}")
            print(f"DeviceViewSet.initial - CSRF Token: {request.META.get('CSRF_COOKIE', 'None')}")
            
            # 记录所有请求头
            headers = [f"{k}={v}" for k, v in request.META.items() if k.startswith('HTTP_')]
            print(f"DeviceViewSet.initial - 所有请求头: {', '.join(headers)}")
            
            super().initial(request, *args, **kwargs)
        except Exception as e:
            print(f"DeviceViewSet.initial - 异常: {str(e)}")
            import traceback
            print(f"DeviceViewSet.initial - 异常堆栈: {traceback.format_exc()}")
            super().initial(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """创建设备"""
        try:
            print(f"DeviceViewSet.create - 用户: {request.user}, 数据: {request.data}")
            return super().create(request, *args, **kwargs)
        except Exception as e:
            print(f"DeviceViewSet.create - 异常: {str(e)}")
            import traceback
            print(f"DeviceViewSet.create - 异常堆栈: {traceback.format_exc()}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, *args, **kwargs):
        """更新设备"""
        try:
            print(f"DeviceViewSet.update - 用户: {request.user}, 数据: {request.data}")
            return super().update(request, *args, **kwargs)
        except Exception as e:
            print(f"DeviceViewSet.update - 异常: {str(e)}")
            import traceback
            print(f"DeviceViewSet.update - 异常堆栈: {traceback.format_exc()}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def health_data(self, request, pk=None):
        """获取特定设备的健康数据"""
        device = self.get_object()
        queryset = HealthData.objects.filter(device=device).order_by('-timestamp')[:100]
        serializer = HealthDataSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def latest_health_data(self, request, pk=None):
        """获取特定设备的最新健康数据"""
        device = self.get_object()
        try:
            health_data = HealthData.objects.filter(device=device).latest('timestamp')
            serializer = HealthDataSerializer(health_data)
            return Response(serializer.data)
        except HealthData.DoesNotExist:
            return Response({"detail": "No health data available for this device."}, 
                           status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def alerts(self, request, pk=None):
        """获取特定设备的健康警报"""
        device = self.get_object()
        queryset = HealthAlert.objects.filter(device=device).order_by('-created_at')[:50]
        serializer = HealthAlertSerializer(queryset, many=True)
        return Response(serializer.data)

class HealthDataViewSet(viewsets.ModelViewSet):
    """健康数据视图集"""
    queryset = HealthData.objects.all()
    serializer_class = HealthDataSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    
    def get_queryset(self):
        """只返回当前用户设备的健康数据"""
        user = self.request.user
        device_id = self.kwargs.get('device_id')
        
        if device_id:
            return HealthData.objects.filter(device__device_id=device_id, device__user=user).order_by('-timestamp')
        
        if user.is_staff:
            return HealthData.objects.all().order_by('-timestamp')
        return HealthData.objects.filter(device__user=user).order_by('-timestamp')
    
    def perform_create(self, serializer):
        """创建健康数据时进行数据验证"""
        device_id = self.request.data.get('device')
        device = get_object_or_404(Device, id=device_id, user=self.request.user)
        serializer.save(device=device)
        
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """获取所有设备最新的健康数据"""
        user = request.user
        devices = Device.objects.filter(user=user)
        
        latest_data = []
        for device in devices:
            try:
                data = HealthData.objects.filter(device=device).latest('timestamp')
                latest_data.append(self.get_serializer(data).data)
            except HealthData.DoesNotExist:
                continue
        
        return Response(latest_data)

class HealthAlertViewSet(viewsets.ModelViewSet):
    """健康警报视图集"""
    queryset = HealthAlert.objects.all()
    serializer_class = HealthAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    
    def get_queryset(self):
        """只返回当前用户的健康警报"""
        user = self.request.user
        if user.is_staff:
            return HealthAlert.objects.all().order_by('-created_at')
        return HealthAlert.objects.filter(device__user=user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """将警报标记为已解决"""
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        return Response({'status': 'alert resolved'})

    @action(detail=False, methods=['get'])
    def active(self, request):
        """获取当前用户所有未解决的警报"""
        queryset = self.get_queryset().filter(is_resolved=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class HealthThresholdViewSet(viewsets.ModelViewSet):
    """健康阈值设置视图集"""
    queryset = HealthThreshold.objects.all()
    serializer_class = HealthThresholdSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    
    def get_queryset(self):
        """只返回当前用户的健康阈值设置"""
        user = self.request.user
        if user.is_staff:
            return HealthThreshold.objects.all()
        return HealthThreshold.objects.filter(user=user)

# Function-based API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_login_status(request):
    """
    检查用户登录状态。
    如果用户已登录，返回用户信息；否则返回401 Unauthorized。
    """
    if request.user.is_authenticated:
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        user_data = {
            'is_logged_in': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name
            },
            'profile': {
                'age': user_profile.age,
                'gender': user_profile.gender,
                'date_of_birth': user_profile.date_of_birth.strftime('%Y-%m-%d') if user_profile.date_of_birth else None,
                'phone_number': user_profile.phone_number,
                'address': user_profile.address,
                'medical_history': user_profile.medical_history
            }
        }
        return Response(user_data)
    return Response({'is_logged_in': False}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(['POST'])
def data_receiver(request):
    """
    接收来自健康监测设备的数据。
    这是一个开放的端点，不需要认证。
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            
            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'Device ID is required'}, status=400)
            
            try:
                device = Device.objects.get(device_id=device_id)
            except Device.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Device not found'}, status=404)
            
            # 使用Celery异步处理数据
            process_health_data.delay(device.id, data)
            
            return JsonResponse({'status': 'success', 'message': 'Data received and queued for processing'})
        
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error processing incoming data: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    用户登出。
    """
    logout(request)
    return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK) 