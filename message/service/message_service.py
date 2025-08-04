# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from utils.flake_id import get_snowflake_id
from ..models import Message, ChatFile


def create_file_message(user_id, channel_id, file) -> Message:
	message_id = get_snowflake_id()

	message_type = Message.FILE
	if 'image' in file.content_type:
		message_type = Message.IMAGE

	message = Message.objects.create(
		id=message_id,
		user_id=user_id,
		channel_id=channel_id,
		file=file,
		file_name=file.name,
		file_size=file.size,
		file_type=file.content_type,
		type=message_type
	)

	ChatFile.objects.create(
		message_id=message.id,
		uploader_id=user_id,
		channel_id=channel_id,
		file_path=message.file.name,
		file_name=message.file_name,
		file_size=message.file_size,
		content_type=message.file_type,
		is_temp=False
	)

	return message
