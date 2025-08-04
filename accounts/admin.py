from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

# Register your models here.

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    # 自定义显示字段（列表页）
    list_display = ('id', 'username', 'name', 'email', 'user_type', 'is_superuser', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_superuser', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('id',)

    # 在编辑页面，分组显示字段，包含自定义字段
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('name', 'email', 'phone')}),
        (_('Permissions'), {
            'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type', 'is_staff', 'is_superuser'),
        }),
    )

    filter_horizontal = ('groups', 'user_permissions',)
