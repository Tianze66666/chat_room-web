# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from rest_framework_simplejwt.authentication import JWTAuthentication as SimpleJWTAuthentication
from commom.sredis import redis_client
from djangoProject.configer import USER_INFO_KEY


class JWTAuthentication(SimpleJWTAuthentication):
	def authenticate(self, request):
		# 调用父类的认证逻辑
		user_auth_tuple = super().authenticate(request)
		if user_auth_tuple is None:
			return None  # 认证失败或无token
		user, validated_token = user_auth_tuple
		key = USER_INFO_KEY.format(user.id)
		current_access_jti = redis_client.hget(key, 'access_jti')
		if validated_token['jti'] != current_access_jti:
			# raise AuthenticationFailed('Token 已失效，请重新登录',code=1003)
			return None  # token过期
		return user, validated_token

