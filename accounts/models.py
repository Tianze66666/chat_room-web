from django.db import models
from django.contrib.auth.models import AbstractUser,Permission,Group


# Create your models here.

class User(AbstractUser):
	GENDER_CHOICES = (
		('M', '男'),
		('F', '女'),
		('O', '其他'),
	)
	USER_TYPE_CHOICES = (
		(1,'Super admin'),
		(2,'Normal user')
	)

	name = models.CharField(max_length=100)
	avatar = models.ImageField( upload_to='avatars/', blank=True, null=True,
	                           default='static/default_avatar.png')
	gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True,default='O')
	birthday = models.DateField(blank=True, null=True)
	phone = models.CharField(max_length=20, blank=True, null=True, unique=True)
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




