from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    id_number = models.CharField(max_length=50, blank=True, null=True) # 身份证号 / ID card number

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    当用户对象保存时，创建或更新对应的用户资料
    When a user object is saved, create or update the corresponding user profile
    """
    if created:
        # 如果是新创建的用户，创建一个资料 / If this is a newly created user, create a profile
        UserProfile.objects.create(user=instance)
    else:
        # 如果用户已存在，确保资料也存在 / If the user already exists, ensure the profile exists too
        try:
            # 尝试获取资料，如果不存在则创建 / Try to get the profile, create it if it doesn't exist
            profile = instance.profile
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=instance)


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Notifications
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    emergency_alerts = models.BooleanField(default=True)

    # Health Thresholds
    heart_rate_min = models.IntegerField(default=60)
    heart_rate_max = models.IntegerField(default=100)
    systolic_bp_min = models.IntegerField(default=90)
    systolic_bp_max = models.IntegerField(default=140)
    diastolic_bp_min = models.IntegerField(default=60)
    diastolic_bp_max = models.IntegerField(default=90)
    body_temp_min = models.DecimalField(max_digits=4, decimal_places=1, default=36.5)
    body_temp_max = models.DecimalField(max_digits=4, decimal_places=1, default=37.5)

    # Privacy
    share_with_staff = models.BooleanField(default=True)
    share_with_family = models.BooleanField(default=True)
    contribute_research_data = models.BooleanField(default=False)
    
    # Data Management
    data_retention_period = models.IntegerField(default=12) # in months

    def __str__(self):
        return f"Settings for {self.user.username}"

@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """
    当用户对象保存时，创建或更新对应的用户设置
    When a user object is saved, create or update the corresponding user settings
    """
    if created:
        # 如果是新创建的用户，创建设置 / If this is a newly created user, create settings
        UserSettings.objects.create(user=instance)
    else:
        # 如果用户已存在，确保设置也存在 / If the user already exists, ensure the settings exist too
        try:
            # 尝试获取设置，如果不存在则创建 / Try to get the settings, create them if they don't exist
            settings = instance.settings
        except UserSettings.DoesNotExist:
            UserSettings.objects.create(user=instance)


class Device(models.Model):
    """设备模型 / Device model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=100, default='Default Device Name')
    device_type = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.device_id})"

class HealthData(models.Model):
    """健康数据模型 / Health data model"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='health_data')
    timestamp = models.DateTimeField(auto_now_add=True)
    heart_rate = models.FloatField(null=True, blank=True)
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    blood_oxygen = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Data for {self.device.name} at {self.timestamp}"

class HealthAlert(models.Model):
    """健康警报模型 / Health alert model"""
    ALERT_TYPES = [
        ('HR_HIGH', 'High Heart Rate'),
        ('HR_LOW', 'Low Heart Rate'),
        ('BP_HIGH', 'High Blood Pressure'),
        ('SPO2_LOW', 'Low Blood Oxygen'),
    ]
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} for {self.device.name}"

class HealthThreshold(models.Model):
    """健康指标阈值设置 / Health metric threshold settings"""
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='thresholds')
    heart_rate_min = models.IntegerField(default=60)
    heart_rate_max = models.IntegerField(default=100)
    blood_pressure_systolic_min = models.IntegerField(default=90)
    blood_pressure_systolic_max = models.IntegerField(default=140)
    blood_pressure_diastolic_min = models.IntegerField(default=60)
    blood_pressure_diastolic_max = models.IntegerField(default=90)
    body_temperature_min = models.DecimalField(max_digits=4, decimal_places=1, default=36.0)
    body_temperature_max = models.DecimalField(max_digits=4, decimal_places=1, default=37.5)
    blood_oxygen_min = models.IntegerField(default=95)

    def __str__(self):
        return f"Thresholds for {self.device.name}"

    def update_heartbeat(self):
        """更新设备心跳时间 / Update device heartbeat time"""
        self.last_heartbeat = timezone.now()
        self.save(update_fields=['last_heartbeat'])

    def save(self, *args, **kwargs):
        """重写save方法以实现缓存更新 / Override save method to update cache"""
        super().save(*args, **kwargs)
        # 更新最新数据缓存 / Update the latest data cache
        cache_key = f"latest_health_data_{self.device_id}"
        cache.set(cache_key, self, timeout=300)  # 缓存5分钟 / Cache for 5 minutes

    def resolve(self, user):
        """解决警报 / Resolve alert"""
        self.is_active = False
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save() 