import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Device, HealthData, HealthAlert

class HealthDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 将用户添加到他们的专属组
        if self.scope["user"].is_authenticated:
            self.user_group_name = f"user_{self.scope['user'].id}"
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        # 从组中移除用户
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # 处理接收到的数据
        try:
            data = json.loads(text_data)
            device_id = data.get('device_id')
            
            # 验证设备归属权
            if await self.verify_device_ownership(device_id):
                # 保存健康数据
                await self.save_health_data(data)
                
                # 检查是否需要触发警报
                alerts = await self.check_alerts(data)
                
                # 发送数据到用户组
                await self.channel_layer.group_send(
                    self.user_group_name,
                    {
                        'type': 'health_data',
                        'message': {
                            'heart_rate': data.get('heart_rate'),
                            'systolic': data.get('systolic'),
                            'diastolic': data.get('diastolic'),
                            'temperature': data.get('temperature'),
                            'alerts': alerts
                        }
                    }
                )
        except json.JSONDecodeError:
            pass

    async def health_data(self, event):
        # 发送数据到WebSocket
        await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def verify_device_ownership(self, device_id):
        try:
            return Device.objects.filter(
                id=device_id,
                user=self.scope['user']
            ).exists()
        except Device.DoesNotExist:
            return False

    @database_sync_to_async
    def save_health_data(self, data):
        device = Device.objects.get(id=data['device_id'])
        HealthData.objects.create(
            device=device,
            heart_rate=data.get('heart_rate'),
            systolic=data.get('systolic'),
            diastolic=data.get('diastolic'),
            temperature=data.get('temperature'),
            timestamp=timezone.now()
        )

    @database_sync_to_async
    def check_alerts(self, data):
        device = Device.objects.get(id=data['device_id'])
        threshold = device.user.healththreshold_set.first()
        alerts = []

        if threshold:
            # 检查心率
            heart_rate = data.get('heart_rate')
            if heart_rate and (heart_rate < threshold.min_heart_rate or heart_rate > threshold.max_heart_rate):
                alert = HealthAlert.objects.create(
                    device=device,
                    type='heart_rate',
                    details=f'心率异常: {heart_rate} BPM',
                    status='active'
                )
                alerts.append({
                    'id': alert.id,
                    'timestamp': alert.timestamp.isoformat(),
                    'device': device.name,
                    'type': '心率警报',
                    'details': alert.details,
                    'status': '活动'
                })

            # 检查血压
            systolic = data.get('systolic')
            diastolic = data.get('diastolic')
            if systolic and diastolic:
                if (systolic < threshold.min_systolic or 
                    systolic > threshold.max_systolic or 
                    diastolic < threshold.min_diastolic or 
                    diastolic > threshold.max_diastolic):
                    alert = HealthAlert.objects.create(
                        device=device,
                        type='blood_pressure',
                        details=f'血压异常: {systolic}/{diastolic} mmHg',
                        status='active'
                    )
                    alerts.append({
                        'id': alert.id,
                        'timestamp': alert.timestamp.isoformat(),
                        'device': device.name,
                        'type': '血压警报',
                        'details': alert.details,
                        'status': '活动'
                    })

            # 检查体温
            temperature = data.get('temperature')
            if temperature and (temperature < threshold.min_temperature or temperature > threshold.max_temperature):
                alert = HealthAlert.objects.create(
                    device=device,
                    type='temperature',
                    details=f'体温异常: {temperature}°C',
                    status='active'
                )
                alerts.append({
                    'id': alert.id,
                    'timestamp': alert.timestamp.isoformat(),
                    'device': device.name,
                    'type': '体温警报',
                    'details': alert.details,
                    'status': '活动'
                })

        return alerts 