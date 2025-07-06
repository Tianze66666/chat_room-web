# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
import json
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
	def user_is_mute(cls,message='用户被禁言',code=501,ex=None):
		data = {
			'code': code,
			'message': message
		}
		if ex:
			data['ex'] = ex.strftime("%Y-%m-%d %H:%M:%S")
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
	def invalid_connect(cls,message='非法连接'):
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
	def group_chat_broadcast(cls, channel_id, sender_id, message, message_id, sender_avatar,sender_name,code=200):
		sender_avatar_url = get_avatar_url(sender_avatar.url) if sender_avatar else ''
		data = {
			"type": "channel_chat",
			"code": code,
			"send_time": now().strftime("%Y-%m-%d %H:%M:%S"),
			"message": message,
			"message_id": message_id,
			"channel_id": int(channel_id),
			"sender_id": sender_id,
			"sender_name":sender_name,
			"sender_avatar":sender_avatar_url,
		}
		return data
