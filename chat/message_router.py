# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from rest_framework_simplejwt.tokens import UntypedToken
from .handdles.chat_handler import GroupChatHandles
from utils.aredis import redis_client
from utils.ws_response import WSResponse
from djangoProject.configer import USER_INFO_KEY

message_type_map = {
	'chat': GroupChatHandles,
}


async def dispatch_message(consumer, data):
	# TODO:消息鉴权，验证消息token中的jti是否与缓存一致
	user_id = consumer.user.id
	key = USER_INFO_KEY.format(user_id)
	current_jti = await redis_client.hget(key,'access_jti')
	token = data.get('token')
	if (not current_jti) or(not token):
		await invalid_connect(consumer)
		return
	try:
		jti = UntypedToken(token).payload.get('jti')
	except Exception as e:
		await invalid_connect(consumer)
		return
	if not current_jti == jti:
		await invalid_connect(consumer)
		return

	msg_type = data.get('type')
	if not msg_type or (msg_type not in message_type_map):
		data = WSResponse.type_error()
		await consumer.send(text_data=data)
		return
	# 实例化示例类
	handler = message_type_map[msg_type](consumer, data)
	await handler.handle()


async def invalid_connect(consumer):
	data = WSResponse.invalid_connect()
	await consumer.send(text_data=data)
	await consumer.close()
