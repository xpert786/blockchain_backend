from django.contrib import admin
from .models import (
    Conversation, Message, MessageReadReceipt, MessageReaction,
    MessageEditHistory, TypingIndicator, MessageAttachment, MessageNotification
)


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['created_at', 'is_read', 'read_at']
    fields = ['sender', 'content', 'attachment', 'is_read', 'read_at', 'created_at']
    
    def get_formset(self, request, obj=None, **kwargs):
        """Customize the formset to make sender selectable"""
        formset = super().get_formset(request, obj, **kwargs)
        # Only show inline messages when editing existing conversation
        if obj is None:
            # Hide inline when creating new conversation
            self.max_num = 0
        else:
            self.max_num = None
        return formset


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'is_group_conversation', 'get_participants', 'created_at', 'updated_at']
    list_filter = ['is_group_conversation', 'created_at']
    search_fields = ['subject', 'participants__username', 'participants__email']
    filter_horizontal = ['participants']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [MessageInline]
    
    def get_participants(self, obj):
        return ', '.join([p.username for p in obj.participants.all()[:3]])
    get_participants.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'content_preview', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at', 'sender']
    search_fields = ['content', 'sender__username', 'sender__email']
    readonly_fields = ['created_at', 'updated_at', 'read_at']
    fields = ['conversation', 'sender', 'content', 'attachment', 'attachment_name', 'is_read', 'read_at', 'created_at', 'updated_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def save_model(self, request, obj, form, change):
        """Auto-set sender to current user if creating new message"""
        if not change and not obj.sender:
            obj.sender = request.user
        super().save_model(request, obj, form, change)


@admin.register(MessageReadReceipt)
class MessageReadReceiptAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'user', 'read_at']
    list_filter = ['read_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['read_at']


@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'user', 'emoji', 'created_at']
    list_filter = ['emoji', 'created_at']
    search_fields = ['user__username', 'message__content']
    readonly_fields = ['created_at']


@admin.register(MessageEditHistory)
class MessageEditHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'edited_by', 'edited_at']
    list_filter = ['edited_at']
    search_fields = ['message__content', 'previous_content', 'edited_by__username']
    readonly_fields = ['edited_at']


@admin.register(TypingIndicator)
class TypingIndicatorAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'user', 'started_typing_at', 'is_active']
    list_filter = ['started_typing_at']
    search_fields = ['user__username', 'conversation__subject']
    readonly_fields = ['started_typing_at']
    
    def is_active(self, obj):
        return obj.is_active()
    is_active.boolean = True


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'file_name', 'file_type', 'file_size', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['file_name', 'message__content']
    readonly_fields = ['created_at']


@admin.register(MessageNotification)
class MessageNotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'recipient', 'notification_type', 'delivery_method', 'is_sent', 'is_read', 'created_at']
    list_filter = ['notification_type', 'delivery_method', 'is_sent', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'message__content']
    readonly_fields = ['sent_at', 'read_at', 'created_at']
