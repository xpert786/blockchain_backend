from django.db import models
from django.conf import settings
from django.utils import timezone


class Conversation(models.Model):
    """Model for conversations between users"""
    
    # Participants
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )
    
    # Conversation metadata
    subject = models.CharField(max_length=255, blank=True, null=True)
    is_group_conversation = models.BooleanField(default=False)
    
    # Related to syndicate/SPV if applicable
    related_syndicate = models.ForeignKey(
        'users.SyndicateProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'conversation'
        verbose_name_plural = 'conversations'
    
    def __str__(self):
        participant_names = ', '.join([p.get_full_name() or p.username for p in self.participants.all()[:3]])
        return f"Conversation: {participant_names}"
    
    def get_last_message(self):
        """Get the last message in the conversation"""
        return self.messages.order_by('-created_at').first()
    
    def get_unread_count(self, user):
        """Get unread message count for a specific user"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    """Model for individual messages within conversations"""
    
    # Conversation and sender
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    
    # Message threading - reply to specific messages
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    # Message content
    content = models.TextField()
    
    # Message editing
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_messages'
    )
    
    # Attachments (if any)
    attachment = models.FileField(
        upload_to='message_attachments/%Y/%m/%d/',
        blank=True,
        null=True
    )
    attachment_name = models.CharField(max_length=255, blank=True, null=True)
    attachment_type = models.CharField(max_length=50, blank=True, null=True)  # image, pdf, doc, etc
    attachment_size = models.IntegerField(null=True, blank=True)  # in bytes
    
    # Message status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'message'
        verbose_name_plural = 'messages'
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def soft_delete(self, user):
        """Soft delete a message"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()
    
    def get_display_content(self):
        """Get content to display (handle deleted messages)"""
        if self.is_deleted:
            return "This message has been deleted"
        return self.content
    
    def get_reply_count(self):
        """Get count of replies to this message"""
        return self.replies.filter(is_deleted=False).count()


class MessageReadReceipt(models.Model):
    """Track which users have read which messages"""
    
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_receipts'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_read_receipts'
    )
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']
        verbose_name = 'message read receipt'
        verbose_name_plural = 'message read receipts'
    
    def __str__(self):
        return f"{self.user.username} read message {self.message.id}"


class MessageReaction(models.Model):
    """Model for emoji reactions to messages"""
    
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_reactions'
    )
    emoji = models.CharField(max_length=10)  # Store emoji character
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user', 'emoji']
        verbose_name = 'message reaction'
        verbose_name_plural = 'message reactions'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to message {self.message.id}"


class MessageEditHistory(models.Model):
    """Track message edit history"""
    
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='edit_history'
    )
    previous_content = models.TextField()
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_edits'
    )
    edited_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'message edit history'
        verbose_name_plural = 'message edit histories'
        ordering = ['-edited_at']
    
    def __str__(self):
        return f"Edit to message {self.message.id} at {self.edited_at}"


class TypingIndicator(models.Model):
    """Track who is currently typing in a conversation"""
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='typing_indicators'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='typing_in_conversations'
    )
    started_typing_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['conversation', 'user']
        verbose_name = 'typing indicator'
        verbose_name_plural = 'typing indicators'
    
    def __str__(self):
        return f"{self.user.username} typing in conversation {self.conversation.id}"
    
    def is_active(self):
        """Check if typing indicator is still active (within 10 seconds)"""
        return (timezone.now() - self.started_typing_at).seconds < 10


class MessageAttachment(models.Model):
    """Model for multiple attachments per message"""
    
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='message_attachments/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)  # image, pdf, doc, video, etc
    file_size = models.IntegerField()  # in bytes
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    thumbnail = models.ImageField(
        upload_to='message_thumbnails/%Y/%m/%d/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'message attachment'
        verbose_name_plural = 'message attachments'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.file_name} attached to message {self.message.id}"
    
    def get_file_type_display(self):
        """Get user-friendly file type"""
        type_mapping = {
            'image': 'Image',
            'pdf': 'PDF Document',
            'doc': 'Word Document',
            'video': 'Video',
            'audio': 'Audio',
            'other': 'File'
        }
        return type_mapping.get(self.file_type, 'File')


class MessageNotification(models.Model):
    """Track message notifications"""
    
    NOTIFICATION_TYPES = [
        ('new_message', 'New Message'),
        ('mention', 'Mentioned in Message'),
        ('reply', 'Reply to Message'),
    ]
    
    DELIVERY_METHODS = [
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    ]
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_notifications'
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    delivery_method = models.CharField(max_length=10, choices=DELIVERY_METHODS)
    is_sent = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'message notification'
        verbose_name_plural = 'message notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.recipient.username}"
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save()
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
