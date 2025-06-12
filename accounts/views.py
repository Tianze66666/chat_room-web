from djangoProject import submit_task as pool_submit_task, settings
from rest_framework import status
from rest_framework.generics import GenericAPIView
import random
from django.core.mail import send_mail
from asgiref.sync import async_to_sync
from decoretas.limitcode import rate_limit_by_ip
from .serializers import UserSerializer, LoginSerializer, UpdateUserPasswordSerializer
from utils.aredis import async_set
from utils.sredis import ChangeTokenStatusMixin
from django.utils.timezone import now
from utils.reponst import UserResponse
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken,TokenError
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from rest_framework_simplejwt.tokens import BlacklistedToken,OutstandingToken
from utils.sredis import redis_client
# Create your views here.

# 获取验证码
class GetCheckCode(GenericAPIView):

	@rate_limit_by_ip()  #限流装饰器，一个ip一分钟一次
	def get(self, request, email):
		code = f"{random.randint(100000, 999999)}"
		async_to_sync(async_set)(f"verify_code:{email}", code, expire=300)
		pool_submit_task(self.safe_send_mail,
		                 '[天泽聊天室]验证码',
		                 f'您的验证码是：{code}，有效期5分钟，请勿泄露。',
		                 settings.EMAIL_HOST_USER,
		                 email
		                 )
		#秒返回，发送邮件任务放后台
		# return JsonResponse({"message": "验证码已发送，请注意查收"},
		#                     status=status.HTTP_200_OK)
		return UserResponse.success()

	@staticmethod
	def safe_send_mail(subject, message, from_email, recipient_list):
		if not isinstance(recipient_list, (list, tuple)):
			recipient_list = [recipient_list]
		try:
			send_mail(subject, message, from_email, recipient_list)
		except Exception as e:
			print("邮件发送异常:", e)


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
			return UserResponse.success(data='注册成功')
		return UserResponse.fail(data='注册失败，请稍后重试')


# 登录接口
class LoginUser(ChangeTokenStatusMixin, GenericAPIView):
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
		return UserResponse.success(data={
			"access": str(refresh.access_token),
			"refresh": str(refresh),
		})


# 退出登录
class LogoutUser(ChangeTokenStatusMixin, GenericAPIView):
	def post(self, request):
		if not request.user.is_authenticated:
			# return Response({'error': 'false'}, status=status.HTTP_400_BAD_REQUEST)
			return UserResponse.fail()
		pool_submit_task(
			self.change_user_token,
			request.user.id,
			None,
			None,
			1
		)
		# return Response({'message': 'ok'}, status=status.HTTP_200_OK)
		return UserResponse.success()

	@staticmethod
	def black_refresh_token(user_id):
		refresh_jti = redis_client.get(f"user:refresh:{user_id}")
		redis_client.delete(f"user:refresh:{user_id}")
		if refresh_jti:
			refresh_token_obj = OutstandingToken.objects.filter(jti=refresh_jti).first()
			if refresh_token_obj:
				BlacklistedToken.objects.get_or_create(token=refresh_token_obj)


# 忘记密码
class UpdatePassword(GenericAPIView):
	serializer_class = UpdateUserPasswordSerializer

	def post(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		# return Response({"message": "ok"}, status=status.HTTP_200_OK)
		return UserResponse.success()


class RefreshTokenGenericAPIView(ChangeTokenStatusMixin,GenericAPIView):
	serializer_class = TokenRefreshSerializer

	def post(self,request):
		# 验证refresh_token是否是最新的
		raw_refresh_token_str = request.data.get('refresh')
		if not raw_refresh_token_str:
			return UserResponse.fail(data='缺少refresh token', status=status.HTTP_400_BAD_REQUEST)
		try:
			old_refresh_token = RefreshToken(raw_refresh_token_str)
			old_refresh_jti = old_refresh_token['jti']
			user_id = old_refresh_token['user_id']
		except TokenError:
			return UserResponse.fail(data='无效的refresh token', status=status.HTTP_401_UNAUTHORIZED)
		latest_jti = redis_client.get(f"user:refresh:{user_id}")
		if not latest_jti == old_refresh_jti:
			return UserResponse.fail(data='无效的refresh token', status=status.HTTP_401_UNAUTHORIZED)

		# 重新签发token并记录
		serializer = self.get_serializer(data=request.data)
		try:
			serializer.is_valid(raise_exception=True)
		except InvalidToken as e:
			return UserResponse.fail(data='刷新令牌无效或已过期', status=status.HTTP_401_UNAUTHORIZED)
		except TokenError as e:
			return UserResponse.fail(data='无效的refresh_token')
		access_token_str = serializer.validated_data['access']
		access_token = AccessToken(access_token_str)
		access_jti = access_token['jti']
		refresh_token_str = serializer.validated_data['refresh']
		refresh_token = RefreshToken(refresh_token_str)
		refresh_jti = refresh_token['jti']
		pool_submit_task(self.change_user_token,user_id, refresh_jti, access_jti,0)
		return UserResponse.success(data={'access': access_token_str,
		                                  'refresh': refresh_token_str,})




