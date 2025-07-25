# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')

app = Celery('djangoProject')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()