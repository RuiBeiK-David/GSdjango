# ... existing code ...
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"


STATICFILES_DIRS = [
    BASE_DIR / "health_monitor" / "static",
]
# ... existing code ... 