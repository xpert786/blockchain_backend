from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Conversation, Message, MessageReadReceipt, MessageReaction,
    MessageEditHistory, TypingIndicator, MessageAttachment, MessageNotification
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for messages"""
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'first_name', 'last_name', 'role']
    
    def get_name(self, obj):
        return obj.get_full_name() or obj.username


class MessageReactionSerializer(serializers.ModelSerializer):
    """Serializer for message reactions"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = ['id', 'message', 'user', 'emoji', 'created_at']
        read_only_fields = ['user', 'created_at']


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for message attachments"""
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageAttachment
        fields = [
            'id', 'file', 'file_name', 'file_type', 'file_type_display',
            'file_size', 'mime_type', 'file_url', 'thumbnail', 'thumbnail_url', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for individual messages"""
    sender = UserBasicSerializer(read_only=True)
    sender_name = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    reactions = MessageReactionSerializer(many=True, read_only=True)
    reactions_summary = serializers.SerializerMethodField()
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    reply_count = serializers.SerializerMethodField()
    parent_message_preview = serializers.SerializerMethodField()
    display_content = serializers.CharField(source='get_display_content', read_only=True)
    read_by = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender',
            'sender_name',
            'parent_message',
            'parent_message_preview',
            'content',
            'display_content',
            'attachment',
            'attachment_name',
            'attachment_type',
            'attachment_size',
            'attachments',
            'is_read',
            'read_at',
            'read_by',
            'is_edited',
            'edited_at',
            'is_deleted',
            'deleted_at',
            'reactions',
            'reactions_summary',
            'reply_count',
            'created_at',
            'updated_at',
            'time_ago'
        ]
        read_only_fields = ['sender', 'created_at', 'updated_at', 'read_at', 'is_edited', 'edited_at']
    
    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.username
    
    def get_time_ago(self, obj):
        """Return a human-readable time ago string"""
        from django.utils.timesince import timesince
        return timesince(obj.created_at) + ' ago'
    
    def get_reactions_summary(self, obj):
        """Group reactions by emoji with counts"""
        reactions = {}
        for reaction in obj.reactions.all():
            if reaction.emoji not in reactions:
                reactions[reaction.emoji] = {
                    'emoji': reaction.emoji,
                    'count': 0,
                    'users': []
                }
            reactions[reaction.emoji]['count'] += 1
            reactions[reaction.emoji]['users'].append({
                'id': reaction.user.id,
                'name': reaction.user.get_full_name() or reaction.user.username
            })
        return list(reactions.values())
    
    def get_reply_count(self, obj):
        """Get count of replies"""
        return obj.get_reply_count()
    
    def get_parent_message_preview(self, obj):
        """Get preview of parent message if this is a reply"""
        if obj.parent_message and not obj.parent_message.is_deleted:
            return {
                'id': obj.parent_message.id,
                'sender_name': obj.parent_message.sender.get_full_name() or obj.parent_message.sender.username,
                'content': obj.parent_message.content[:100] + '...' if len(obj.parent_message.content) > 100 else obj.parent_message.content
            }
        return None
    
    def get_read_by(self, obj):
        """Get list of users who have read this message"""
        return [
            {
                'id': receipt.user.id,
                'name': receipt.user.get_full_name() or receipt.user.username,
                'read_at': receipt.read_at
            }
            for receipt in obj.read_receipts.all()
        ]


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages"""
    attachment_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Message
        fields = ['conversation', 'parent_message', 'content', 'attachment', 'attachment_files']
    
    def create(self, validated_data):
        # Extract attachment files if provided
        attachment_files = validated_data.pop('attachment_files', [])
        
        # Sender is set from the request user in the view
        message = super().create(validated_data)
        
        # Create multiple attachments if provided
        if attachment_files:
            for file in attachment_files:
                self._create_attachment(message, file)
        
        return message
    
    def _create_attachment(self, message, file):
        """Create a MessageAttachment from uploaded file"""
        import os
        import mimetypes
        
        file_name = file.name
        file_size = file.size
        mime_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
        
        # Determine file type
        file_type = 'other'
        if mime_type.startswith('image/'):
            file_type = 'image'
        elif mime_type == 'application/pdf':
            file_type = 'pdf'
        elif mime_type.startswith('video/'):
            file_type = 'video'
        elif mime_type.startswith('audio/'):
            file_type = 'audio'
        elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            file_type = 'doc'
        
        MessageAttachment.objects.create(
            message=message,
            file=file,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            mime_type=mime_type
        )


class MessageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating/editing messages"""
    
    class Meta:
        model = Message
        fields = ['content']
    
    def update(self, instance, validated_data):
        # Save edit history before updating
        MessageEditHistory.objects.create(
            message=instance,
            previous_content=instance.content,
            edited_by=self.context['request'].user
        )
        
        # Update message
        instance.content = validated_data.get('content', instance.content)
        instance.is_edited = True
        instance.edited_at = timezone.now()
        instance.save()
        
        return instance


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer for listing conversations"""
    participants = UserBasicSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    participant_info = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id',
            'subject',
            'is_group_conversation',
            'participants',
            'other_participant',
            'participant_info',
            'last_message',
            'unread_count',
            'status',
            'created_at',
            'updated_at'
        ]
    
    def get_last_message(self, obj):
        last_msg = obj.get_last_message()
        if last_msg:
            return {
                'id': last_msg.id,
                'content': last_msg.content,
                'sender': last_msg.sender.get_full_name() or last_msg.sender.username,
                'sender_id': last_msg.sender.id,
                'created_at': last_msg.created_at,
                'time_ago': self._get_time_ago(last_msg.created_at)
            }
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.get_unread_count(request.user)
        return 0
    
    def get_other_participant(self, obj):
        """Get the other participant in a 1-on-1 conversation"""
        request = self.context.get('request')
        if request and request.user and not obj.is_group_conversation:
            other_participants = obj.participants.exclude(id=request.user.id)
            if other_participants.exists():
                other = other_participants.first()
                return UserBasicSerializer(other).data
        return None
    
    def get_participant_info(self, obj):
        """Get formatted participant info for display"""
        request = self.context.get('request')
        if request and request.user:
            other_participants = obj.participants.exclude(id=request.user.id)
            if other_participants.exists():
                other = other_participants.first()
                return {
                    'name': other.get_full_name() or other.username,
                    'role': other.role,
                    'initials': self._get_initials(other)
                }
        return None
    
    def get_status(self, obj):
        """Get online/offline status (placeholder - implement with websockets)"""
        # For now, return 'Online' or 'Offline' - can be enhanced with real-time status
        return 'Online'
    
    def _get_time_ago(self, dt):
        """Return a human-readable time ago string"""
        from django.utils.timesince import timesince
        return timesince(dt) + ' ago'
    
    def _get_initials(self, user):
        """Get user initials for avatar"""
        if user.first_name and user.last_name:
            return f"{user.first_name[0]}{user.last_name[0]}".upper()
        elif user.first_name:
            return user.first_name[0].upper()
        elif user.username:
            return user.username[0].upper()
        return "?"


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Serializer for conversation detail with messages"""
    participants = UserBasicSerializer(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id',
            'subject',
            'is_group_conversation',
            'participants',
            'messages',
            'unread_count',
            'created_at',
            'updated_at'
        ]
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.get_unread_count(request.user)
        return 0


class ConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating conversations"""
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    initial_message = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Conversation
        fields = ['subject', 'participant_ids', 'initial_message', 'is_group_conversation']
    
    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids')
        initial_message = validated_data.pop('initial_message', None)
        
        # Create conversation
        conversation = Conversation.objects.create(**validated_data)
        
        # Add participants
        participants = User.objects.filter(id__in=participant_ids)
        conversation.participants.add(*participants)
        
        # Add the creator to participants
        request = self.context.get('request')
        if request and request.user:
            conversation.participants.add(request.user)
        
        # Create initial message if provided
        if initial_message and request and request.user:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=initial_message
            )
        
        return conversation


class TypingIndicatorSerializer(serializers.ModelSerializer):
    """Serializer for typing indicators"""
    user = UserBasicSerializer(read_only=True)
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = TypingIndicator
        fields = ['id', 'conversation', 'user', 'started_typing_at', 'is_active']
        read_only_fields = ['user', 'started_typing_at']
    
    def get_is_active(self, obj):
        return obj.is_active()


class MessageNotificationSerializer(serializers.ModelSerializer):
    """Serializer for message notifications"""
    message_preview = serializers.SerializerMethodField()
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageNotification
        fields = [
            'id', 'recipient', 'message', 'notification_type',
            'delivery_method', 'is_sent', 'is_read', 'sent_at',
            'read_at', 'created_at', 'message_preview', 'sender_name'
        ]
        read_only_fields = ['is_sent', 'sent_at', 'read_at', 'created_at']
    
    def get_message_preview(self, obj):
        content = obj.message.content
        return content[:100] + '...' if len(content) > 100 else content
    
    def get_sender_name(self, obj):
        return obj.message.sender.get_full_name() or obj.message.sender.username


from django.utils import timezone
