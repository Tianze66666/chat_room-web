# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from urllib.parse import parse_qs
from channels.auth import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken,TokenBackendExpiredToken,TokenBackendError
from jwt.exceptions import InvalidSignatureError
from django.contrib.auth import get_user_model
from django.conf import settings
from asgiref.sync import sync_to_async
from utils.aredis import redis_client
from djangoProject.configer import USER_INFO_KEY


# channel-jwt认证中间件
class JWTAuthMiddleware(BaseMiddleware):
	async def __call__(self, scope, receive, send):
		# 从 query string 中获取 token
		query_string = parse_qs(scope["query_string"].decode())
		token = query_string.get("token", [None])[0]
		if not token:
			scope['user'] = AnonymousUser()
			# return await super.__call__(scope, receive, send)
			return await self.inner(scope, receive, send)
		# 尝试调用simple_jwt的验证后端验证
		try:
			token_backend = TokenBackend(algorithm='HS256', signing_key=settings.SECRET_KEY)
			validated_data = token_backend.decode(token, verify=True)
			user_id = validated_data.get("user_id")
			if await self.check_jti(user_id, validated_data.get('jti')):
				scope["user"] = await self.get_user(user_id)
			else:
				scope["user"] = AnonymousUser()
		except (TokenError, InvalidToken,
		        TokenBackendExpiredToken,TokenBackendExpiredToken,
		        InvalidSignatureError,TokenBackendError) as e:
			print(f"Token 验证失败: {e}")
			scope["user"] = AnonymousUser()
		# return await super().__call__(scope, receive, send)
		return await self.inner(scope, receive, send)

	@staticmethod
	async def get_user(user_id):
		user_model = get_user_model()
		try:
			return await sync_to_async(user_model.objects.get)(id=user_id)
		except user_model.DoesNotExist:
			return AnonymousUser()

	@staticmethod
	async def check_jti(user_id, jti):
		key = USER_INFO_KEY.format(user_id)
		return (await redis_client.hget(key,'access_jti')) == jti
