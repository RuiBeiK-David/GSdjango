from rest_framework import serializers
from .models import UserProfile, Device, HealthData, HealthAlert
from django.contrib.auth.models import User

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['name', 'gender', 'phone_number', 'id_number']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'profile']

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['device_id', 'name', 'is_active', 'last_seen']

class HealthDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthData
        fields = ['timestamp', 'heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'blood_oxygen', 'temperature']

class HealthAlertSerializer(serializers.ModelSerializer):
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    device_name = serializers.CharField(source='device.name', read_only=True)

    class Meta:
        model = HealthAlert
        fields = [
            'id', 
            'alert_type', 
            'alert_type_display',
            'message', 
            'timestamp', 
            'is_active',
            'device',
            'device_name',
        ]
        read_only_fields = ['device'] 