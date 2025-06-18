# -*- coding: UTF-8 -*-
# @Author  ：天泽1344

import redis.asyncio as redis
from django.conf import settings
from djangoProject.configer import CHANNEL_MEMBERS, CHANNEL_MUTED, CHANNEL_ALL_MUTED
from chat.models import ChannelMember
from asgiref.sync import sync_to_async

redis_client = redis.Redis(
	host=settings.REDIS_CACHE_CONFIG['host'],
	port=settings.REDIS_CACHE_CONFIG['port'],
	db=settings.REDIS_CACHE_CONFIG['db'],
	password=settings.REDIS_CACHE_CONFIG['password'],
	decode_responses=settings.REDIS_CACHE_CONFIG['decode_responses'],
)


async def async_set(key, value, expire=None):
	await redis_client.set(key, value, ex=expire)


async def async_get(key):
	return await redis_client.get(key)


async def async_delete(key):
	await redis_client.delete(key)


class ChannelMemberCache:

	@staticmethod
	def _key(channel_id):
		return CHANNEL_MEMBERS.format(channel_id)

	@staticmethod
	async def add_member(channel_id, user_id):
		await redis_client.sadd(ChannelMemberCache._key(channel_id), user_id)

	@staticmethod
	async def add_members(channel_id, user_ids):
		if user_ids:
			await redis_client.sadd(ChannelMemberCache._key(channel_id), *user_ids)

	@staticmethod
	async def remove_member(group_id, user_id):
		await redis_client.srem(ChannelMemberCache._key(group_id), user_id)

	@staticmethod
	async def get_members(channel_id):
		return await redis_client.smembers(ChannelMemberCache._key(channel_id))

	@staticmethod
	async def is_member(channel_id, user_id):
		return await redis_client.sismember(ChannelMemberCache._key(channel_id), user_id)

	@staticmethod
	async def clear_channel(channel_id):
		await redis_client.delete(ChannelMemberCache._key(channel_id))

	@staticmethod
	async def set_expire(channel_id, seconds):
		await redis_client.expire(ChannelMemberCache._key(channel_id), seconds)


class ChannelMuteCache:
	@sync_to_async
	def get_muted_ids(self, channel_id):
		return list(
			ChannelMember.objects.filter(channel_id=channel_id, is_muted=True)
			.values_list('user_id', flat=True)
		)

	@sync_to_async
	def get_first_channel_member(self, channel_id):
		return ChannelMember.objects.filter(channel_id=channel_id).select_related('channel').first()

	@sync_to_async
	def get_member_basic(self, channel_id, user_id):
		return ChannelMember.objects.filter(channel_id=channel_id, user_id=user_id).only('is_admin').first()

	async def init_mute_cache(self, channel_id):
		key_muted = CHANNEL_MUTED.format(channel_id)
		# 单人禁言
		muted_ids = await self.get_muted_ids(channel_id)
		if muted_ids:
			await redis_client.sadd(key_muted, *muted_ids)
		# 全员禁言
		channel_member = await self.get_first_channel_member(channel_id)
		if channel_member and hasattr(channel_member.channel, "is_all_muted"):
			await redis_client.set(CHANNEL_ALL_MUTED.format(channel_id), int(channel_member.channel.is_all_muted))

	# 判断是否允许发言
	async def can_user_send(self, channel_id, user_id):
		if not await redis_client.exists(CHANNEL_MUTED.format(channel_id)):
			await self.init_mute_cache(channel_id)
		member = await self.get_member_basic(channel_id, user_id)
		if not member:
			return False  # 非成员
		if await redis_client.sismember(CHANNEL_MUTED.format(channel_id), user_id):
			return False
		if member.is_admin:
			return True  # 管理员可发言
		all_muted = await redis_client.get(CHANNEL_ALL_MUTED.format(channel_id))
		if int(all_muted) == 1:
			return False
		return True
