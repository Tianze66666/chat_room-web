from djangoProject import submit_task as pool_submit_task
from rest_framework import status
from rest_framework.generics import GenericAPIView
import random
from django.core.mail import send_mail
from django.http.response import JsonResponse
from asgiref.sync import async_to_sync
from decoretas.limitcode import rate_limit_by_ip
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from .serializers import UserSerializer, LoginSerializer,UpdateUserPasswordSerializer
from utils.aredis import async_set
from utils.sredis import ChangeTokenStatusMixin
from django.utils.timezone import now


# Create your views here.

# 获取验证码
class GetCheckCode(GenericAPIView):

	@rate_limit_by_ip()  #限流装饰器，一个ip一分钟一次
	def get(self, request, email):
		code = f"{random.randint(100000, 999999)}"
		async_to_sync(async_set)(f"verify_code:{email}", code, expire=300)
		pool_submit_task(send_mail,
		                 '[天泽聊天室]验证码',
		                 f'您的验证码是：{code}，有效期5分钟，请勿泄露。',
		                 None,
		                 [email]
		                 )
		#秒返回，发送邮件任务放后台
		return JsonResponse({"message": "验证码已发送，请注意查收"},
		                    status=status.HTTP_200_OK)


# async def get_code(request, email):
# 	code = f"{random.randint(100000, 999999)}"
# 	await async_set(f"verify_code:{email}", code, expire=300)
# 	subject = '天泽聊天室验证码'
# 	message = f'您的验证码是：{code}，有效期5分钟，请勿泄露。'
# 	from_email = None
# 	recipient_list = [email]
# 	await asyncio.create_task(send_async_email(subject, message, from_email, recipient_list))
# 	return Response({"message": "验证码已发送，请注意查收"}, status=status.HTTP_200_OK)



# 注册接口
class RegisterUser(GenericAPIView):
	serializer_class = UserSerializer

	def post(self, request):
		serializer = self.get_serializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response({"message": "注册成功"}, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 登录接口
class LoginUser(ChangeTokenStatusMixin,GenericAPIView):
	serializer_class = LoginSerializer

	def post(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.validated_data['user']
		user.last_login = now()
		user.save(update_fields=['last_login'])
		refresh = RefreshToken.for_user(user)
		# 保存最新的jti
		refresh_jti = refresh['jti']
		access_jti = refresh.access_token['jti']
		pool_submit_task(self.change_user_token,
		                 user.id,
		                 refresh_jti,
		                 access_jti,
		                 )
		return Response({
			"access": str(refresh.access_token),
			"refresh": str(refresh),
		}, status=status.HTTP_200_OK)



# 退出登录
class LogoutUser(ChangeTokenStatusMixin,GenericAPIView):
	def post(self, request):

		if not request.user.is_authenticated:
			return Response({'error':'false'}, status=status.HTTP_400_BAD_REQUEST)
		pool_submit_task(
			self.change_user_token,
			request.user.id
		)
		return Response({'message':'ok'},status = status.HTTP_200_OK)


# 忘记密码
class UpdatePassword(GenericAPIView):
	serializer_class = UpdateUserPasswordSerializer
	def post(self, request):
		serializer=self.get_serializer(data = request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response({"message":"ok"},status=status.HTTP_200_OK)

