# -*- coding: UTF-8 -*-
# @Author  ：天泽1344

import redis.asyncio as redis
from django.conf import settings
from djangoProject.configer import CHANNEL_MEMBERS, CHANNEL_ALL_MUTE_KEY, CHANNEL_MUTE_USER_KEY, USER_MUTE_KEY
from channel.models import ChannelMember
from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import timedelta

redis_client = redis.Redis(
	host=settings.REDIS_CACHE_CONFIG['host'],
	port=settings.REDIS_CACHE_CONFIG['port'],
	db=settings.REDIS_CACHE_CONFIG['db'],
	password=settings.REDIS_CACHE_CONFIG['password'],
	decode_responses=settings.REDIS_CACHE_CONFIG['decode_responses'],
)


async def async_set(key, value, expire=None):
	if not expire:
		await redis_client.set(key, value)
		return True
	await redis_client.set(key, value,ex=expire)


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


