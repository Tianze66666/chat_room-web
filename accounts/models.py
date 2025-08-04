from django.db import models
from django.contrib.auth.models import AbstractUser,Permission,Group

from djangoProject import settings


# Create your models here.

class User(AbstractUser):
	USER_TYPE_CHOICES = (
		(1,'Super admin'),
		(2,'Normal user')
	)
	name = models.CharField(max_length=100)
	user_type = models.PositiveSmallIntegerField(default=2,choices=USER_TYPE_CHOICES)  # 1超级管理员 2普通用户
	user_permissions = models.ManyToManyField(
		Permission,
		verbose_name='user permissions',
		blank=True,
		related_name='customuser_set',  # 自定义一个唯一的 related_name，避免冲突
		help_text='Specific permissions for this user.',
		related_query_name='customuser',
	)
	groups = models.ManyToManyField(
		Group,
		verbose_name='groups',
		blank=True,
		related_name='customuser_set',  # 避免冲突，改成自定义名字
		help_text='The groups this user belongs to.',
		related_query_name='customuser',
	)

	# 其它字段用AbstractUser已有的，比如email, last_login, date_joined等
	#拓展字段


	def __str__(self):
		return self.username or self.name or str(self.id)

	@property
	def is_super_admin(self):
		# return self.user_type == 1 or self.is_superuser
		return self.user_type == 1

	def get_full_name(self):
		if self.name:
			return self.name
		return super().get_full_name()

	def get_short_name(self):
		return self.username

	def has_admin_privileges(self):
		""" 判断是否为超级管理员或有管理权限 """
		return self.is_super_admin or self.is_staff

	class Meta:
		db_table = 'User'
		verbose_name = '用户'
		verbose_name_plural = '用户管理'


class UserProfile(models.Model):
	GENDER_CHOICES = (
		('M', '男'),
		('F', '女'),
		('O', '其他'),
	)
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		db_constraint=False,  # 关闭数据库外键约束
		related_name='profile'
	)
	birthday = models.DateField(blank=True, null=True)
	gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True,default='O')
	phone = models.CharField(max_length=20, blank=True, null=True, unique=True)
	avatar = models.ImageField(upload_to='avatars/', blank=True, null=True,
	                           default='static/default_avatar.png')
	signature = models.TextField(blank=True, null=True)  # 个性签名等
	created_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f'用户id:{self.user.username}的个人资料'

	class Meta:
		verbose_name = '用户资料'
		verbose_name_plural = '用户资料管理'

