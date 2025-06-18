# -*- coding: UTF-8 -*-
# @Author  ：天泽1344


from django.urls import re_path
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # re_path(r'ws/chat/(?P<usera_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    path(r'ws/chat/',consumers.ChatConsumer.as_asgi())
]