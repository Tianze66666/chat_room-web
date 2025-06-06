# -*- coding: UTF-8 -*-
# @Author  ：天泽1344


from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<channel_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
]