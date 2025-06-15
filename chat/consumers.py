# -*- coding: UTF-8 -*-
# @Author  ：天泽1344

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import ChannelMember


class ChatConsumer(AsyncWebsocketConsumer):

	async def connect(self):
		await self.accept()
		print('用户连接')


	async def disconnect(self, close_code):
		# 离开所有 group
		print('用户离开')

	async def receive(self, text_data=None, bytes_data=None):
		"""
		处理来自前端发送的消息：
		{
			"channel_id": 123,
			"message": "hello world"
		}
		"""
		data = json.loads(text_data)
		print('收到消息',data)
		await self.send(text_data=json.dumps(data))

