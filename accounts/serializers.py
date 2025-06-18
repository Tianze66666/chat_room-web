# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import authenticate
from .models import User
from utils.sredis import redis_client


class UserSerializer(serializers.ModelSerializer):
	password = serializers.CharField(write_only=True, required=True, )
	avatar_url = serializers.SerializerMethodField(read_only=True)  # 返回avatar图片的完整URL
	verify_code = serializers.CharField(write_only=True, required=True, max_length=6, min_length=6)
	email = serializers.EmailField(
		required=True,
		allow_blank=False,
		validators=[UniqueValidator(queryset=User.objects.all(), message='用户已经存在')]
	)

	class Meta:
		model = User
		fields = [
			'id', 'username', 'name', 'email', 'password', 'avatar', 'verify_code',
			'gender', 'birthday', 'phone', 'user_type', 'avatar_url'
		]
		extra_kwargs = {
			'name': {'required': True, },
			'phone': {'required': False, 'allow_null': True},
			'username': {'required': False, 'allow_null': True},
		}

	def validate(self, attrs):
		email = attrs.get('email')
		verify_code = redis_client.get(f'verify_code:{email}')
		if not verify_code:
			raise serializers.ValidationError({'verify_code': '请先获取验证码'},code=1001)
		if not verify_code == attrs.get('verify_code'):
			raise serializers.ValidationError({'verify_code': '验证码不一致'},code=1001)
		return attrs

	def get_avatar_url(self, obj):
		request = self.context.get('request')
		if obj.avatar and request:
			return request.build_absolute_uri(obj.avatar.url)
		return None

	def create(self, validated_data):
		validated_data.pop('verify_code')
		password = validated_data.pop('password')
		validated_data['username'] = validated_data.get('email')
		user = User(**validated_data)
		user.set_password(password)
		user.save()
		return user


class LoginSerializer(serializers.Serializer):
	email = serializers.CharField(required=False)
	password = serializers.CharField(required=False, write_only=True)
	username = serializers.CharField(required=False, write_only=True)
	verify_code = serializers.CharField(required=False, write_only=True,
	                                    max_length=6, min_length=6)

	def validate(self, attrs):
		email = attrs.get('email')
		password = attrs.get('password')
		verify_code = attrs.get('verify_code')
		username = attrs.get('username')
		# 密码登录
		if password:
			return self._verify_password(attrs, username, email, password)
		# 验证码登录
		if verify_code:
			return self._verify_code(attrs, username, email, verify_code)

		raise serializers.ValidationError("必须同时提供账号密码或使用验证码登录", code='1001')

	def _verify_password(self, attrs, username, email, password):
		user = authenticate(request=self.context.get('request'), username=username, password=password, email=email)
		if not user:
			raise serializers.ValidationError('用户名或密码错误', code='1001')
		if not user.is_active:
			raise serializers.ValidationError({'active': '该用户已被禁用'})
		attrs['user'] = user
		return attrs

	def _verify_code(self, attrs, username, email, verify_code):
		user = None
		# 没有邮箱，用户名登录，需要先获取该用户绑定的邮箱
		if not email:
			user = authenticate(request=self.context.get('request'),
			                    username=username,
			                    verify_login=True,
			                    require_email=True)
			if not user:
				raise serializers.ValidationError('用户名或密码错误', code='authorization')
			if not user.is_active:
				raise serializers.ValidationError("该用户已被禁用", code='authorization')
			email = user.email
		redis_code = redis_client.get(f'verify_code:{email}')
		if not redis_code:
			raise serializers.ValidationError({'verify_code': '请获取验证码'},code=1001)
		if not redis_code == verify_code:
			raise serializers.ValidationError({'verify_code': '验证码错误'},code=1001)
		if not user:
			user = authenticate(request=self.context.get('request'),
			                    username=username, email=email,
			                    verify_login=True)
		if not user:
			raise serializers.ValidationError('用户名或密码错误', code=1001)
		if not user.is_active:
			raise serializers.ValidationError("该用户已被禁用", code=1001)
		attrs['user'] = user
		redis_client.delete(f'verify_code:{email}')
		return attrs


class UpdateUserPasswordSerializer(serializers.Serializer):
	old_password = serializers.CharField(write_only=True, required=False)
	username = serializers.CharField(required=False, write_only=True)
	password = serializers.CharField(write_only=True, required=True, )
	verify_code = serializers.CharField(write_only=True, required=False, max_length=6, min_length=6)
	email = serializers.EmailField(required=False)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.user = None

	def validate(self, attrs):
		email = attrs.get('email')
		if email:
			try:
				user = User.objects.get(email=email)
				self.user = user
			except Exception:
				raise serializers.ValidationError({'email': '用户不存在'},code=1001)
		else:
			username = attrs.get('username')
			try:
				user = User.objects.get(username=username)
				self.user = user
				email = user.email
			except Exception:
				raise serializers.ValidationError({'email': '用户不存在'},code=1001)
		verify_code = attrs.get('verify_code')
		# 验证码修改
		if not attrs.get('old_password'):
			redis_code = redis_client.get(f'verify_code:{email}')
			if not redis_code:
				raise serializers.ValidationError({'verify_code': '请获取验证码'},code=1001)
			if not verify_code:
				raise serializers.ValidationError({'verify_code': '请带上验证码'},code=1001)
			if verify_code != redis_code:
				raise serializers.ValidationError({'verify_code': '验证码不一致'},code=1001)
			redis_client.delete(f'verify_code:{email}')
			return attrs
		if attrs.get('old_password') == attrs.get('password'):
			raise serializers.ValidationError({'password': '新旧密码不能一致'},code=1001)
		if not user.check_password(attrs.get('old_password')):
			raise serializers.ValidationError({'old_password': '旧密码错误'},code=1001)
		return attrs

	def save(self):
		user = self.user
		user.set_password(self.validated_data['password'])
		user.save()
		return user


class UserInfoSerializer(serializers.ModelSerializer):
	avatar_url = serializers.SerializerMethodField()
	gender = serializers.SerializerMethodField()

	class Meta:
		model = User
		fields = ['id', 'username', 'name', 'email', 'gender', 'birthday', 'phone', 'user_type', 'avatar_url']

	def get_avatar_url(self, obj):
		request = self.context.get('request')
		if obj.avatar and request:
			return request.build_absolute_uri(obj.avatar.url)
		return None

	@staticmethod
	def get_gender(obj):
		return obj.get_gender_display()
