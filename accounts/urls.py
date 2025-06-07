# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from django.urls import path
from . import views

urlpatterns = [
	path('getcode/<ema:email>', views.GetCheckCode.as_view()),
	path('login/', views.LoginUser.as_view(),),
	path('register/', views.RegisterUser.as_view(),),
	path('loginout/', views.LogoutUser.as_view(),),
	path('updatepassword/',views.UpdatePassword.as_view())
]