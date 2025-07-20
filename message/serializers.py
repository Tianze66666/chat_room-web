# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from rest_framework import serializers
from .models import Message
from datetime import datetime
import time


class MessageSerializer(serializers.ModelSerializer):
	file_url = serializers.CharField(read_only=True)
	file_name = serializers.CharField(read_only=True)
	file_size = serializers.IntegerField(read_only=True)
	file_type = serializers.CharField(read_only=True)

	class Meta:
		model = Message
		fields = ['id', 'user', 'channel', 'content', 'timestamp', 'type', 'file_url', 'file_name', 'file_size', 'file_type']

	def to_representation(self, instance):
		data = super(MessageSerializer, self).to_representation(instance)
		formatted_time = data.get('timestamp')
		timestamp = int(time.mktime(datetime.strptime(formatted_time, "%Y-%m-%dT%H:%M:%S.%f").timetuple()))

		message_data = {
			'type': data.get('type'),
			'timestamp': timestamp,
			'message': data.get('content'),
			'message_id': data.get('id'),
			"channel_id": data['channel'],
			"sender_id": data['user'],
		}

		if data.get('type') in [Message.FILE, Message.IMAGE]:
			message_data['file_url'] = data.get('file_url')
			message_data['file_name'] = data.get('file_name')
			message_data['file_size'] = data.get('file_size')
			message_data['file_type'] = data.get('file_type')

		return message_data





class FileMessageSerializer(serializers.Serializer):
	content = serializers.CharField(required=False)
	file = serializers.FileField(required=False)
	channel_id = serializers.IntegerField()
	user_id = serializers.IntegerField()
