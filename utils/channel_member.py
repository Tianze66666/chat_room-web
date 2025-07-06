# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from channel.models import ChannelMember
from asgiref.sync import sync_to_async
from utils.get_avatar_url import get_avatar_url
from djangoProject.configer import CHANNEL_MEMBERS
from utils.aredis import redis_client
import json


@sync_to_async
def get_channel_member_ids(channel_id):
	return list(ChannelMember.objects.filter(channel_id=channel_id).values_list('user_id', flat=True))


async def load_channel_members(channel_id):
	key = CHANNEL_MEMBERS.format(channel_id)
	exists = await redis_client.exists(key)
	if not exists:
		member_info_dict = await get_channel_member_info(channel_id)
		if member_info_dict:
			await redis_client.hset(key, mapping=member_info_dict)
			await redis_client.expire(key, 300)
			return member_info_dict
		return False


@sync_to_async
def get_channel_member_info(channel_id):
	members = ChannelMember.objects.select_related('user').filter(channel_id=channel_id)
	member_data = {}
	for m in members:
		member_data[str(m.id)] = json.dumps({
			"user_id": m.id,
			"name": m.user.name,
			"avatar": get_avatar_url(m.user.avatar.url) if m.user.avatar.url else '',
		})
	return member_data
