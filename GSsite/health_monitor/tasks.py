from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from .models import HealthData, HealthAlert, Device

@shared_task
def process_health_data(health_data_ids):
    """处理健康数据并生成警报"""
    health_data_list = HealthData.objects.filter(
        id__in=health_data_ids,
        processed=False
    ).select_related('device__thresholds')

    for health_data in health_data_list:
        device = health_data.device
        thresholds = device.thresholds

        alerts = []

        # 检查心率
        if health_data.heart_rate is not None:
            if health_data.heart_rate < thresholds.heart_rate_min:
                alerts.append({
                    'alert_type': 'heart_rate_low',
                    'message': f'心率过低: {health_data.heart_rate}',
                    'severity': 'HIGH'
                })
            elif health_data.heart_rate > thresholds.heart_rate_max:
                alerts.append({
                    'alert_type': 'heart_rate_high',
                    'message': f'心率过高: {health_data.heart_rate}',
                    'severity': 'HIGH'
                })

        # 检查血压
        if health_data.blood_pressure_systolic is not None and health_data.blood_pressure_diastolic is not None:
            if health_data.blood_pressure_systolic < thresholds.blood_pressure_systolic_min:
                alerts.append({
                    'alert_type': 'blood_pressure_systolic_low',
                    'message': f'收缩压过低: {health_data.blood_pressure_systolic}',
                    'severity': 'HIGH'
                })
            elif health_data.blood_pressure_systolic > thresholds.blood_pressure_systolic_max:
                alerts.append({
                    'alert_type': 'blood_pressure_systolic_high',
                    'message': f'收缩压过高: {health_data.blood_pressure_systolic}',
                    'severity': 'HIGH'
                })

            if health_data.blood_pressure_diastolic < thresholds.blood_pressure_diastolic_min:
                alerts.append({
                    'alert_type': 'blood_pressure_diastolic_low',
                    'message': f'舒张压过低: {health_data.blood_pressure_diastolic}',
                    'severity': 'HIGH'
                })
            elif health_data.blood_pressure_diastolic > thresholds.blood_pressure_diastolic_max:
                alerts.append({
                    'alert_type': 'blood_pressure_diastolic_high',
                    'message': f'舒张压过高: {health_data.blood_pressure_diastolic}',
                    'severity': 'HIGH'
                })

        # 检查体温
        if health_data.body_temperature is not None:
            if health_data.body_temperature < thresholds.body_temperature_min:
                alerts.append({
                    'alert_type': 'body_temperature_low',
                    'message': f'体温过低: {health_data.body_temperature}',
                    'severity': 'MEDIUM'
                })
            elif health_data.body_temperature > thresholds.body_temperature_max:
                alerts.append({
                    'alert_type': 'body_temperature_high',
                    'message': f'体温过高: {health_data.body_temperature}',
                    'severity': 'HIGH'
                })

        # 检查血氧
        if health_data.blood_oxygen is not None and health_data.blood_oxygen < thresholds.blood_oxygen_min:
            alerts.append({
                'alert_type': 'blood_oxygen_low',
                'message': f'血氧过低: {health_data.blood_oxygen}',
                'severity': 'CRITICAL'
            })

        # 创建警报
        with transaction.atomic():
            for alert_data in alerts:
                HealthAlert.objects.create(
                    device=device,
                    **alert_data
                )
            
            # 标记数据为已处理
            health_data.processed = True
            health_data.save()

        # 更新设备心跳
        device.update_heartbeat()

@shared_task
def clean_old_health_data():
    """清理30天前的健康数据"""
    threshold_date = timezone.now() - timezone.timedelta(days=30)
    HealthData.objects.filter(timestamp__lt=threshold_date).delete()

@shared_task
def check_device_status():
    """检查设备状态并生成离线警报"""
    threshold_time = timezone.now() - timezone.timedelta(minutes=5)
    offline_devices = Device.objects.filter(
        is_active=True,
        last_heartbeat__lt=threshold_time
    )

    for device in offline_devices:
        HealthAlert.objects.create(
            device=device,
            alert_type='device_offline',
            message=f'设备已离线，最后心跳时间: {device.last_heartbeat}',
            severity='HIGH'
        )
        device.is_active = False
        device.save() 