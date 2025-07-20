# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from celery import shared_task
from .models import ChatFile, Message


@shared_task
def save_file_and_create_message(user_id, channel_id, message_id, file_path):
	"""
    任务：保存文件并创建消息记录
    """

	message_type = Message.FILE
	if 'image' in file.content_type:
		message_type = Message.IMAGE
	file_name = f"chat_files/{message_id}_{file.name}"
	# 创建消息记录到 Message 表
	Message.objects.create(
		id=message_id,
		user_id=user_id,
		channel_id=channel_id,
		file=file,
		file_name=file_name,
		file_size=file.size,
		file_type=file.content_type,
		type=message_type
	)
