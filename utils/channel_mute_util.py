# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from channel.models import ChannelMember, Channel
from djangoProject.configer import CHANNEL_MUTE_SET, CHANNEL_ALL_MUTE_KEY, CHANNEL_MEMBER_ROLES
from commom.mixins.build_channel_member_cache import AsyncBuildChannelMemberCacheMixin
from asgiref.sync import sync_to_async
import time
from commom.aredis import redis_client as a_redis_client


class ChannelMuteCache(AsyncBuildChannelMemberCacheMixin):
	@sync_to_async
	def get_muted_ids(self, channel_id):
		return list(
			ChannelMember.objects.filter(channel_id=channel_id, is_muted=True)
			.values_list('user_id', flat=True)
		)

	@sync_to_async
	def get_channel_is_all_mute(self, channel_id):
		# return ChannelMember.objects.filter(channel_id=channel_id).select_related('channel').first()
		return Channel.objects.filter(id=channel_id).values_list('is_all_muted', flat=True).first()

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
		set_key = CHANNEL_MUTE_SET.format(channel_id)
		all_mute_key = CHANNEL_ALL_MUTE_KEY.format(channel_id)
		muted = await self.get_muted_with_expire(channel_id)
		now = time.time()
		pipe = a_redis_client.pipeline()

		if muted:
			# 设置过期时间
			for user_id, expire_at in muted:
				expire_at = int(expire_at.timestamp())
				if expire_at and expire_at > now:
					score = int(expire_at)
					pipe.zadd(set_key, {user_id: score})

		# 全员禁言缓存
		is_all_mute = await self.get_channel_is_all_mute(channel_id)
		if is_all_mute:
			pipe.set(all_mute_key, int(is_all_mute))
		await pipe.execute()

	@staticmethod
	async def is_user_muted(channel_id, user_id, ):
		set_key = CHANNEL_MUTE_SET.format(channel_id)
		score = await a_redis_client.zscore(set_key, user_id)
		now_ts = time.time()

		if score and float(score) > now_ts:
			return True, float(score)
		else:
			# 过期清除
			await a_redis_client.zrem(set_key, user_id)
			return False, None

	# 判断是否允许发言
	async def can_user_send(self, channel_id, user_id):
		set_key = CHANNEL_MUTE_SET.format(channel_id)
		all_mute_key = CHANNEL_ALL_MUTE_KEY.format(channel_id)

		if not await a_redis_client.exists(set_key) or not await a_redis_client.exists(all_mute_key):
			await self.init_mute_cache(channel_id)

		result, ex = await self.is_user_muted(channel_id, user_id)
		if result:
			return False, ex

		if await self.is_admin(channel_id, user_id):
			return True, None  # 管理员允许发言

		all_muted = await a_redis_client.get(all_mute_key)
		return not (all_muted and int(all_muted) == 1), 0

	async def is_admin(self, channel_id, user_id):
		if not await a_redis_client.exists(CHANNEL_MEMBER_ROLES.format(channel_id)):
			roles_map = await self.build_and_cache_channel_roles(channel_id)
			return user_id in roles_map
		# 返回map里面是否能拿到
		return await a_redis_client.hget(CHANNEL_MEMBER_ROLES.format(channel_id), user_id) is not None


