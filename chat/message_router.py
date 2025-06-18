# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from utils.ws_response import WSResponse

from .handdles.chat_handler import GroupChatHandles

message_type_map = {
	'chat': GroupChatHandles,
}


async def dispatch_message(consumer, data):
	# TODO:消息鉴权，验证消息token中的jti是否与缓存一致
	msg_type = data.get('type')
	if not msg_type or (msg_type not in message_type_map):
		data = WSResponse.type_error()
		await consumer.send(text_data=data)
		return
	# 实例化示例类
	handler = message_type_map[msg_type](consumer,data)
	await handler.handle()
