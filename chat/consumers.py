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
		await self.send(text_data=json.dumps(
			{
				'hello': 'nihao'
			}
		))


#
# class ChatConsumer(AsyncWebsocketConsumer):
#
# 	async def connect(self):
# 		self.user = self.scope["user"]
#
# 		if not self.user.is_authenticated:
# 			await self.close()
# 			return
#
# 		# 获取用户加入的所有频道ID
# 		self.channel_ids = await sync_to_async(list)(
# 			ChannelMember.objects.filter(user_id=self.user.id).values_list("channel_id", flat=True)
# 		)
#
# 		# 加入每个频道对应的 group
# 		for channel_id in self.channel_ids:
# 			await self.channel_layer.group_add(f"channel_{channel_id}", self.channel_name)
#
# 		await self.accept()
#
# 	async def disconnect(self, close_code):
# 		# 离开所有 group
# 		for channel_id in getattr(self, "channel_ids", []):
# 			await self.channel_layer.group_discard(f"channel_{channel_id}", self.channel_name)
#
# 	async def receive(self, text_data=None, bytes_data=None):
# 		"""
# 		处理来自前端发送的消息：
# 		{
# 			"channel_id": 123,
# 			"message": "hello world"
# 		}
# 		"""
# 		data = json.loads(text_data)
# 		channel_id = data.get("channel_id")
# 		message = data.get("message")
#
# 		if not channel_id or not message:
# 			return
# 		# 判断用户是否真的加入了这个频道（可选校验）
# 		if channel_id not in self.channel_ids:
# 			return
# 		# 广播消息给对应频道 group
# 		await self.channel_layer.group_send(
# 			f"channel_{channel_id}",
# 			{
# 				"type": "chat.message",  # 注意：必须匹配 handler 方法名
# 				"user": self.user.username,
# 				"message": message,
# 				"channel_id": channel_id,
# 			}
# 		)
#
# 	async def chat_message(self, event):
# 		"""
# 		接收 group 广播的消息，推送给前端
# 		"""
# 		await self.send(text_data=json.dumps({
# 			"user": event["user"],
# 			"message": event["message"],
# 			"channel_id": event["channel_id"]
# 		}))