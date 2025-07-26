from asgiref.sync import async_to_sync
from django.core.files.base import ContentFile
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Message, ChatFile
from .serializers import MessageSerializer
from rest_framework.response import Response
from utils.permission import IsChannelMemberPermission
from django.core.files.storage import default_storage
from utils.reponst import ChannelResponse
from utils.flake_id import get_snowflake_id
from utils.ws_response import WSResponse
from .tasks import save_file_and_create_message
from channels.layers import get_channel_layer
from djangoProject.configer import CHANNEL_NAME
import time


# 获取历史消息接口
class GetChannelHistoryMessagesAPIView(APIView):
	# permission_classes = [IsAuthenticated, IsChannelMemberPermission]

	def get(self, request, *args, **kwargs):
		# 获取前端传递的参数
		channel_id = int(request.query_params.get('channel_id'))
		page_size = int(request.query_params.get('page_size', 30))  # 每页30条消息
		if not channel_id:
			return Response({"error": "channel_id is required"}, status=400)
		min_id = request.query_params.get('min_id') # 当前页
		# 获取指定频道的消息
		if min_id:
			min_id = int(min_id)
			# 如果传入了最早的消息ID，从该ID之前的消息开始查询
			messages = Message.objects.select_related('channel').filter(channel_id=channel_id, id__lt=min_id).order_by(
				'-timestamp')[:page_size]
		else:
			# 否则，返回最新的消息
			messages = Message.objects.select_related('channel').filter(channel_id=channel_id).order_by('-timestamp')[
			           :page_size]

		# 序列化分页后的数据
		serializer = MessageSerializer(messages, many=True)
		data = {
			'timestamp': int(time.time()),  # 当前时间戳
			'message_id': messages[0].id if messages else None,  # 最新消息ID
			'channel_id': int(channel_id),
			'messages': serializer.data,  # 消息内容
		}

		return Response(data)


# 发送图片消息接口
class SendFileMessageAPIView(APIView):
	# permission_classes = [IsAuthenticated, IsChannelMemberPermission]
	parser_classes = (MultiPartParser, FormParser)

	def post(self, request):
		user = request.user
		user_id = user.id or 2
		channel_id = request.data.get("channel_id")  # 获取频道ID
		file = request.FILES.get('file')  # 获取文件数据
		temp_id = request.data.get('temp_id')
		if not file:
			return Response({"detail": "没有文件"})
		print(file.content_type)
		# 将文件保存到服务器
		message_id = get_snowflake_id()

		message_type = Message.FILE
		if 'image' in file.content_type:
			message_type = Message.IMAGE
		message = Message.objects.create(
			id=message_id,
			user_id=user_id,
			channel_id=channel_id,
			file=file,
			file_name=file.name,
			file_size=file.size,
			file_type=file.content_type,
			type=message_type
		)

		data = WSResponse.channel_image_broadcast(channel_id, user_id, message_id, message.file.url,temp_id)
		channel_layer = get_channel_layer()
		key_channel_name = CHANNEL_NAME.format(channel_id)
		async_to_sync(channel_layer.group_send)(key_channel_name, data)

		# save_file_and_create_message.delay(user.id, channel_id, message_id,file_temp_path)

		return ChannelResponse.success()
