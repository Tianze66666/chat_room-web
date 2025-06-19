# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from celery import shared_task
from message.models import Message, Channel
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task
def save_message_async(channel_id, user_id, message_id, content):
	user = User.objects.filter(id=user_id).first()
	channel = Channel.objects.filter(id=channel_id).first()
	if not channel:
		# 频道不存在，任务可选择忽略或记录日志
		return
	try:
		Message.objects.create(
			id=message_id,
			user=user,
			channel=channel,
			content=content,
		)
	except Exception as e:
		print(e)
