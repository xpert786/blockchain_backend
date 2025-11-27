"""
WebSocket consumers for real-time messaging functionality.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Conversation, Message, MessageReaction, TypingIndicator

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat functionality.
    
    Handles:
    - Message sending and receiving
    - Typing indicators
    - Read receipts
    - Message reactions
    - Online/offline status
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope["user"]
        
        # Reject anonymous users
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Get conversation_id from URL
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'
        
        # Join conversation group
        await self.channel_layer.group_add(
            self.conversation_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Broadcast user online status
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'status': 'online',
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'conversation_group_name'):
            # Broadcast user offline status
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'status': 'offline',
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Leave conversation group
            await self.channel_layer.group_discard(
                self.conversation_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing_indicator':
                await self.handle_typing_indicator(data)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)
            elif message_type == 'message_reaction':
                await self.handle_message_reaction(data)
            elif message_type == 'message_edit':
                await self.handle_message_edit(data)
            elif message_type == 'message_delete':
                await self.handle_message_delete(data)
            else:
                await self.send(text_data=json.dumps({
                    'error': f'Unknown message type: {message_type}'
                }))
        except json.JSONDecodeError:
            # If it's plain text, treat it as a chat message
            if text_data and isinstance(text_data, str) and not text_data.startswith('{'):
                # Auto-convert plain text to chat message
                await self.handle_chat_message({'content': text_data})
            else:
                await self.send(text_data=json.dumps({
                    'error': 'Invalid JSON format. Please send JSON like: {"type": "chat_message", "content": "your message"}'
                }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
    
    async def handle_chat_message(self, data):
        """Handle new chat message."""
        content = data.get('content', '').strip()
        parent_message_id = data.get('parent_message_id')
        
        if not content:
            await self.send(text_data=json.dumps({
                'error': 'Message content cannot be empty'
            }))
            return
        
        # Create message in database
        message = await self.create_message(
            content=content,
            parent_message_id=parent_message_id
        )
        
        # Broadcast message to conversation group
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': {
                        'id': self.user.id,
                        'email': self.user.email,
                        'first_name': getattr(self.user, 'first_name', ''),
                        'last_name': getattr(self.user, 'last_name', ''),
                    },
                    'parent_message_id': message.parent_message_id,
                    'created_at': message.created_at.isoformat(),
                    'is_edited': message.is_edited,
                }
            }
        )
    
    async def handle_typing_indicator(self, data):
        """Handle typing indicator."""
        is_typing = data.get('is_typing', False)
        
        # Update typing indicator
        await self.update_typing_indicator(is_typing)
        
        # Broadcast typing status to others (excluding sender)
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'user_name': f"{getattr(self.user, 'first_name', '')} {getattr(self.user, 'last_name', '')}".strip() or self.user.email,
                'is_typing': is_typing,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def handle_read_receipt(self, data):
        """Handle read receipt."""
        message_id = data.get('message_id')
        
        if not message_id:
            return
        
        # Mark message as read
        await self.mark_message_read(message_id)
        
        # Broadcast read receipt
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'read_receipt',
                'message_id': message_id,
                'user_id': self.user.id,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def handle_message_reaction(self, data):
        """Handle message reaction."""
        message_id = data.get('message_id')
        emoji = data.get('emoji')
        
        if not message_id or not emoji:
            return
        
        # Add/toggle reaction
        reaction = await self.toggle_reaction(message_id, emoji)
        
        # Broadcast reaction
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'message_reaction',
                'message_id': message_id,
                'emoji': emoji,
                'user_id': self.user.id,
                'action': 'added' if reaction else 'removed',
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def handle_message_edit(self, data):
        """Handle message edit."""
        message_id = data.get('message_id')
        new_content = data.get('content', '').strip()
        
        if not message_id or not new_content:
            return
        
        # Update message
        message = await self.edit_message(message_id, new_content)
        
        if message:
            # Broadcast edit
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'message_edit',
                    'message_id': message_id,
                    'content': new_content,
                    'edited_at': message.edited_at.isoformat(),
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    async def handle_message_delete(self, data):
        """Handle message deletion."""
        message_id = data.get('message_id')
        
        if not message_id:
            return
        
        # Soft delete message
        success = await self.delete_message(message_id)
        
        if success:
            # Broadcast deletion
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'message_delete',
                    'message_id': message_id,
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    # Event handlers (receive from channel layer)
    
    async def chat_message(self, event):
        """Send chat message to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket (exclude own messages)."""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing'],
                'timestamp': event['timestamp']
            }))
    
    async def read_receipt(self, event):
        """Send read receipt to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))
    
    async def message_reaction(self, event):
        """Send message reaction to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'message_reaction',
            'message_id': event['message_id'],
            'emoji': event['emoji'],
            'user_id': event['user_id'],
            'action': event['action'],
            'timestamp': event['timestamp']
        }))
    
    async def message_edit(self, event):
        """Send message edit to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'message_edit',
            'message_id': event['message_id'],
            'content': event['content'],
            'edited_at': event['edited_at'],
            'timestamp': event['timestamp']
        }))
    
    async def message_delete(self, event):
        """Send message deletion to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'message_delete',
            'message_id': event['message_id'],
            'timestamp': event['timestamp']
        }))
    
    async def user_status(self, event):
        """Send user status to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))
    
    # Database operations
    
    @database_sync_to_async
    def create_message(self, content, parent_message_id=None):
        """Create a new message in the database."""
        conversation = Conversation.objects.get(id=self.conversation_id)
        
        parent_message = None
        if parent_message_id:
            try:
                parent_message = Message.objects.get(id=parent_message_id)
            except Message.DoesNotExist:
                pass
        
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content,
            parent_message=parent_message
        )
        
        # Update conversation's last message
        conversation.last_message = message
        conversation.updated_at = timezone.now()
        conversation.save()
        
        return message
    
    @database_sync_to_async
    def update_typing_indicator(self, is_typing):
        """Update typing indicator status."""
        conversation = Conversation.objects.get(id=self.conversation_id)
        
        if is_typing:
            TypingIndicator.objects.update_or_create(
                conversation=conversation,
                user=self.user,
                defaults={'timestamp': timezone.now()}
            )
        else:
            TypingIndicator.objects.filter(
                conversation=conversation,
                user=self.user
            ).delete()
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark a message as read."""
        try:
            from .models import MessageReadReceipt
            message = Message.objects.get(id=message_id)
            MessageReadReceipt.objects.get_or_create(
                message=message,
                user=self.user,
                defaults={'read_at': timezone.now()}
            )
        except Message.DoesNotExist:
            pass
    
    @database_sync_to_async
    def toggle_reaction(self, message_id, emoji):
        """Add or remove a reaction to a message."""
        try:
            message = Message.objects.get(id=message_id)
            reaction, created = MessageReaction.objects.get_or_create(
                message=message,
                user=self.user,
                emoji=emoji
            )
            
            if not created:
                # Reaction already exists, remove it
                reaction.delete()
                return None
            
            return reaction
        except Message.DoesNotExist:
            return None
    
    @database_sync_to_async
    def edit_message(self, message_id, new_content):
        """Edit a message."""
        try:
            from .models import MessageEditHistory
            message = Message.objects.get(id=message_id, sender=self.user)
            
            # Create edit history
            MessageEditHistory.objects.create(
                message=message,
                previous_content=message.content,
                edited_by=self.user
            )
            
            # Update message
            message.content = new_content
            message.is_edited = True
            message.edited_at = timezone.now()
            message.save()
            
            return message
        except Message.DoesNotExist:
            return None
    
    @database_sync_to_async
    def delete_message(self, message_id):
        """Soft delete a message."""
        try:
            message = Message.objects.get(id=message_id, sender=self.user)
            message.is_deleted = True
            message.deleted_at = timezone.now()
            message.deleted_by = self.user
            message.save()
            return True
        except Message.DoesNotExist:
            return False
