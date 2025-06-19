from django.db import models
from accounts.models import User


class SystemNotification(models.Model):
	TARGET_SCOPE_CHOICES = [
		('global', '全局通知'),
		('channel', '频道通知'),
		('user', '个人通知'),
	]
	id = models.BigAutoField(primary_key=True)
	title = models.CharField(max_length=100, verbose_name='通知标题')
	content = models.TextField(verbose_name='通知内容')
	scope = models.CharField(max_length=10, choices=TARGET_SCOPE_CHOICES, default='global', verbose_name='作用范围')
	channel_id = models.BigIntegerField(blank=True, null=True, verbose_name='频道ID')  # 如果是频道通知
	user_id = models.BigIntegerField(blank=True, null=True, verbose_name='用户ID')  # 如果是个人通知
	is_pinned = models.BooleanField(default=False, verbose_name='是否置顶')
	is_active = models.BooleanField(default=True, verbose_name='是否生效')
	created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
	expires_at = models.DateTimeField(blank=True, null=True, verbose_name='过期时间')

	class Meta:
		verbose_name = '系统通知'
		verbose_name_plural = '系统通知管理'
		db_table = 'system_notification'
		ordering = ['-is_pinned', '-created_at']
		indexes = [
			models.Index(fields=['scope']),
			models.Index(fields=['channel_id']),
			models.Index(fields=['user_id']),
		]

	def __str__(self):
		return f"{self.title}（{self.get_scope_display()}）"


class Notification(models.Model):
	class NotificationType(models.TextChoices):
		JOIN_REQUEST = 'join_request', '加入申请'
		APPROVAL_RESULT = 'approval_result', '审批结果'
		MESSAGE = 'message', '聊天消息'
		SYSTEM = 'system', '系统通知'
	# 以后可以继续加类型

	user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name='用户',
	                         related_name='notifications')
	notification_type = models.CharField(max_length=30, choices=NotificationType.choices, verbose_name='通知类型')
	related_id = models.BigIntegerField(null=True, blank=True, verbose_name='关联ID')
	title = models.CharField(max_length=255, verbose_name='标题')
	content = models.TextField(blank=True, verbose_name='内容')
	is_read = models.BooleanField(default=False, verbose_name='是否已读')
	created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
	updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

	class Meta:
		db_table = 'notification'
		verbose_name = '通知'
		verbose_name_plural = '通知管理'
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.user.username} - {self.title}'
