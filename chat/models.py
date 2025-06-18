from django.db import models
from accounts.models import User
from django.utils import timezone
from django.contrib.auth import get_user_model


class Channel(models.Model):
	JOIN_POLICY_CHOICES = (
		('public', '公开'),
		('request', '申请加入'),
		('private', '私密'),
	)
	id = models.BigAutoField(primary_key=True)
	name = models.CharField(max_length=100, unique=True, verbose_name='频道名称')
	description = models.TextField(blank=True, verbose_name='频道描述')
	avatar = models.ImageField(upload_to='channel_avatars/', blank=True, null=True, verbose_name='频道头像',
	                           default='default/default_avatar.jpg')
	owner_id = models.BigIntegerField(verbose_name='创建者ID')
	join_policy = models.CharField(
		max_length=10,
		choices=JOIN_POLICY_CHOICES,
		default='public',
		verbose_name='加入策略'
	)
	is_public = models.BooleanField(default=True, verbose_name='是否公开可搜索')
	created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

	class Meta:
		verbose_name = '频道'
		verbose_name_plural = '频道管理'
		db_table = 'channel'
		ordering = ['-created_at']

	def __str__(self):
		return self.name


class ChannelJoinRequest(models.Model):
	STATUS_CHOICES = (
		('pending', '待审批'),
		('approved', '已批准'),
		('rejected', '已拒绝'),
	)
	id = models.BigAutoField(primary_key=True)
	user_id = models.BigIntegerField(verbose_name='申请用户ID')
	channel_id = models.BigIntegerField(verbose_name='目标频道ID')
	reason = models.TextField(blank=True, verbose_name='申请理由')
	status = models.CharField(
		max_length=10,
		choices=STATUS_CHOICES,
		default='pending',
		verbose_name='审批状态'
	)
	handled_by_id = models.BigIntegerField(blank=True, null=True, verbose_name='处理人ID')
	handled_at = models.DateTimeField(blank=True, null=True, verbose_name='处理时间')
	created_at = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
	updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

	class Meta:
		verbose_name = '频道加入申请'
		verbose_name_plural = '频道加入申请管理'
		db_table = 'channel_join_request'
		indexes = [
			models.Index(fields=['user_id', 'channel_id']),
			models.Index(fields=['status']),
		]
		ordering = ['-created_at']

	def __str__(self):
		return f'申请用户ID {self.user_id} 加入频道ID {self.channel_id} 状态 {self.status}'


class ChannelMember(models.Model):
	ROLE_CHOICES = (
		(1, '普通成员'),
		(2, '管理员'),
	)
	user = models.ForeignKey(get_user_model(),
	                         verbose_name='用户ID',
	                         db_index=True,
	                         on_delete=models.CASCADE,
	                         related_name='channel_memberships',
	                         )
	channel = models.ForeignKey(
		'Channel',
		db_index=True,
		on_delete=models.CASCADE,
		related_name='members',
		verbose_name='频道'
	)
	is_admin = models.BooleanField(default=False, verbose_name='是否管理员')
	is_muted = models.BooleanField(default=False, verbose_name='是否禁言')
	joined_at = models.DateTimeField(auto_now_add=True, verbose_name='加入时间')

	class Meta:
		db_table = 'chat_channel_member'
		verbose_name = '频道成员'
		verbose_name_plural = '频道成员管理'
		unique_together = ('user', 'channel')
		ordering = ['-joined_at']

	def __str__(self):
		return f'User {self.user} in Channel {self.channel}'


class Message(models.Model):
	id = models.BigIntegerField(primary_key=True)  # 雪花ID
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='发送者')
	channel = models.ForeignKey(Channel, on_delete=models.CASCADE, verbose_name='频道')
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


class KickBanRecord(models.Model):
	ACTION_CHOICES = (
		('kick', '踢出'),
		('ban', '拉黑'),
	)
	user_id = models.BigIntegerField(verbose_name='用户ID', db_index=True)
	channel_id = models.BigIntegerField(verbose_name='频道ID', db_index=True)
	action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name='操作类型')
	reason = models.TextField(blank=True, null=True, verbose_name='原因')
	created_at = models.DateTimeField(default=timezone.now, verbose_name='操作时间')
	operator_id = models.BigIntegerField(verbose_name='操作人ID', db_index=True)

	class Meta:
		db_table = 'kick_ban_record'
		verbose_name = '踢出/拉黑记录'
		verbose_name_plural = '踢出/拉黑记录管理'
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['user_id', 'channel_id']),
		]

	def __str__(self):
		return f"{self.get_action_display()} - 用户 {self.user_id} 于频道 {self.channel_id}"


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


class ChannelActionLog(models.Model):
	ACTION_CHOICES = [
		('enter', '进入频道'),
		('leave', '离开频道'),
		('kick', '被踢出'),
		('ban', '被禁言'),
		('unban', '解除禁言'),
		('mute', '静音自己'),
		('unmute', '解除静音'),
		('blacklist', '拉黑'),
		('whitelist', '取消拉黑'),
		('custom', '其他'),
	]

	id = models.BigAutoField(primary_key=True)
	user_id = models.BigIntegerField(verbose_name='用户ID')
	channel_id = models.BigIntegerField(verbose_name='频道ID')
	action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='行为类型')
	operator_id = models.BigIntegerField(blank=True, null=True, verbose_name='操作人ID')  # 管理员/系统
	reason = models.TextField(blank=True, null=True, verbose_name='原因')
	created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

	class Meta:
		verbose_name = '频道行为记录'
		verbose_name_plural = '频道行为日志'
		db_table = 'channel_action_log'
		indexes = [
			models.Index(fields=['user_id', 'channel_id']),
			models.Index(fields=['channel_id', 'created_at']),
		]

	def __str__(self):
		return f"用户 {self.user_id} 在频道 {self.channel_id} 的行为：{self.action}"


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
		verbose_name = '通知'
		verbose_name_plural = '通知管理'
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.user.username} - {self.title}'
