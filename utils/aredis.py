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
	def __init__(self):
		self.key_muted_format = CHANNEL_MUTE_USER_KEY  # 频道禁言成员列表
		self.key_all_muted_format = CHANNEL_ALL_MUTE_KEY  # 频道是否全员禁言
		self.key_user_mute_format = USER_MUTE_KEY  # 用户禁言key

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
		return ChannelMember.objects.filter(channel_id=channel_id,
		                                    user_id=user_id).only('is_admin').first()

	@sync_to_async
	def get_muted_with_expire(self, channel_id):
		"""返回 [(user_id, muted_until)] 列表"""
		return list(
			ChannelMember.objects.filter(channel_id=channel_id, is_muted=True)
			.values_list('user_id', 'muted_until')
		)

	async def init_mute_cache(self, channel_id):
		set_key = self.key_muted_format.format(channel_id)
		all_key = self.key_all_muted_format.format(channel_id)
		muted = await self.get_muted_with_expire(channel_id)
		now = timezone.now()
		pipe = redis_client.pipeline()

		if muted:
			pipe.sadd(set_key, *[user_id for user_id, _ in muted])
			# 设置过期时间
			for user_id, expire_at in muted:
				if expire_at and expire_at > now:
					ttl = int((expire_at - now).total_seconds())
					mute_key = self.key_user_mute_format.format(channel_id, user_id)
					pipe.setex(mute_key, ttl, 1)
				else:
					# 过期时间无效，直接移除
					pipe.srem(set_key, user_id)

		# 全员禁言缓存
		channel_member = await self.get_first_channel_member(channel_id)
		if channel_member and hasattr(channel_member.channel, "is_all_muted"):
			pipe.set(all_key, int(channel_member.channel.is_all_muted))
		await pipe.execute()

	async def is_user_muted(self, channel_id, user_id):
		set_key = self.key_muted_format.format(channel_id)
		mute_key = self.key_user_mute_format.format(channel_id, user_id)

		if await redis_client.sismember(set_key, user_id):
			ttl = await redis_client.ttl(mute_key)
			if ttl and ttl > 0:
				expire_at = timezone.now() + timezone.timedelta(seconds=ttl)
				return True, expire_at
			else:
				# 过期自动清除
				await redis_client.srem(set_key, user_id)
		return False, None

	# 判断是否允许发言
	async def can_user_send(self, channel_id, user_id):
		set_key = self.key_muted_format.format(channel_id)
		all_key = self.key_all_muted_format.format(channel_id)

		if not await redis_client.exists(set_key) or not await redis_client.exists(all_key):
			await self.init_mute_cache(channel_id)

		member = await self.get_member_basic(channel_id, user_id)
		if not member:
			return False, None  # 非频道成员

		if member.is_admin:
			return False, None  # 管理员允许发言

		result, ex = await self.is_user_muted(channel_id, user_id)
		if result:
			return False, ex

		all_muted = await redis_client.get(all_key)
		return not (all_muted and int(all_muted) == 1), None

	async def mute_user(self, channel_id, user_id, seconds):
		set_key = self.key_muted_format.format(channel_id)
		mute_key = self.key_user_mute_format.format(channel_id, user_id)

		await redis_client.sadd(set_key, user_id)
		await redis_client.setex(mute_key, seconds, 1)
		# 同步更新数据库
		expire_time = timezone.now() + timedelta(seconds=seconds)
		await sync_to_async(ChannelMember.objects.filter(
			channel_id=channel_id, user_id=user_id
		).update)(
			is_muted=True,
			muted_until=expire_time
		)

	async def unmute_user(self, channel_id, user_id):
		set_key = self.key_muted_format.format(channel_id)
		mute_key = self.key_user_mute_format.format(channel_id, user_id)

		await redis_client.srem(set_key, user_id)
		await redis_client.delete(mute_key)

		# 同步更新数据库
		await sync_to_async(ChannelMember.objects.filter(
			channel_id=channel_id, user_id=user_id
		).update)(
			is_muted=False,
			muted_until=None
		)
