# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
import time
from datetime import datetime

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from channel.models import ChannelMember, Channel
from commom.ws_response import WSResponse
from djangoProject.configer import CHANNEL_MUTE_SET, CHANNEL_NAME, CHANNEL_ALL_MUTE_KEY
from commom.sredis import redis_client as s_redis_client


class MuteUserUtilsMixin:

	@staticmethod
	def mute_user(channel_id, mute_user_id, seconds, user_id=None):
		set_key = CHANNEL_MUTE_SET.format(channel_id)
		key_channel_name = CHANNEL_NAME.format(channel_id)
		timestamp = int(time.time()) + seconds  # 时间戳

		s_redis_client.zadd(set_key, {mute_user_id: timestamp})

		data = WSResponse.mute_user_notice(mute_user_id, user_id, channel_id, seconds=seconds)
		channel_layer = get_channel_layer()
		async_to_sync(channel_layer.group_send)(key_channel_name, data)

		# 同步更新数据库

		ChannelMember.objects.filter(
			channel_id=channel_id, user_id=mute_user_id
		).update(
			is_muted=True,
			muted_until=datetime.fromtimestamp(timestamp)
		)

	@staticmethod
	def unmute_user(channel_id, mute_user_id, user_id=None):
		set_key = CHANNEL_MUTE_SET.format(channel_id)
		key_channel_name = CHANNEL_NAME.format(channel_id)

		s_redis_client.zrem(set_key, mute_user_id)

		data = WSResponse.mute_user_notice(mute_user_id, user_id, channel_id, code=502)
		channel_layer = get_channel_layer()
		async_to_sync(channel_layer.group_send)(key_channel_name, data)
		# 同步更新数据库
		ChannelMember.objects.filter(
			channel_id=channel_id, user_id=mute_user_id
		).update(
			is_muted=False,
			muted_until=None
		)

	@staticmethod
	def change_all_mute_state(channel_id):
		channel_all_mute_key = CHANNEL_ALL_MUTE_KEY.format(channel_id)
		key_channel_name = CHANNEL_NAME.format(channel_id)
		channel_layer = get_channel_layer()

		# 没有key说明没有全员禁言 那就进行全员禁言
		if not s_redis_client.exists(channel_all_mute_key):
			channel_all_mute_key = channel_all_mute_key.format(channel_id)
			s_redis_client.set(channel_all_mute_key, 1)
			Channel.objects.filter(id=channel_id).update(is_all_muted=True)
			data = WSResponse.all_mute_user_notice(channel_id)
			async_to_sync(channel_layer.group_send)(key_channel_name, data)
			return

		# 解除全员禁言
		state = (s_redis_client.get(channel_all_mute_key) == str(1))
		if state:
			s_redis_client.delete(channel_all_mute_key)
			Channel.objects.filter(id=channel_id).update(is_all_muted=False)
			data = WSResponse.all_mute_user_notice(channel_id, message='管理员关闭了全群禁言', code=502)
			async_to_sync(channel_layer.group_send)(key_channel_name, data)
			return True
		return False
