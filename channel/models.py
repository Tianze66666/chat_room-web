from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
# Create your models here.

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
	is_all_muted = models.BooleanField(verbose_name='是否全员禁言', default=False)
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
	muted_until = models.DateTimeField(blank=True, null=True, verbose_name='禁言截止时间')

	class Meta:
		db_table = 'chat_channel_member'
		verbose_name = '频道成员'
		verbose_name_plural = '频道成员管理'
		unique_together = ('user', 'channel')
		ordering = ['-joined_at']

	def __str__(self):
		return f'User {self.user} in Channel {self.channel}'



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







