# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from rest_framework import serializers
from .models import Message
from datetime import datetime
import time

class MessageSerializer(serializers.ModelSerializer):
	class Meta:
		model = Message
		fields = ['id', 'user', 'channel', 'content', 'timestamp', 'type']

	def to_representation(self, instance):
		data = super(MessageSerializer, self).to_representation(instance)
		formatted_time = data.get('timestamp')
		timestamp = int(time.mktime(datetime.strptime(formatted_time, "%Y-%m-%dT%H:%M:%S.%f").timetuple()))
		return {
			'type': data.get('type'),
			'timestamp': timestamp,
			'message': data.get('content'),
			'message_id': data.get('id'),
			"channel_id": data['channel'],
			"sender_id": data['user'],
		}
