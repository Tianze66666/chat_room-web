from django.contrib import admin
from .models import (
     SystemNotification, Notification
)
# Register your models here.


@admin.register(SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'scope', 'channel_id', 'user_id', 'is_pinned', 'is_active', 'created_at', 'expires_at')
    search_fields = ('title', 'content')
    list_filter = ('scope', 'is_pinned', 'is_active')
    ordering = ('-is_pinned', '-created_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'notification_type', 'title', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'content')
    list_filter = ('notification_type', 'is_read')
    ordering = ('-created_at',)