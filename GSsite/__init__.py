from __future__ import absolute_import, unicode_literals

# 这个文件可以为空，或者只包含版本信息
__version__ = '0.1.0'

from .celery_app import app as celery_app

__all__ = ('celery_app',)
