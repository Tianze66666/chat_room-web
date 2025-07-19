# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from django.urls import path
from . import views

urlpatterns = [
	path('history/',views.GetChannelHistoryMessagesAPIView.as_view())
]