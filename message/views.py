from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Message
from .serializers import MessageSerializer
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from utils.permission import IsChannelMemberPermission
import time

class MessagePagination(PageNumberPagination):
	page_size = 50  # 默认每页50条消息
	page_size_query_param = 'page_size'  # 客户端可以通过参数传递每页条数
	max_page_size = 100  # 最大每页条数


# 获取历史消息接口
class GetChannelHistoryMessagesAPIView(APIView):
	permission_classes = [IsAuthenticated, IsChannelMemberPermission]

	def get(self, request, *args, **kwargs):
		# 获取前端传递的参数
		channel_id = int(request.query_params.get('channel_id'))
		page_size = int(request.query_params.get('page_size', 50))  # 每页50条消息
		min_id = request.query_params.get('min_id')  # 当前页

		if not channel_id:
			return Response({"error": "channel_id is required"}, status=400)

		# 获取指定频道的消息
		if min_id:
			# 如果传入了最早的消息ID，从该ID之前的消息开始查询
			messages = Message.objects.filter(channel_id=channel_id, id__lt=min_id).order_by('-timestamp')[:page_size]
		else:
			# 否则，返回最新的消息
			messages = Message.objects.filter(channel_id=channel_id).order_by('-timestamp')[:page_size]

		# 序列化分页后的数据
		serializer = MessageSerializer(messages, many=True)
		data = {
			'timestamp': int(time.time()),  # 当前时间戳
			'message_id': messages[0].id if messages else None,  # 最新消息ID
			'channel_id': int(channel_id),
			'messages': serializer.data,  # 消息内容
		}

		return Response(data)
