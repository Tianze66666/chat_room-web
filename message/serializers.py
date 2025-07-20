# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from rest_framework import serializers
from .models import Message
from datetime import datetime
import time


class MessageSerializer(serializers.ModelSerializer):


	class Meta:
		model = Message
		fields = ['id', 'user', 'channel', 'content', 'timestamp', 'type', 'file']

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
		if data.get('file'):
			message_data['file_url'] = data.get('file')

		return message_data





class FileMessageSerializer(serializers.Serializer):
	content = serializers.CharField(required=False)
	file = serializers.FileField(required=False)
	channel_id = serializers.IntegerField()
	user_id = serializers.IntegerField()
