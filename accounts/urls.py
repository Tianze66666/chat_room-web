# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from django.urls import path
from . import views

urlpatterns = [
	path('getcode/', views.GetCheckCode.as_view(),),
	path('login/', views.LoginUser.as_view(),),
	path('register/', views.RegisterUser.as_view(),),
	path('logout/', views.LogoutUser.as_view(),),
	path('forget/',views.ForgetPassword.as_view())
]