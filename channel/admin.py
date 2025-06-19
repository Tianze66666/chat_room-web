from django.contrib import admin
from .models import ChannelMember,Channel,ChannelJoinRequest,ChannelActionLog,KickBanRecord
# Register your models here.


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


@admin.register(ChannelJoinRequest)
class ChannelJoinRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'channel_id', 'status', 'handled_by_id', 'handled_at', 'created_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('user_id', 'channel_id', 'handled_by_id')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(KickBanRecord)
class KickBanRecordAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'channel_id', 'action', 'operator_id', 'created_at')
    search_fields = ('user_id', 'channel_id', 'operator_id')
    list_filter = ('action',)
    ordering = ('-created_at',)

@admin.register(ChannelActionLog)
class ChannelActionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'channel_id', 'action', 'operator_id', 'created_at')
    search_fields = ('user_id', 'channel_id', 'operator_id')
    list_filter = ('action',)
    ordering = ('-created_at',)