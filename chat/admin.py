from django.contrib import admin
from .models import (
    Channel, ChannelJoinRequest, ChannelMember, Message, KickBanRecord,
    ChatFile, ChannelActionLog, SystemNotification, Notification
)
# Register your models here.


@admin.register(ChannelJoinRequest)
class ChannelJoinRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'channel_id', 'status', 'handled_by_id', 'handled_at', 'created_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('user_id', 'channel_id', 'handled_by_id')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner_id', 'join_policy', 'is_public', 'created_at')
    search_fields = ('name', 'description', 'owner_id')
    list_filter = ('join_policy', 'is_public')
    ordering = ('-created_at',)


@admin.register(ChannelMember)
class ChannelMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'channel', 'is_admin', 'is_muted', 'joined_at')
    search_fields = ('user', 'channel')
    list_filter = ('is_admin', 'is_muted')
    ordering = ('-joined_at',)
    list_per_page = 50


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'channel', 'timestamp')
    search_fields = ('user__username', 'channel__name', 'content')
    list_filter = ('channel',)
    ordering = ('-timestamp',)
    readonly_fields = ('id',)


@admin.register(KickBanRecord)
class KickBanRecordAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'channel_id', 'action', 'operator_id', 'created_at')
    search_fields = ('user_id', 'channel_id', 'operator_id')
    list_filter = ('action',)
    ordering = ('-created_at',)


@admin.register(ChatFile)
class ChatFileAdmin(admin.ModelAdmin):
    list_display = ('file_id', 'file_name', 'uploader_id', 'channel_id', 'file_size', 'uploaded_at', 'is_temp')
    search_fields = ('file_name', 'uploader_id', 'channel_id')
    list_filter = ('is_temp',)
    ordering = ('-uploaded_at',)


@admin.register(ChannelActionLog)
class ChannelActionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'channel_id', 'action', 'operator_id', 'created_at')
    search_fields = ('user_id', 'channel_id', 'operator_id')
    list_filter = ('action',)
    ordering = ('-created_at',)


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