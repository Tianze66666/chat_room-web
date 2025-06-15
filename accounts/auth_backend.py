# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


User = get_user_model()


class EmailBackend(ModelBackend):
	def authenticate(self, request, username=None, password=None, verify_login=False,require_email=False,**kwargs):
		login_identifier = kwargs.get('email') if kwargs.get('email') else username
		if not verify_login:
			try:
				user = User.objects.only('id', 'password', 'is_active').get(Q(email=login_identifier)|Q(username = login_identifier))
			except User.DoesNotExist:
				return None
			if user.check_password(password):
				return user
		if verify_login:
			try:
				if require_email:
					user = User.objects.only('id', 'is_active','email').get(username = login_identifier)
				else:
					user = User.objects.only('id', 'is_active',).get(email=login_identifier)
			except User.DoesNotExist:
				return None
			return user
		return None
