# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from djangoProject.configer import USER_INFO_KEY
from django.conf import settings
from utils.sredis import redis_client


class ChangeTokenStatusMixin:
	def __init__(self):
		self.ex_access = None
		self.ex_refresh = None
		self.key = None
		self.mode_dic = None

	def _ensure_initialized(self):
		"""懒加载初始化方法，仅在首次使用时执行一次"""
		if self.ex_access is None:
			self.ex_access = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
			self.ex_refresh = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
			self.key = USER_INFO_KEY
			self.mode_dic = {
				0: self.set_token,
				1: self.delete_token,
			}

	def change_user_token(self, user_id, refresh_jti=None, access_jti=None, type=0):
		self._ensure_initialized()
		try:
			self.mode_dic.get(type)(user_id, refresh_jti, access_jti)
		except Exception as e:
			print(e)

	def set_token(self, user_id, refresh_jti=None, access_jti=None, *args, **kwargs):
		key = self.key.format(user_id)
		pipe = redis_client.pipeline()
		if refresh_jti:
			pipe.hset(key, mapping={
				"refresh_jti": refresh_jti,
			})
		if access_jti:
			pipe.hset(key, mapping={
				"access_jti": access_jti,
			})
		pipe.execute()
		pipe.expire(key, self.ex_refresh)
		return

	def delete_token(self, user_id, *args, **kwargs):
		key = self.key.format(user_id)
		redis_client.hdel(key, "refresh_jti", "access_jti")
		return
