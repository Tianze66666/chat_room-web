from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from utils.reponst import ChannelResponse
from django.contrib.auth import get_user_model
from djangoProject.configer import (CHANNEL_MEMBERS,
                                    USER_INFO_KEY,
                                    CHANNEL_INFO_KEY,
                                    CHANNEL_MEMBER_ROLES,
                                    CHANNEL_MUTE_USER_KEY,
                                    CHANNEL_ALL_MUTE_KEY,
                                    USER_MUTE_KEY,
									CHANNEL_NAME
                                    )
from utils.sredis import redis_client
from utils.get_avatar_url import get_avatar_url
from channel.models import ChannelMember, Channel
from .permission import IsChannelMemberPermission
from datetime import datetime, date
from utils.channel_member import BuildChannelMemberCacheMixin
from utils.channel_mute_util import MuteUserUtilsMixin


User = get_user_model()


class ChannelMembersAPIView(BuildChannelMemberCacheMixin, APIView):
	permission_classes = [IsAuthenticated, IsChannelMemberPermission]

	def __init__(self, *args, **kwargs):
		super(ChannelMembersAPIView, self).__init__(*args, **kwargs)
		self.key_member_set = CHANNEL_MEMBERS
		self.roles_map_key = CHANNEL_MEMBER_ROLES
		self.user_info_key = USER_INFO_KEY

	def get(self, request, channel_id):
		member_ids = [str(id) for id in redis_client.smembers(self.key_member_set.format(channel_id))]
		roles_map = redis_client.hgetall(self.roles_map_key.format(channel_id))
		if not roles_map:
			roles_map = self.build_and_cache_channel_roles(channel_id)
		users_data = self.get_users_info(member_ids, roles_map)
		return ChannelResponse.success(data=users_data)

	def get_users_info(self, user_ids, roles_map):
		result = []
		pipeline = redis_client.pipeline()
		for uid in user_ids:
			pipeline.hgetall(self.user_info_key.format(uid))
		cached_data = pipeline.execute()
		missing_ids = []
		for uid, data in zip(user_ids, cached_data):
			role = roles_map.get(uid, 0)
			if data:
				result.append({
					'id': int(uid),
					'name': data.get('name'),
					'avatar': data.get('avatar'),
					'role': int(role)  # 加入角色信息
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
					'role': int(roles_map.get(str(user.id), 0))
				}
				result.append(user_data)
				# 存入 Redis Hash
				pipeline.hset(self.user_info_key.format(user.id), mapping={
					'name': user_data['name'],
					'avatar': user_data['avatar']
				})
				pipeline.expire(f"user_info:{user.id}", 300)
			pipeline.execute()
		return result


class ChannelAnnouncementsLastAPIView(APIView):
	permission_classes = [IsAuthenticated, IsChannelMemberPermission]

	def get(self, request, channel_id):
		channel_announcements_key = CHANNEL_INFO_KEY.format(channel_id)
		key_exists = redis_client.exists(channel_announcements_key)
		if not key_exists:
			info_dict = Channel.objects.filter(id=channel_id).values().first()
			clean_info = self.clean_redis_dict(info_dict)
			redis_client.hset(channel_announcements_key, mapping=clean_info)
			redis_client.expire(channel_announcements_key, 300)
			return ChannelResponse.success(data=clean_info)
		info_dict = redis_client.hgetall(channel_announcements_key)
		return ChannelResponse.success(data=info_dict)

	@staticmethod
	def clean_redis_dict(d):
		new_dict = {}
		for k, v in d.items():
			if v is None:
				new_dict[k] = ''
			elif isinstance(v, bool):
				new_dict[k] = 'true' if v else 'false'
			elif isinstance(v, (datetime, date)):
				new_dict[k] = v.strftime('%Y-%m-%d %H:%M:%S')
			else:
				new_dict[k] = v
		return new_dict


class ChannelMuteUserAPIView(APIView, MuteUserUtilsMixin, BuildChannelMemberCacheMixin):
	permission_classes = [IsAuthenticated]

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.key_muted_format = CHANNEL_MUTE_USER_KEY  # 频道禁言成员列表
		self.key_all_muted_format = CHANNEL_ALL_MUTE_KEY  # 频道是否全员禁言
		self.key_user_mute_format = USER_MUTE_KEY  # 用户禁言key
		self.key_channel_name = CHANNEL_NAME
		self.roles_map_key = CHANNEL_MEMBER_ROLES

	def post(self, request):
		request_data = request.data
		user_id = request.user.id
		channel_id = request_data.get('channel_id')
		mute_user_id = request_data.get('mute_user_id')
		seconds = request_data.get('seconds')
		# 全员禁言
		if request_data.get('is_all_mute',False):
			self.change_all_mute_state(channel_id)
			return ChannelResponse.success()
		if not user_id or not channel_id:
			return ChannelResponse.fail(message='出错了，请稍后再试')
		# 验证两人的权限关系
		if not redis_client.exists(self.roles_map_key.format(channel_id)):
			roles_map = self.build_and_cache_channel_roles(channel_id)
		else:
			roles_map = redis_client.hgetall(self.roles_map_key.format(channel_id))
		user_role = int(roles_map.get(str(user_id), 0))
		mute_user_role = int(roles_map.get(str(mute_user_id), 0))
		if not user_role > mute_user_role:
			return ChannelResponse.fail(message='你无权操作该用户')
		# 单人禁言/解除禁言
		if mute_user_id == user_id:
			return ChannelResponse.fail(message='不能对自己进行操作')
		# 解除禁言
		if not seconds:
			self.unmute_user(channel_id, mute_user_id,user_id)
			return ChannelResponse.success(message='成功解除禁言')
		# 禁言
		self.mute_user(channel_id, mute_user_id, seconds,user_id)
		return ChannelResponse.success(message='成功禁言')





