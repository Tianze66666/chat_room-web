# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
import json
import time
from utils.get_avatar_url import get_avatar_url
from django.utils.timezone import now


class WSResponse:

	@classmethod
	def fail(cls, message='缺少必要参数', code=400):
		data = {
			'code': code,
			'message': message
		}
		return json.dumps(data, ensure_ascii=False)

	@classmethod
	def mute_user_notice(cls, mute_user_id, user_id, channel_id, seconds=None, code=501):
		data = {
			'code': code,
			'type': 'mute_notice',
			'user_id': user_id,
			'mute_user_id': mute_user_id,
			'channel_id': channel_id,
		}
		if seconds:
			# data['ex'] = ex.strftime("%Y-%m-%d %H:%M:%S")
			data['mute_seconds'] = seconds
		return data

	@classmethod
	def all_mute_user_notice(cls, channel_id, message='管理员开启了全员禁言', code=501):
		data = {
			'code': code,
			'type': 'all_mute_notice',
			'message': message,
			'channel_id': channel_id,
		}
		return data

	@classmethod
	def user_is_mute(cls, channel_id,message='用户被禁言', ex=None, code=501):
		data = {
			'type': 'user_is_mute',
			'code': code,
			'message': message,
			'channel_id': channel_id,
		}
		if ex:
			data['ex'] = ex
		return json.dumps(data, ensure_ascii=False)

	@classmethod
	def type_error(cls, message='不支持的消息类型'):
		data = {
			'code': 500,
			'message': message
		}
		return json.dumps(data, ensure_ascii=False)

	@classmethod
	def force_disconnect(cls):
		data = {
			'code': 403,
			"type": 'force_disconnect',
			"message": "账号已在其他其他上线"
		}
		return data

	@classmethod
	def invalid_connect(cls, message='非法连接'):
		data = {
			'code': 401,
			'message': message
		}
		return json.dumps(data, ensure_ascii=False)

	@classmethod
	def init_connection(cls, channel_ids):
		data = {
			"code": 200,
			"type": "init_connection",
			"message": "连接成功并加入频道",
			"joined_channels": channel_ids
		}
		return json.dumps(data, ensure_ascii=False)

	@classmethod
	def group_chat_broadcast(cls, channel_id, sender_id, message, message_id, sender_avatar, sender_name):
		sender_avatar_url = get_avatar_url(sender_avatar.url) if sender_avatar else ''
		# 只返回sender_id 前端自行根据id查找name和avatar_url
		data = {
			"type": "channel_chat_text",
			"timestamp": int(time.time()) or now().strftime("%Y-%m-%d %H:%M:%S"),
			"message": message,
			"message_id": message_id,
			"channel_id": int(channel_id),
			"sender_id": sender_id,
			# "sender_name": sender_name,
			# "sender_avatar": sender_avatar_url,
		}
		return data

	@classmethod
	def channel_image_broadcast(cls,channel_id,sender_id,message_id,image_url):
		data = {
			"type": "channel_chat_image",
			"message_id": message_id,
			"timestamp": int(time.time()),
			"channel_id": int(channel_id),
			"sender_id": int(sender_id),
			"file_url": get_avatar_url(image_url)
		}
		return data
