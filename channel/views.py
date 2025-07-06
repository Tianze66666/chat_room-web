from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from utils.reponst import ChannelResponse
from django.contrib.auth import get_user_model
from djangoProject.configer import CHANNEL_MEMBERS, USER_INFO_KEY,CHANNEL_INFO_KEY
from utils.sredis import redis_client
from asgiref.sync import async_to_sync
from utils.channel_member import get_channel_member_ids
from utils.get_avatar_url import get_avatar_url
from channel.models import ChannelMember,Channel
from .permission import IsChannelMemberPermission
from datetime import datetime,date


User = get_user_model()


class ChannelMembersAPIView(APIView):
	permission_classes = [IsAuthenticated,IsChannelMemberPermission]

	def get(self, request, channel_id):
		key_member_set = CHANNEL_MEMBERS.format(channel_id)
		member_ids = [str(id) for id in redis_client.smembers(key_member_set)]
		users_data = self.get_users_info(member_ids)
		return ChannelResponse.success(data=users_data)

	@staticmethod
	def get_users_info(user_ids):
		user_info_key = USER_INFO_KEY
		result = []
		pipeline = redis_client.pipeline()
		for uid in user_ids:
			pipeline.hgetall(user_info_key.format(uid))
		cached_data = pipeline.execute()
		missing_ids = []
		for uid, data in zip(user_ids, cached_data):
			if data:
				result.append({
					'id': int(uid),
					'name': data.get('name'),
					'avatar': data.get('avatar'),
				})
			else:
				missing_ids.append(uid)
		# 数据库查缺失数据
		if missing_ids:
			users = User.objects.filter(id__in=missing_ids).all()
			for user in users:
				user_data = {
					'id': user.id,
					'name': user.name,
					'avatar': get_avatar_url(user.avatar.url) if user.avatar else '',
				}
				result.append(user_data)
				# 存入 Redis Hash
				pipeline.hset(user_info_key.format(user.id), mapping={
					'name': user_data['name'],
					'avatar': user_data['avatar']
				})
				pipeline.expire(f"user_info:{user.id}", 300)
			pipeline.execute()
		return result


class ChannelAnnouncementsLastAPIView(APIView):
	permission_classes = [IsAuthenticated,IsChannelMemberPermission]

	def get(self, request, channel_id):
		channel_announcements_key = CHANNEL_INFO_KEY.format(channel_id)
		key_exists = redis_client.exists(channel_announcements_key)
		if not key_exists:
			info = Channel.objects.filter(id=channel_id).values().first()
			clean_info = self.clean_redis_dict(info)
			redis_client.hset(channel_announcements_key,mapping=clean_info)
			redis_client.expire(channel_announcements_key, 300)
			return ChannelResponse.success(data={'announcements': info.get('description')})
		info = redis_client.hget(channel_announcements_key,'description')
		data = {
			'announcements': info if info else '',
		}
		return ChannelResponse.success(data=data)

	@staticmethod
	def clean_redis_dict(d):
		new_dict = {}
		for k, v in d.items():
			if v is None:
				new_dict[k] = ''
			elif isinstance(v, bool):
				new_dict[k] = 'true' if v else 'false'
			elif isinstance(v,(datetime,date)):
				new_dict[k] = v.strftime('%Y-%m-%d %H:%M:%S')
			else:
				new_dict[k] = v
		return new_dict
