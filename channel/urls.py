# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from django.urls import path
from . import views

urlpatterns = [
	path('members/<int:channel_id>',views.ChannelMembersAPIView.as_view()),
	path('announcement/last/<int:channel_id>',views.ChannelAnnouncementsLastAPIView.as_view()),
]