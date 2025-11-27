# WebSocket Implementation Guide

## Overview

The messaging system now includes full WebSocket support for real-time communication. This allows instant message delivery, typing indicators, online status, and more without polling.

## Connection URL

```
ws://localhost:8000/ws/chat/{conversation_id}/?token=YOUR_JWT_TOKEN
```

For production with SSL:
```
wss://yourdomain.com/ws/chat/{conversation_id}/?token=YOUR_JWT_TOKEN
```

## Authentication

WebSockets use JWT token authentication. Pass your access token as a query parameter:

### JavaScript/React Example
```javascript
const token = localStorage.getItem('access_token');
const conversationId = 123;

// Using native WebSocket with JWT token
const ws = new WebSocket(`ws://localhost:8000/ws/chat/${conversationId}/?token=${token}`);

ws.onopen = () => {
  console.log('WebSocket connected');
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
};
```

**Important**: Always include your JWT access token in the query string for authentication.

## Message Types

### 1. Send Chat Message

**Client → Server:**
```json
{
  "type": "chat_message",
  "content": "Hello, this is a message!",
  "parent_message_id": null  // Optional, for threading
}
```

**Server → All Clients:**
```json
{
  "type": "chat_message",
  "message": {
    "id": 456,
    "content": "Hello, this is a message!",
    "sender": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe"
    },
    "parent_message_id": null,
    "created_at": "2025-11-26T10:30:00Z",
    "is_edited": false
  }
}
```

### 2. Typing Indicator

**Client → Server:**
```json
{
  "type": "typing_indicator",
  "is_typing": true  // or false when stopped
}
```

**Server → Other Clients:**
```json
{
  "type": "typing_indicator",
  "user_id": 1,
  "user_name": "John Doe",
  "is_typing": true,
  "timestamp": "2025-11-26T10:30:00Z"
}
```

### 3. Read Receipt

**Client → Server:**
```json
{
  "type": "read_receipt",
  "message_id": 456
}
```

**Server → All Clients:**
```json
{
  "type": "read_receipt",
  "message_id": 456,
  "user_id": 1,
  "timestamp": "2025-11-26T10:30:00Z"
}
```

### 4. Message Reaction

**Client → Server:**
```json
{
  "type": "message_reaction",
  "message_id": 456,
  "emoji": "👍"
}
```

**Server → All Clients:**
```json
{
  "type": "message_reaction",
  "message_id": 456,
  "emoji": "👍",
  "user_id": 1,
  "action": "added",  // or "removed"
  "timestamp": "2025-11-26T10:30:00Z"
}
```

### 5. Edit Message

**Client → Server:**
```json
{
  "type": "message_edit",
  "message_id": 456,
  "content": "Updated message content"
}
```

**Server → All Clients:**
```json
{
  "type": "message_edit",
  "message_id": 456,
  "content": "Updated message content",
  "edited_at": "2025-11-26T10:35:00Z",
  "timestamp": "2025-11-26T10:35:00Z"
}
```

### 6. Delete Message

**Client → Server:**
```json
{
  "type": "message_delete",
  "message_id": 456
}
```

**Server → All Clients:**
```json
{
  "type": "message_delete",
  "message_id": 456,
  "timestamp": "2025-11-26T10:35:00Z"
}
```

### 7. User Status (Automatic)

When user connects/disconnects:

**Server → All Clients:**
```json
{
  "type": "user_status",
  "user_id": 1,
  "status": "online",  // or "offline"
  "timestamp": "2025-11-26T10:30:00Z"
}
```

## React Implementation Example

### Custom Hook for WebSocket

```javascript
// hooks/useWebSocket.js
import { useEffect, useRef, useState, useCallback } from 'react';

export const useWebSocket = (conversationId) => {
  const [messages, setMessages] = useState([]);
  const [typingUsers, setTypingUsers] = useState({});
  const [onlineUsers, setOnlineUsers] = useState({});
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    if (!conversationId) return;

    // Get JWT token from localStorage
    const token = localStorage.getItem('access_token');
    if (!token) {
      console.error('No access token found');
      return;
    }

    // Connect to WebSocket with JWT token
    ws.current = new WebSocket(
      `ws://localhost:8000/ws/chat/${conversationId}/?token=${token}`
    );

    ws.current.onopen = () => {
      console.log('WebSocket Connected');
      setIsConnected(true);
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleMessage(data);
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };

    ws.current.onclose = () => {
      console.log('WebSocket Disconnected');
      setIsConnected(false);
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [conversationId]);

  const handleMessage = (data) => {
    switch (data.type) {
      case 'chat_message':
        setMessages(prev => [...prev, data.message]);
        break;
      
      case 'typing_indicator':
        if (data.is_typing) {
          setTypingUsers(prev => ({
            ...prev,
            [data.user_id]: data.user_name
          }));
          // Clear after 3 seconds
          setTimeout(() => {
            setTypingUsers(prev => {
              const newTyping = { ...prev };
              delete newTyping[data.user_id];
              return newTyping;
            });
          }, 3000);
        } else {
          setTypingUsers(prev => {
            const newTyping = { ...prev };
            delete newTyping[data.user_id];
            return newTyping;
          });
        }
        break;
      
      case 'read_receipt':
        setMessages(prev => prev.map(msg =>
          msg.id === data.message_id
            ? { ...msg, read_by: [...(msg.read_by || []), data.user_id] }
            : msg
        ));
        break;
      
      case 'message_reaction':
        setMessages(prev => prev.map(msg => {
          if (msg.id === data.message_id) {
            const reactions = msg.reactions || {};
            if (data.action === 'added') {
              reactions[data.emoji] = [...(reactions[data.emoji] || []), data.user_id];
            } else {
              reactions[data.emoji] = reactions[data.emoji].filter(id => id !== data.user_id);
            }
            return { ...msg, reactions };
          }
          return msg;
        }));
        break;
      
      case 'message_edit':
        setMessages(prev => prev.map(msg =>
          msg.id === data.message_id
            ? { ...msg, content: data.content, is_edited: true, edited_at: data.edited_at }
            : msg
        ));
        break;
      
      case 'message_delete':
        setMessages(prev => prev.map(msg =>
          msg.id === data.message_id
            ? { ...msg, is_deleted: true, content: 'Message deleted' }
            : msg
        ));
        break;
      
      case 'user_status':
        setOnlineUsers(prev => ({
          ...prev,
          [data.user_id]: data.status === 'online'
        }));
        break;
    }
  };

  const sendMessage = useCallback((content, parentMessageId = null) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'chat_message',
        content,
        parent_message_id: parentMessageId
      }));
    }
  }, []);

  const sendTypingIndicator = useCallback((isTyping) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'typing_indicator',
        is_typing: isTyping
      }));
    }
  }, []);

  const sendReadReceipt = useCallback((messageId) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'read_receipt',
        message_id: messageId
      }));
    }
  }, []);

  const sendReaction = useCallback((messageId, emoji) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'message_reaction',
        message_id: messageId,
        emoji
      }));
    }
  }, []);

  const editMessage = useCallback((messageId, content) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'message_edit',
        message_id: messageId,
        content
      }));
    }
  }, []);

  const deleteMessage = useCallback((messageId) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'message_delete',
        message_id: messageId
      }));
    }
  }, []);

  return {
    messages,
    typingUsers,
    onlineUsers,
    isConnected,
    sendMessage,
    sendTypingIndicator,
    sendReadReceipt,
    sendReaction,
    editMessage,
    deleteMessage
  };
};
```

### Using the Hook in a Component

```javascript
// components/ChatRoom.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

const ChatRoom = ({ conversationId }) => {
  const [inputValue, setInputValue] = useState('');
  const {
    messages,
    typingUsers,
    onlineUsers,
    isConnected,
    sendMessage,
    sendTypingIndicator,
    sendReadReceipt,
    sendReaction,
    editMessage,
    deleteMessage
  } = useWebSocket(conversationId);

  const typingTimeoutRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Mark messages as read when they appear
  useEffect(() => {
    messages.forEach(msg => {
      if (!msg.is_read) {
        sendReadReceipt(msg.id);
      }
    });
  }, [messages, sendReadReceipt]);

  const handleInputChange = (e) => {
    setInputValue(e.target.value);

    // Send typing indicator
    sendTypingIndicator(true);

    // Clear previous timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Stop typing after 2 seconds of inactivity
    typingTimeoutRef.current = setTimeout(() => {
      sendTypingIndicator(false);
    }, 2000);
  };

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      sendMessage(inputValue);
      setInputValue('');
      sendTypingIndicator(false);
    }
  };

  const typingUsersList = Object.values(typingUsers);

  return (
    <div className="chat-room">
      <div className="chat-header">
        <h3>Chat Room</h3>
        <div className="connection-status">
          {isConnected ? (
            <span className="connected">● Connected</span>
          ) : (
            <span className="disconnected">● Disconnected</span>
          )}
        </div>
      </div>

      <div className="messages-container">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.is_deleted ? 'deleted' : ''}`}>
            <div className="message-header">
              <strong>{msg.sender.first_name} {msg.sender.last_name}</strong>
              <span className="timestamp">
                {new Date(msg.created_at).toLocaleTimeString()}
              </span>
              {onlineUsers[msg.sender.id] && (
                <span className="online-indicator">●</span>
              )}
            </div>
            <div className="message-content">
              {msg.content}
              {msg.is_edited && <span className="edited-label">(edited)</span>}
            </div>
            <div className="message-actions">
              <button onClick={() => sendReaction(msg.id, '👍')}>👍</button>
              <button onClick={() => sendReaction(msg.id, '❤️')}>❤️</button>
              <button onClick={() => sendReaction(msg.id, '😂')}>😂</button>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {typingUsersList.length > 0 && (
        <div className="typing-indicator">
          {typingUsersList.join(', ')} {typingUsersList.length === 1 ? 'is' : 'are'} typing...
        </div>
      )}

      <form onSubmit={handleSendMessage} className="message-input-form">
        <input
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          placeholder="Type a message..."
          disabled={!isConnected}
        />
        <button type="submit" disabled={!isConnected || !inputValue.trim()}>
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatRoom;
```

## Running with WebSocket Support

### Development Server

Use Daphne (ASGI server) instead of Django's runserver:

```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run with Daphne
daphne -b 0.0.0.0 -p 8000 blockchain_admin.asgi:application
```

Or you can still use Django's development server (it supports both HTTP and WebSocket):

```bash
python manage.py runserver
```

### Production Deployment

For production, use Daphne with a process manager like systemd or supervisor:

```bash
daphne -b 0.0.0.0 -p 8000 blockchain_admin.asgi:application
```

Configure Nginx to proxy WebSocket connections:

```nginx
upstream channels-backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    location /ws/ {
        proxy_pass http://channels-backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location / {
        proxy_pass http://channels-backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Using Redis for Channel Layer (Production)

For production with multiple server instances, use Redis:

1. Install Redis:
```bash
# Windows (using Chocolatey)
choco install redis-64

# Or use Docker
docker run -p 6379:6379 -d redis:7
```

2. Update settings.py:
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

## Testing WebSocket Connection

### Using Browser Console

```javascript
// Open browser console on your app
// First, get your JWT token (after logging in)
const token = localStorage.getItem('access_token');

// Connect with token
const ws = new WebSocket(`ws://localhost:8000/ws/chat/1/?token=${token}`);

ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Received:', JSON.parse(e.data));
ws.onerror = (e) => console.error('Error:', e);

// Send a message
ws.send(JSON.stringify({
  type: 'chat_message',
  content: 'Hello from console!'
}));

// Send typing indicator
ws.send(JSON.stringify({
  type: 'typing_indicator',
  is_typing: true
}));
```

### Using Postman or WebSocket Testing Tools

1. First, get your JWT access token by logging in via the API
2. Open Postman or use online tool like: https://www.piesocket.com/websocket-tester
3. Connect to: `ws://localhost:8000/ws/chat/1/?token=YOUR_JWT_TOKEN`
4. Send JSON messages as shown above

## Troubleshooting

### Connection Refused
- Make sure server is running with Daphne or Django runserver
- Check that ASGI application is configured correctly
- Verify firewall settings

### Authentication Issues
- WebSocket uses Django session authentication by default
- Ensure user is logged in via Django admin or session-based login
- For JWT authentication, implement custom middleware

### Messages Not Broadcasting
- Check that CHANNEL_LAYERS is configured
- For production, ensure Redis is running
- Verify conversation_id exists in database

### Performance Issues
- Use Redis channel layer for production
- Consider implementing message pagination
- Add rate limiting for message sending

## Next Steps

1. **Implement JWT Authentication for WebSocket**: Add custom middleware to authenticate via JWT tokens
2. **Add Push Notifications**: Integrate with FCM or similar service
3. **File Upload via WebSocket**: Implement chunked file uploads
4. **Voice/Video Calls**: Add WebRTC support for real-time communication
5. **Message Search**: Index messages for full-text search
6. **Analytics**: Track message delivery, read rates, response times

## Additional Resources

- [Django Channels Documentation](https://channels.readthedocs.io/)
- [WebSocket API MDN](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Redis Documentation](https://redis.io/documentation)
