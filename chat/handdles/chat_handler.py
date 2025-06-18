# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from utils.ws_response import WSResponse
from djangoProject.configer import GROUP_NAME

class GroupChatHandles(object):
	def __init__(self, consumer, data):
		self.consumer = consumer
		self.data = data
		self.to_map = {
			'group': self._group_chat,
			'private': self._private_chat
		}

	async def handle(self):
		print('收到消息', self.data)
		to = self.data.get('to')
		if not to or (to not in self.to_map):
			data = WSResponse.type_error()
			await self.consumer.send(data)
			return
		await self.to_map.get(to)()

	# 群组聊天
	async def _group_chat(self):
		group_id = self.data.get("group_id")
		message = self.data.get("message")
		user = self.consumer.scope["user"]
		if not group_id or not message:
			await self.consumer.send(WSResponse.fail())
			return

		# TODO:判断是否是该频道成员
		# TODO:消息队列保存message实现数据持久化
		group_name = GROUP_NAME.format(group_id)
		data = WSResponse.group_chat_broadcast(group_id,user.id,message)
		await self.consumer.channel_layer.group_send(group_name,data)


	# 私聊
	async def _private_chat(self):
		pass
