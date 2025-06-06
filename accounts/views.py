from django.shortcuts import render
from rest_framework.views import APIView
from .models import User

# Create your views here.

# 获取验证码
class GetCheckCode(APIView):
	def get(self, request):
		pass


# 注册接口
class RegisterUser(APIView):
	def post(self, request):
		pass


# 登录接口
class LoginUser(APIView):
	def post(self, request):
		pass


# 退出登录
class LogoutUser(APIView):
	def post(self, request):
		pass


# 忘记密码
class ForgetPassword(APIView):
	def post(self, request):
		pass
