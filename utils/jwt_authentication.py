# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from rest_framework_simplejwt.authentication import JWTAuthentication as SimpleJWTAuthentication
from rest_framework import exceptions


class JWTAuthentication(SimpleJWTAuthentication):
	def authenticate(self, request):
		# 调用父类的认证逻辑
		user_auth_tuple = super().authenticate(request)
		if user_auth_tuple is None:
			return None  # 认证失败或无token
		user, validated_token = user_auth_tuple
		return user, validated_token
