from django.contrib import admin
from .models import Message,ChatFile
# Register your models here.


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'channel', 'timestamp')
    search_fields = ('user__username', 'channel__name', 'content')
    list_filter = ('channel',)
    ordering = ('-timestamp',)
    readonly_fields = ('id',)


@admin.register(ChatFile)
class ChatFileAdmin(admin.ModelAdmin):
    list_display = ('file_id', 'file_name', 'uploader_id', 'channel_id', 'file_size', 'uploaded_at', 'is_temp')
    search_fields = ('file_name', 'uploader_id', 'channel_id')
    list_filter = ('is_temp',)
    ordering = ('-uploaded_at',)