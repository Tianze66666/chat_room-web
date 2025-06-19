from django.db import models
from channel.models import Channel
from accounts.models import User
from django.utils import timezone


# Create your models here.
class Message(models.Model):
	id = models.BigIntegerField(primary_key=True)  # 雪花ID
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='发送者', db_constraint=False)
	channel = models.ForeignKey(Channel, on_delete=models.CASCADE, verbose_name='频道', db_constraint=False)
	content = models.TextField(blank=True, null=True, verbose_name='消息内容')
	file_id = models.BigIntegerField(blank=True, null=True, verbose_name='文件ID')
	timestamp = models.DateTimeField(auto_now_add=True, verbose_name='发送时间')

	class Meta:
		db_table = 'chat_message'
		ordering = ['timestamp']
		verbose_name = '消息'
		verbose_name_plural = '消息管理'

	def __str__(self):
		return f'{self.user} @ {self.channel} at {self.timestamp}'


class ChatFile(models.Model):
	file_id = models.BigAutoField(primary_key=True)
	uploader_id = models.BigIntegerField(verbose_name='上传用户ID')
	channel_id = models.BigIntegerField(verbose_name='所属频道ID')
	file = models.FileField(upload_to='chat_files/', verbose_name='文件')
	file_name = models.CharField(max_length=255, verbose_name='文件名')
	file_size = models.PositiveIntegerField(verbose_name='文件大小', help_text='单位：字节')
	content_type = models.CharField(max_length=100, blank=True, null=True, verbose_name='MIME类型')
	uploaded_at = models.DateTimeField(default=timezone.now, verbose_name='上传时间')
	is_temp = models.BooleanField(default=False, verbose_name='是否为临时文件')

	class Meta:
		db_table = 'chat_file'
		verbose_name = '聊天文件'
		verbose_name_plural = '聊天文件记录'
		ordering = ['-uploaded_at']
		indexes = [
			models.Index(fields=['uploader_id']),
			models.Index(fields=['channel_id']),
		]

	def __str__(self):
		return self.file_name
