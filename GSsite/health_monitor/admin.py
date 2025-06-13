from django.contrib import admin
from .models import UserProfile, Device, HealthData, HealthAlert, UserSettings

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Device)
admin.site.register(HealthData)
admin.site.register(HealthAlert)
admin.site.register(UserSettings) 