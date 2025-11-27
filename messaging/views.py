from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Max, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import (
    Conversation, Message, MessageReadReceipt, MessageReaction,
    MessageEditHistory, TypingIndicator, MessageAttachment, MessageNotification
)
from .serializers import (
    ConversationListSerializer,
    ConversationDetailSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
    MessageCreateSerializer,
    MessageUpdateSerializer,
    MessageReactionSerializer,
    TypingIndicatorSerializer,
    MessageNotificationSerializer,
    MessageAttachmentSerializer
)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations
    
    Endpoints:
    - GET /api/conversations/ - List all conversations for the current user
    - POST /api/conversations/ - Create a new conversation
    - GET /api/conversations/{id}/ - Get conversation details with messages
    - DELETE /api/conversations/{id}/ - Delete a conversation
    - GET /api/conversations/{id}/messages/ - Get all messages in a conversation
    - POST /api/conversations/{id}/mark_as_read/ - Mark all messages as read
    - POST /api/conversations/{id}/start_typing/ - Indicate user is typing
    - POST /api/conversations/{id}/stop_typing/ - Indicate user stopped typing
    - GET /api/conversations/{id}/typing/ - Get who is currently typing
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get conversations for the current user"""
        user = self.request.user
        return Conversation.objects.filter(
            participants=user
        ).prefetch_related('participants', 'messages').distinct()
    
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'list':
            return ConversationListSerializer
        elif self.action == 'create':
            return ConversationCreateSerializer
        elif self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationListSerializer
    
    def list(self, request, *args, **kwargs):
        """List all conversations with last message and unread count"""
        queryset = self.get_queryset().order_by('-updated_at')
        
        # Optional filter by search query
        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(subject__icontains=search) |
                Q(participants__username__icontains=search) |
                Q(participants__first_name__icontains=search) |
                Q(participants__last_name__icontains=search) |
                Q(messages__content__icontains=search)
            ).distinct()
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create a new conversation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        
        # Return the created conversation with detail serializer
        return Response(
            ConversationDetailSerializer(
                conversation,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Get conversation details with all messages"""
        conversation = self.get_object()
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages in a conversation"""
        conversation = self.get_object()
        messages = conversation.messages.filter(is_deleted=False).order_by('created_at')
        
        # Pagination
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark all messages in a conversation as read for the current user"""
        conversation = self.get_object()
        user = request.user
        
        # Mark all unread messages as read
        unread_messages = conversation.messages.filter(
            is_read=False,
            is_deleted=False
        ).exclude(sender=user)
        
        for message in unread_messages:
            message.mark_as_read()
            # Create read receipt
            MessageReadReceipt.objects.get_or_create(
                message=message,
                user=user
            )
        
        return Response({
            'status': 'success',
            'marked_read': unread_messages.count()
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get total unread message count for the current user"""
        user = request.user
        total_unread = Message.objects.filter(
            conversation__participants=user,
            is_read=False,
            is_deleted=False
        ).exclude(sender=user).count()
        
        return Response({
            'unread_count': total_unread
        })
    
    @action(detail=False, methods=['post'])
    def start_conversation(self, request):
        """
        Start a conversation with a specific user or group
        Body: {
            "participant_id": 123,  // For 1-on-1
            "participant_ids": [123, 456],  // For group
            "initial_message": "Hello!",
            "subject": "Investment Question"
        }
        """
        participant_id = request.data.get('participant_id')
        participant_ids = request.data.get('participant_ids', [])
        initial_message = request.data.get('initial_message', '')
        subject = request.data.get('subject', '')
        
        # Determine if it's a 1-on-1 or group conversation
        if participant_id:
            participant_ids = [participant_id]
        
        if not participant_ids:
            return Response(
                {'error': 'participant_id or participant_ids required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if conversation already exists (for 1-on-1)
        if len(participant_ids) == 1:
            existing_conversation = Conversation.objects.filter(
                participants=request.user,
                is_group_conversation=False
            ).filter(
                participants__id=participant_ids[0]
            ).first()
            
            if existing_conversation:
                # Return existing conversation
                return Response(
                    ConversationDetailSerializer(
                        existing_conversation,
                        context={'request': request}
                    ).data
                )
        
        # Create new conversation
        serializer = ConversationCreateSerializer(
            data={
                'participant_ids': participant_ids,
                'initial_message': initial_message,
                'subject': subject,
                'is_group_conversation': len(participant_ids) > 1
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        
        return Response(
            ConversationDetailSerializer(
                conversation,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def start_typing(self, request, pk=None):
        """Indicate that user has started typing in this conversation"""
        conversation = self.get_object()
        user = request.user
        
        typing_indicator, created = TypingIndicator.objects.get_or_create(
            conversation=conversation,
            user=user
        )
        
        # Update timestamp (auto_now will handle this)
        typing_indicator.save()
        
        return Response({'status': 'typing'})
    
    @action(detail=True, methods=['post'])
    def stop_typing(self, request, pk=None):
        """Indicate that user has stopped typing"""
        conversation = self.get_object()
        user = request.user
        
        TypingIndicator.objects.filter(
            conversation=conversation,
            user=user
        ).delete()
        
        return Response({'status': 'stopped'})
    
    @action(detail=True, methods=['get'])
    def typing(self, request, pk=None):
        """Get list of users currently typing (exclude current user)"""
        conversation = self.get_object()
        user = request.user
        
        # Get active typing indicators (within last 10 seconds)
        active_typing = TypingIndicator.objects.filter(
            conversation=conversation,
            started_typing_at__gte=timezone.now() - timezone.timedelta(seconds=10)
        ).exclude(user=user)
        
        serializer = TypingIndicatorSerializer(active_typing, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages
    
    Endpoints:
    - GET /api/messages/ - List all messages (not typically used)
    - POST /api/messages/ - Send a new message
    - GET /api/messages/{id}/ - Get a specific message
    - PATCH /api/messages/{id}/ - Update a message
    - DELETE /api/messages/{id}/ - Delete a message (soft delete)
    - POST /api/messages/{id}/mark_read/ - Mark a message as read
    - POST /api/messages/{id}/react/ - Add a reaction to a message
    - DELETE /api/messages/{id}/react/ - Remove a reaction
    - GET /api/messages/{id}/reactions/ - Get all reactions
    - GET /api/messages/{id}/edit_history/ - Get edit history
    - GET /api/messages/{id}/replies/ - Get all replies to this message
    - POST /api/messages/search/ - Search messages
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get messages accessible by the current user"""
        user = self.request.user
        return Message.objects.filter(
            conversation__participants=user
        ).select_related('sender', 'conversation')
    
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'create':
            return MessageCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MessageUpdateSerializer
        return MessageSerializer
    
    def create(self, request, *args, **kwargs):
        """Send a new message"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set the sender to the current user
        message = serializer.save(sender=request.user)
        
        # Update conversation's updated_at timestamp
        message.conversation.save()
        
        # Create notifications for other participants
        self._create_notifications(message)
        
        # Return the created message
        return Response(
            MessageSerializer(message, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Edit a message (only sender can edit)"""
        message = self.get_object()
        
        # Check if user is the sender
        if message.sender != request.user:
            return Response(
                {'error': 'You can only edit your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if message is deleted
        if message.is_deleted:
            return Response(
                {'error': 'Cannot edit deleted messages'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(message, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(MessageSerializer(message, context={'request': request}).data)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete a message"""
        message = self.get_object()
        
        # Check if user is the sender
        if message.sender != request.user:
            return Response(
                {'error': 'You can only delete your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete
        message.soft_delete(request.user)
        
        return Response({'status': 'deleted', 'message': 'Message deleted successfully'})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a specific message as read"""
        message = self.get_object()
        
        # Only mark as read if current user is not the sender
        if message.sender != request.user:
            message.mark_as_read()
            MessageReadReceipt.objects.get_or_create(
                message=message,
                user=request.user
            )
        
        return Response({
            'status': 'success',
            'message_id': message.id,
            'is_read': message.is_read
        })
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent messages for the current user"""
        user = request.user
        messages = self.get_queryset().filter(is_deleted=False).order_by('-created_at')[:50]
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post', 'delete'])
    def react(self, request, pk=None):
        """Add or remove a reaction to/from a message"""
        message = self.get_object()
        emoji = request.data.get('emoji')
        
        if not emoji:
            return Response(
                {'error': 'emoji is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.method == 'POST':
            # Create or get reaction
            reaction, created = MessageReaction.objects.get_or_create(
                message=message,
                user=request.user,
                emoji=emoji
            )
            
            return Response({
                'status': 'success',
                'created': created,
                'reaction': MessageReactionSerializer(reaction).data
            })
        
        elif request.method == 'DELETE':
            # Delete reaction
            deleted_count = MessageReaction.objects.filter(
                message=message,
                user=request.user,
                emoji=emoji
            ).delete()[0]
            
            return Response({
                'status': 'success',
                'removed': deleted_count > 0
            })
    
    @action(detail=True, methods=['get'])
    def reactions(self, request, pk=None):
        """Get all reactions for a message"""
        message = self.get_object()
        reactions = message.reactions.all()
        serializer = MessageReactionSerializer(reactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def edit_history(self, request, pk=None):
        """Get edit history for a message"""
        message = self.get_object()
        history = message.edit_history.all()
        
        history_data = [
            {
                'id': h.id,
                'previous_content': h.previous_content,
                'edited_by': h.edited_by.get_full_name() or h.edited_by.username,
                'edited_at': h.edited_at
            }
            for h in history
        ]
        
        return Response(history_data)
    
    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """Get all replies to this message"""
        message = self.get_object()
        replies = message.replies.filter(is_deleted=False).order_by('created_at')
        serializer = MessageSerializer(replies, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """
        Search messages
        Body: {
            "query": "search text",
            "conversation_id": 123  // optional
        }
        """
        query = request.data.get('query', '')
        conversation_id = request.data.get('conversation_id')
        
        if not query:
            return Response(
                {'error': 'query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start with user's accessible messages
        messages = self.get_queryset().filter(
            is_deleted=False,
            content__icontains=query
        )
        
        # Filter by conversation if specified
        if conversation_id:
            messages = messages.filter(conversation_id=conversation_id)
        
        # Order by relevance (most recent first)
        messages = messages.order_by('-created_at')[:50]
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response({
            'query': query,
            'count': messages.count(),
            'results': serializer.data
        })
    
    def _create_notifications(self, message):
        """Create notifications for other participants in the conversation"""
        participants = message.conversation.participants.exclude(id=message.sender.id)
        
        for participant in participants:
            # Create in-app notification
            MessageNotification.objects.create(
                recipient=participant,
                message=message,
                notification_type='new_message',
                delivery_method='in_app'
            )
            
            # TODO: Send email notification if user has email notifications enabled
            # TODO: Send push notification if user has push notifications enabled


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing notifications
    
    Endpoints:
    - GET /api/notifications/ - List all notifications
    - GET /api/notifications/{id}/ - Get specific notification
    - POST /api/notifications/{id}/mark_read/ - Mark as read
    - POST /api/notifications/mark_all_read/ - Mark all as read
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageNotificationSerializer
    
    def get_queryset(self):
        """Get notifications for current user"""
        return MessageNotification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        
        return Response({
            'status': 'success',
            'notification_id': notification.id,
            'is_read': notification.is_read
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'status': 'success',
            'marked_read': updated
        })
