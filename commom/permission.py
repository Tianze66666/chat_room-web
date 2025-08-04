# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from rest_framework.permissions import BasePermission
from djangoProject.configer import CHANNEL_MEMBERS
from commom.sredis import redis_client
from channel.models import ChannelMember

class IsChannelMemberPermission(BasePermission):
	message = "你不是该频道成员"

	def has_permission(self, request, view):
		user = request.user
		channel_id = view.kwargs.get('channel_id') or request.data.get('channel_id')
		if not user or not user.is_authenticated or not channel_id:
			print(channel_id)
			return False

		key_member_set = CHANNEL_MEMBERS.format(channel_id)
		user_id = user.id

		# 判断redis是否有成员缓存
		if not redis_client.exists(key_member_set):
			member_ids = list(ChannelMember.objects.filter(channel_id=channel_id).values_list('user_id', flat=True))
			if not member_ids:
				print(2)
				return False
			redis_client.sadd(key_member_set, *member_ids)
			redis_client.expire(key_member_set, 300)

		# 判断用户是否是成员（注意redis存的是字符串，所以做类型转换）
		is_member = redis_client.sismember(key_member_set, user_id)
		print(3, is_member)
		return is_member

