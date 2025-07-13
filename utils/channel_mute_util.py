# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from channel.models import ChannelMember, Channel
from djangoProject.configer import CHANNEL_MUTE_USER_KEY, CHANNEL_ALL_MUTE_KEY, USER_MUTE_KEY, CHANNEL_MEMBER_ROLES, \
	CHANNEL_NAME
from utils.channel_member import AsyncBuildChannelMemberCacheMixin
from asgiref.sync import sync_to_async, async_to_sync
from django.utils import timezone
from datetime import timedelta
from .aredis import redis_client as a_redis_client
from .sredis import redis_client as s_redis_client
from channels.layers import get_channel_layer
from utils.ws_response import WSResponse


class ChannelMuteCache(AsyncBuildChannelMemberCacheMixin):
	def __init__(self):
		self.key_muted_format = CHANNEL_MUTE_USER_KEY  # 频道禁言成员列表
		self.key_all_muted_format = CHANNEL_ALL_MUTE_KEY  # 频道是否全员禁言
		self.key_user_mute_format = USER_MUTE_KEY  # 用户禁言key
		self.key_channel_member_roles = CHANNEL_MEMBER_ROLES  # 用户身份

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
		set_key = self.key_muted_format.format(channel_id)
		all_key = self.key_all_muted_format.format(channel_id)
		muted = await self.get_muted_with_expire(channel_id)
		now = timezone.now()
		pipe = a_redis_client.pipeline()

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
		is_all_mute = await self.get_channel_is_all_mute(channel_id)
		if is_all_mute:
			pipe.set(all_key, int(is_all_mute))
		await pipe.execute()

	async def is_user_muted(self, channel_id, user_id):
		set_key = self.key_muted_format.format(channel_id)
		mute_key = self.key_user_mute_format.format(channel_id, user_id)

		if await a_redis_client.sismember(set_key, user_id):
			ttl = await a_redis_client.ttl(mute_key)
			if ttl and ttl > 0:
				expire_at = timezone.now() + timezone.timedelta(seconds=ttl)
				return True, expire_at
			else:
				# 过期自动清除
				await a_redis_client.srem(set_key, user_id)
		return False, None

	# 判断是否允许发言
	async def can_user_send(self, channel_id, user_id):
		set_key = self.key_muted_format.format(channel_id)
		all_key = self.key_all_muted_format.format(channel_id)

		if not await a_redis_client.exists(set_key) or not await a_redis_client.exists(all_key):
			await self.init_mute_cache(channel_id)

		# 已经判断过了，不需要这个逻辑
		# member = await self.get_member_basic(channel_id, user_id)
		# if not member:
		# 	return False, None  # 非频道成员

		result, ex = await self.is_user_muted(channel_id, user_id)
		if result:
			return False, ex

		if await self.is_admin(channel_id, user_id):
			return True, None  # 管理员允许发言

		all_muted = await a_redis_client.get(all_key)
		return not (all_muted and int(all_muted) == 1), 0

	async def is_admin(self, channel_id, user_id):
		if not await a_redis_client.exists(self.key_channel_member_roles.format(channel_id)):
			roles_map = await self.build_and_cache_channel_roles(channel_id)
			return user_id in roles_map
		# 返回map里面是否能拿到
		return await a_redis_client.hget(self.key_channel_member_roles.format(channel_id), user_id) is not None


class MuteUserUtilsMixin:

	def __init__(self):
		self.key_muted_format = CHANNEL_MUTE_USER_KEY  # 频道禁言成员列表
		self.key_all_muted_format = CHANNEL_ALL_MUTE_KEY  # 频道是否全员禁言
		self.key_user_mute_format = USER_MUTE_KEY  # 用户禁言key
		self.key_channel_name = CHANNEL_NAME

	def mute_user(self, channel_id, mute_user_id, seconds, user_id=None):
		set_key = self.key_muted_format.format(channel_id)
		mute_key = self.key_user_mute_format.format(channel_id, mute_user_id)
		key_channel_name = self.key_channel_name.format(channel_id)

		s_redis_client.sadd(set_key, mute_user_id)
		s_redis_client.setex(mute_key, seconds, 1)
		data = WSResponse.mute_user_notice(mute_user_id, user_id, ex=seconds)
		channel_layer = get_channel_layer()
		async_to_sync(channel_layer.group_send)(key_channel_name, data)

		# 同步更新数据库
		expire_time = timezone.now() + timedelta(seconds=seconds)
		ChannelMember.objects.filter(
			channel_id=channel_id, user_id=mute_user_id
		).update(
			is_muted=True,
			muted_until=expire_time
		)

	def unmute_user(self, channel_id, mute_user_id, user_id=None):
		set_key = self.key_muted_format.format(channel_id)
		mute_key = self.key_user_mute_format.format(channel_id, mute_user_id)
		key_channel_name = self.key_channel_name.format(channel_id)


		s_redis_client.srem(set_key, mute_user_id)
		s_redis_client.delete(mute_key)

		data = WSResponse.mute_user_notice(mute_user_id, user_id, message='解除禁言')
		channel_layer = get_channel_layer()
		async_to_sync(channel_layer.group_send)(key_channel_name, data)
		# 同步更新数据库
		ChannelMember.objects.filter(
			channel_id=channel_id, user_id=mute_user_id
		).update(
			is_muted=False,
			muted_until=None
		)

	def change_all_mute_state(self, channel_id):
		channel_all_mute_key = self.key_all_muted_format.format(channel_id)
		key_channel_name = self.key_channel_name.format(channel_id)
		channel_layer = get_channel_layer()

		# 没有key说明没有全员禁言 那就进行全员禁言
		if not s_redis_client.exists(channel_all_mute_key):
			channel_all_mute_key = self.key_all_muted_format.format(channel_id)
			s_redis_client.set(channel_all_mute_key, 1)
			Channel.objects.filter(id=channel_id).update(is_all_muted=True)
			data = WSResponse.all_mute_user_notice()
			async_to_sync(channel_layer.group_send)(key_channel_name, data)
			return

		# 解除全员禁言
		state = (s_redis_client.get(channel_all_mute_key) == str(1))
		if state:
			s_redis_client.delete(channel_all_mute_key)
			Channel.objects.filter(id=channel_id).update(is_all_muted=False)
			data = WSResponse.all_mute_user_notice(message='管理员关闭了全群禁言')
			async_to_sync(channel_layer.group_send)(key_channel_name, data)
			return True
		return False
