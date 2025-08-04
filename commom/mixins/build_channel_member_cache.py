# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from channel.models import Channel, ChannelMember
from commom.aredis import redis_client as a_redis_client
from djangoProject.configer import CHANNEL_MEMBER_ROLES
from commom.sredis import redis_client


class BuildChannelMemberCacheMixin:

	@staticmethod
	def build_and_cache_channel_roles(channel_id):
		"""
		从数据库获取频道主与管理员信息，并缓存到 Redis 的 CHANNEL_MEMBER_ROLES:{channel_id}
		"""
		roles_map = {}
		roles_map_key = CHANNEL_MEMBER_ROLES
		# 获取频道主
		channel = Channel.objects.filter(id=channel_id).only('owner_id').first()
		if channel:
			roles_map[str(channel.owner_id)] = int(2)

		# 获取管理员（ChannelMember 表中 is_admin=True）
		admin_ids = ChannelMember.objects.filter(
			channel_id=channel_id,
			is_admin=True
		).values_list('user_id', flat=True)
		for uid in admin_ids:
			uid_str = str(uid)
			# 避免覆盖频道主
			if uid_str not in roles_map:
				roles_map[uid_str] = int(1)
		# 写入 Redis
		if roles_map:
			redis_client.hset(roles_map_key.format(channel_id), mapping=roles_map)
			redis_client.expire(roles_map_key.format(channel_id), 300)  # 设置过期时间为 5 分钟
		return roles_map


class AsyncBuildChannelMemberCacheMixin:

	@staticmethod
	async def build_and_cache_channel_roles(channel_id):
		"""
		异步方式：从数据库获取频道主与管理员信息，并缓存到 Redis 的 CHANNEL_MEMBER_ROLES:{channel_id}
		"""
		roles_map = {}
		roles_map_key = CHANNEL_MEMBER_ROLES
		# 获取频道主（用 async ORM）
		channel = await Channel.objects.filter(id=channel_id).only('owner_id').afirst()
		if channel:
			roles_map[str(channel.owner_id)] = 2  # 2 = owner

		# 获取管理员列表（异步 values_list）
		async for member in ChannelMember.objects.filter(channel_id=channel_id, is_admin=True):
			uid_str = str(member.user_id)
			if uid_str not in roles_map:
				roles_map[uid_str] = 1

		# 写入 Redis（使用异步 Redis 客户端）
		if roles_map:
			redis_key = roles_map_key.format(channel_id)
			await a_redis_client.hset(redis_key, mapping=roles_map)
			await a_redis_client.expire(redis_key, 300)  # 5 分钟
		return roles_map
