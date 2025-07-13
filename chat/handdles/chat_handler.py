# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from utils.ws_response import WSResponse
from utils.flake_id import get_snowflake_id
from djangoProject.configer import CHANNEL_NAME, CHANNEL_MEMBERS
from chat.tasks import save_message_async
from utils.aredis import redis_client
from utils.channel_mute_util import ChannelMuteCache
from utils.channel_member import get_channel_member_ids
from channel.models import ChannelMember
from asgiref.sync import sync_to_async


class GroupChatHandles(object):
	def __init__(self, consumer, data):
		self.consumer = consumer
		self.data = data
		self.to_map = {
			'group': self._group_chat,
			'private': self._private_chat
		}
		self.channel_mute_cache = ChannelMuteCache()

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
		channel_id = self.data.get("channel_id")
		message = self.data.get("message")
		user = self.consumer.scope["user"]
		if not channel_id or not message:
			await self.consumer.send(WSResponse.fail())
			return
		# 判断是否是该频道成员
		if not await self._user_in_channel(channel_id, user.id):
			await self.consumer.send(WSResponse.fail(message='非频道成员'))
			return
		# 判断是否禁言
		result, ex = await self.channel_mute_cache.can_user_send(channel_id, user.id)
		if not result:
			if ex == 0:
				await self.consumer.send(WSResponse.user_is_mute(message='全群禁言'))
				return
			await self.consumer.send(WSResponse.user_is_mute(ex=ex))
			return
		# 发送消息
		message_id = get_snowflake_id()
		channel_name = CHANNEL_NAME.format(channel_id)
		data = WSResponse.group_chat_broadcast(channel_id,
		                                       user.id,
		                                       message,
		                                       message_id,
		                                       user.avatar,
		                                       user.name)
		await self.consumer.channel_layer.group_send(channel_name, data)
		# 消息队列保存message实现数据持久化
		save_message_async.delay(channel_id, user.id, message_id, message)

	# 私聊
	async def _private_chat(self):
		pass

	@staticmethod
	async def _user_in_channel(channel_id, user_id):
		key = CHANNEL_MEMBERS.format(channel_id)
		if not await redis_client.exists(key):
			member_ids = await get_channel_member_ids(channel_id)
			if not member_ids:
				return False
			await redis_client.sadd(key, *member_ids)
		return await redis_client.sismember(key, user_id)
