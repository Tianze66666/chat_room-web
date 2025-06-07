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

	@staticmethod
	def validate_verify_code(attrs):
		email = attrs.get('email')
		verify_code = redis_client.get(f'verify_code:{email}')
		if not verify_code:
			raise serializers.ValidationError({'verify_code': '请先获取验证码'})
		if not verify_code == attrs.get('verify_code'):
			raise serializers.ValidationError({'verify_code': '验证码不一致'})
		return attrs

	def get_avatar_url(self, obj):
		request = self.context.get('request')
		if obj.avatar and request:
			return request.build_absolute_uri(obj.avatar.url)
		return None

	def create(self, validated_data):
		validated_data.pop('verify_code')
		password = validated_data.pop('password')
		user = User(**validated_data)
		user.set_password(password)
		user.save()
		return user


class LoginSerializer(serializers.Serializer):
	email = serializers.CharField(required=True)
	password = serializers.CharField(required=True, write_only=True)

	def validate(self, attrs):
		email = attrs.get('email')
		password = attrs.get('password')
		if email and password:
			user = authenticate(request=self.context.get('request'), password=password, email=email)
			if not user:
				raise serializers.ValidationError("用户名或密码错误", code='authorization')
			if not user.is_active:
				raise serializers.ValidationError("该用户已被禁用", code='authorization')
			attrs['user'] = user  # 后续可以使用
			return attrs
		raise serializers.ValidationError("必须同时提供用户名和密码", code='authorization')


class UpdateUserPasswordSerializer(serializers.Serializer):
	old_password = serializers.CharField(write_only=True, required=False)
	password = serializers.CharField(write_only=True, required=True, )
	verify_code = serializers.CharField(write_only=True, required=False, max_length=6, min_length=6)
	email = serializers.EmailField(
		required=True,
		allow_blank=False,
	)
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.user = None

	def validate(self, attrs):
		email = attrs.get('email')
		try:
			user = User.objects.get(email=attrs.get('email'))
			self.user = user
		except Exception as e:
			raise serializers.ValidationError({'email': '用户不存在'})
		verify_code = attrs.get('verify_code')
		if not attrs.get('old_password'):
			redis_code = redis_client.get(f'verify_code:{email}')
			if not redis_code:
				raise serializers.ValidationError({'verify_code': '请获取验证码'})
			if not verify_code:
				raise serializers.ValidationError({'verify_code': '请带上验证码'})
			if verify_code != redis_code:
				raise serializers.ValidationError({'verify_code': '验证码不一致'})
			redis_client.delete(f'verify_code:{email}')
			return attrs
		if attrs.get('old_password') == attrs.get('password'):
			raise serializers.ValidationError({'password': '新旧密码不能一致'})
		if not user.check_password(attrs.get('old_password')):
			raise serializers.ValidationError({'old_password': '旧密码错误'})
		return attrs

	def save(self):
		user = self.user
		user.set_password(self.validated_data['password'])
		user.save()
		return user
