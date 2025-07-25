from djangoProject import submit_task as pool_submit_task, settings
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
import random
from django.core.mail import send_mail
from asgiref.sync import async_to_sync
from decoretas.limitcode import rate_limit_by_ip
from .serializers import (UserSerializer,
                          LoginSerializer,
                          UpdateUserPasswordSerializer,
                          UserInfoSerializer)
from utils.aredis import async_set
from .Mixin_utils import ChangeTokenStatusMixin
from django.utils.timezone import now
from utils.reponst import UserResponse
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.tokens import BlacklistedToken, OutstandingToken
from utils.sredis import redis_client
from .models import User
from djangoProject.configer import (VERIFY_CODE_EXP,
                                    EMAIL_VERIFY_CODE_MESSAGE,
                                    EMAIL_VERIFY_CODE_SUBJECT,
                                    CHANNEL_MEMBERS,
                                    USER_INFO_KEY)
from channel.models import ChannelMember, Channel


# 获取验证码
class GetCheckCode(GenericAPIView):

	@rate_limit_by_ip()  # 限流装饰器，一个ip一分钟一次
	def get(self, request, email=None, username=None):
		verify_code = f"{random.randint(100000, 999999)}"
		if email:
			pool_submit_task(self.safe_send_mail, email, verify_code)
			return UserResponse.success()
		elif username:
			try:
				user = User.objects.only('email', 'is_active').get(username=username)
			except User.DoesNotExist:
				return UserResponse.fail(message='用户不存在')
			if not user.is_active:
				return UserResponse.fail(message='用户被封禁')
			email = user.email
			pool_submit_task(self.safe_send_mail, email, verify_code)
			return UserResponse.success()
		return UserResponse.fail()

	@staticmethod
	def safe_send_mail(email, verify_code):
		subject = EMAIL_VERIFY_CODE_SUBJECT
		message = EMAIL_VERIFY_CODE_MESSAGE
		from_email = settings.EMAIL_HOST_USER
		recipient_list = email
		async_to_sync(async_set)(f"verify_code:{email}", verify_code, expire=VERIFY_CODE_EXP)
		if not isinstance(recipient_list, (list, tuple)):
			recipient_list = [recipient_list]
		try:
			send_mail(subject, message.format(verify_code), from_email, recipient_list)
		except Exception as e:
			print("邮件发送异常:", e)


# 注册接口
class RegisterUser(GenericAPIView):
	serializer_class = UserSerializer

	def post(self, request):
		serializer = self.get_serializer(data=request.data)
		if serializer.is_valid():
			user = serializer.save()
			default_channel = Channel.objects.get(id=1)
			try:
				ChannelMember.objects.create(user=user, channel=default_channel)
				# redis更新
				if redis_client.exists(CHANNEL_MEMBERS.format(1)):
					redis_client.sadd(CHANNEL_MEMBERS.format(1), user.id)
				return UserResponse.success(data='注册成功')
			except Exception as e:
				print(e)
		data = next(iter(serializer.errors.values()))[0]
		if data == '用户已经存在':
			return UserResponse.fail(code=1004, data=data)
		else:
			return UserResponse.fail(code=1001, data=data)


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
		access = refresh.access_token
		# 保存最新的jti
		refresh_jti = refresh['jti']
		access_jti = access['jti']
		pool_submit_task(self.change_user_token,
		                 user.id,
		                 refresh_jti,
		                 access_jti,
		                 )
		return UserResponse.success(data={
			"access": str(access),
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
		pool_submit_task(
			self.black_refresh_token,
			request.user.id
		)
		# return Response({'message': 'ok'}, status=status.HTTP_200_OK)
		return UserResponse.success()

	@staticmethod
	def black_refresh_token(user_id):
		key = USER_INFO_KEY.format(user_id)
		refresh_jti = redis_client.hget(key, "refresh_jti")
		if refresh_jti:
			redis_client.hdel(key, "refresh_jti")
			refresh_token_obj = OutstandingToken.objects.filter(jti=refresh_jti).first()
			if refresh_token_obj:
				BlacklistedToken.objects.get_or_create(token=refresh_token_obj)


# 修改密码
class UpdatePassword(GenericAPIView):
	serializer_class = UpdateUserPasswordSerializer

	def post(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return UserResponse.success()


class RefreshTokenGenericAPIView(ChangeTokenStatusMixin, GenericAPIView):
	serializer_class = TokenRefreshSerializer

	def post(self, request):
		# 验证refresh_token是否是最新的
		raw_refresh_token_str = request.data.get('refresh')
		if not raw_refresh_token_str:
			return UserResponse.fail(data='缺少refresh token')
		try:
			old_refresh_token = RefreshToken(raw_refresh_token_str)
			old_refresh_jti = old_refresh_token['jti']
			user_id = old_refresh_token['user_id']
		except TokenError:
			return UserResponse.fail(code=1003, data='无效的refresh token')
		key = USER_INFO_KEY.format(user_id)
		latest_jti = redis_client.hget(key,'refresh_jti')
		if not latest_jti == old_refresh_jti:
			return UserResponse.fail(code=1003, data='无效的refresh token')

		# 重新签发token并记录
		serializer = self.get_serializer(data=request.data)
		try:
			serializer.is_valid(raise_exception=True)
		except InvalidToken:
			return UserResponse.fail(code=1003, data='刷新令牌无效或已过期')
		except TokenError:
			return UserResponse.fail(code=1003, data='无效的refresh_token')
		access_token_str = serializer.validated_data['access']
		access_token = AccessToken(access_token_str)
		access_jti = access_token['jti']
		refresh_token_str = serializer.validated_data['refresh']
		refresh_token = RefreshToken(refresh_token_str)
		refresh_jti = refresh_token['jti']
		pool_submit_task(self.change_user_token, user_id, refresh_jti, access_jti, 0)
		return UserResponse.success(data={'access': access_token_str,
		                                  'refresh': refresh_token_str, })


# 获取用户信息
class GetUserInfoRetrieveAPIView(RetrieveAPIView):
	serializer_class = UserInfoSerializer
	permission_classes = [IsAuthenticated]

	def get_object(self):
		return self.request.user
