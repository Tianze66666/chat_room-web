# -*- coding: UTF-8 -*-
# @Author  ：天泽1344

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from utils.ws_response import WSResponse
from djangoProject.configer import USER_CHANNEL_KEY, CHANNEL_NAME
from channel.models import ChannelMember
from .message_router import dispatch_message
from utils.aredis import async_set, async_get ,async_delete


class ChatConsumer(AsyncWebsocketConsumer):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.user = None
		self.channels = []

	async def connect(self):
		await self.accept()
		# data = {
		# 	'code': 401,
		# }
		# await self.send(text_data=json.dumps(data,ensure_ascii=False))
		self.user = self.scope['user']
		if not self.user.is_authenticated:
			data = WSResponse.invalid_connect()
			await self.send(text_data=data)
			await self.close()
			return
		old_channel_name = await async_get(USER_CHANNEL_KEY.format(self.user.id))
		if old_channel_name and (old_channel_name != self.channel_name):
			# 踢掉老连接
			data = WSResponse.force_disconnect()
			await self.channel_layer.send(old_channel_name, data)

		print(f'用户{self.user.id}连接')

		self.channels = await self.get_user_channels(self.user.id)
		for channel in self.channels:
			group_name = CHANNEL_NAME.format(channel.get('id'))
			await self.channel_layer.group_add(group_name,self.channel_name)
			print(f'用户 {self.user.id}:{self.user.name} 加入 channel: {channel.get("id")}:{channel.get("name")}')
		data = WSResponse.init_connection(self.channels)
		await self.send(text_data=data)
		# redis配置用户唯一channel_id
		await async_set(USER_CHANNEL_KEY.format(self.user.id), self.channel_name)

	async def disconnect(self, close_code=400):
		# 离开所有 group
		user = self.scope['user']
		print(f'用户{user.id}离开')
		if hasattr(self, 'channels'):
			for channel in self.channels:
				group_name = f'channel_{channel.get("id")}'
				await self.channel_layer.group_discard(group_name, self.channel_name)
		# 删除redis存储的user_channel_id
		await async_delete(USER_CHANNEL_KEY.format(self.user.id))


	# 强制下线
	async def force_disconnect(self, event):
		await self.send(text_data=json.dumps(event, ensure_ascii=False))
		await self.close()

	async def receive(self, text_data=None, bytes_data=None):
		# 处理前端消息
		if not text_data:
			return
		data = json.loads(text_data)
		await dispatch_message(self, data)

	async def channel_chat(self, event):
		# if event.get('sender_id') == self.user.id:
		# 	return  # 跳过自己
		await self.send(text_data=json.dumps(event, ensure_ascii=False))

	async def mute_notice(self,event):
		await self.send(text_data=json.dumps(event, ensure_ascii=False))


	# 获取用户的所有加入频道   
	@database_sync_to_async
	def get_user_channels(self, user_id):
		standardized_channels = []
		channels = (ChannelMember.objects.select_related('channel')
		            .filter(user__id=user_id)
		            .values('channel__id','channel__name'))
		for channel in channels:
			data = {
				'id': channel.get('channel__id'),
				'name': channel.get('channel__name'),
			}
			standardized_channels.append(data)
		return standardized_channels
