# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
	def authenticate(self, request, username=None, password=None, verify_login=False,**kwargs):
		email = kwargs.get('email') or username  # 兼容username或email登录
		if not verify_login:
			try:
				user = User.objects.only('id', 'password', 'is_active').get(email=email)
			except User.DoesNotExist:
				return None
			if user.check_password(password):
				return user
		if verify_login:
			try:
				user = User.objects.only('id', 'is_active').get(email=email)
			except User.DoesNotExist:
				return None
			return user
		return None
