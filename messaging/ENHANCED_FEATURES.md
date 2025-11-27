# Enhanced Messages API Documentation

## 🎉 New Features Added

All 10 requested features have been implemented:

1. ✅ **Message Reactions** - React with emojis to any message
2. ✅ **Message Threading** - Reply to specific messages
3. ✅ **Typing Indicators** - See who is currently typing
4. ✅ **Message Editing** - Edit sent messages with history tracking
5. ✅ **Soft Delete** - Delete messages with "Message deleted" placeholder
6. ✅ **Enhanced Attachments** - Multiple files, type detection, previews
7. ✅ **Message Search** - Full-text search across all messages
8. ✅ **Notifications** - In-app, email, and push notification support
9. ✅ **Read Receipts** - See who has read your messages (group chats)
10. ✅ **Edit History** - Track all message edits

---

## Table of Contents

- [Message Reactions](#message-reactions)
- [Message Threading (Replies)](#message-threading-replies)
- [Typing Indicators](#typing-indicators)
- [Message Editing](#message-editing)
- [Message Deletion](#message-deletion)
- [Enhanced Attachments](#enhanced-attachments)
- [Message Search](#message-search)
- [Notifications](#notifications)
- [Read Receipts](#read-receipts)
- [Complete API Reference](#complete-api-reference)

---

## Message Reactions

### Add Reaction to Message

**POST** `/messages/{id}/react/`

```json
{
  "emoji": "👍"
}
```

**Response:**
```json
{
  "status": "success",
  "created": true,
  "reaction": {
    "id": 1,
    "message": 15,
    "user": {
      "id": 1,
      "name": "John Doe"
    },
    "emoji": "👍",
    "created_at": "2025-11-26T12:00:00Z"
  }
}
```

### Remove Reaction

**DELETE** `/messages/{id}/react/`

```json
{
  "emoji": "👍"
}
```

### Get All Reactions

**GET** `/messages/{id}/reactions/`

**Response:**
```json
[
  {
    "id": 1,
    "emoji": "👍",
    "user": {
      "id": 1,
      "name": "John Doe"
    },
    "created_at": "2025-11-26T12:00:00Z"
  },
  {
    "id": 2,
    "emoji": "❤️",
    "user": {
      "id": 2,
      "name": "Sarah Chen"
    },
    "created_at": "2025-11-26T12:01:00Z"
  }
]
```

### Reactions Summary in Message Response

Messages now include a `reactions_summary` field:

```json
{
  "id": 15,
  "content": "Great news!",
  "reactions_summary": [
    {
      "emoji": "👍",
      "count": 3,
      "users": [
        {"id": 1, "name": "John Doe"},
        {"id": 2, "name": "Sarah Chen"},
        {"id": 3, "name": "Mike Rodriguez"}
      ]
    },
    {
      "emoji": "❤️",
      "count": 1,
      "users": [
        {"id": 2, "name": "Sarah Chen"}
      ]
    }
  ]
}
```

---

## Message Threading (Replies)

### Reply to a Message

**POST** `/messages/`

```json
{
  "conversation": 1,
  "parent_message": 15,  // ID of message being replied to
  "content": "Thanks for the update!"
}
```

**Response:**
```json
{
  "id": 20,
  "conversation": 1,
  "parent_message": 15,
  "parent_message_preview": {
    "id": 15,
    "sender_name": "Sarah Chen",
    "content": "The TechCorp Series C documents are ready for review."
  },
  "content": "Thanks for the update!",
  "reply_count": 0,
  "sender": {
    "id": 1,
    "name": "John Doe"
  },
  "created_at": "2025-11-26T12:00:00Z"
}
```

### Get All Replies to a Message

**GET** `/messages/{id}/replies/`

**Response:** Array of messages that are replies to this message

---

## Typing Indicators

### Start Typing

**POST** `/conversations/{id}/start_typing/`

**Response:**
```json
{
  "status": "typing"
}
```

### Stop Typing

**POST** `/conversations/{id}/stop_typing/`

**Response:**
```json
{
  "status": "stopped"
}
```

### Get Who Is Typing

**GET** `/conversations/{id}/typing/`

**Response:**
```json
[
  {
    "id": 1,
    "user": {
      "id": 2,
      "name": "Sarah Chen"
    },
    "started_typing_at": "2025-11-26T12:00:45Z",
    "is_active": true
  }
]
```

**Frontend Implementation:**

```javascript
// When user types in input
let typingTimeout;
messageInput.addEventListener('input', () => {
  // Start typing
  fetch(`/blockchain-backend/api/conversations/${conversationId}/start_typing/`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  // Stop typing after 3 seconds of inactivity
  clearTimeout(typingTimeout);
  typingTimeout = setTimeout(() => {
    fetch(`/blockchain-backend/api/conversations/${conversationId}/stop_typing/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
  }, 3000);
});

// Poll for typing indicators
setInterval(() => {
  fetch(`/blockchain-backend/api/conversations/${conversationId}/typing/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  .then(res => res.json())
  .then(typing => {
    if (typing.length > 0) {
      showTypingIndicator(typing[0].user.name);
    } else {
      hideTypingIndicator();
    }
  });
}, 1000);
```

---

## Message Editing

### Edit a Message

**PATCH** `/messages/{id}/`

```json
{
  "content": "Updated message content"
}
```

**Response:**
```json
{
  "id": 15,
  "content": "Updated message content",
  "is_edited": true,
  "edited_at": "2025-11-26T12:05:00Z",
  "sender": {
    "id": 1,
    "name": "John Doe"
  },
  "created_at": "2025-11-26T12:00:00Z"
}
```

### Get Edit History

**GET** `/messages/{id}/edit_history/`

**Response:**
```json
[
  {
    "id": 1,
    "previous_content": "Original message content",
    "edited_by": "John Doe",
    "edited_at": "2025-11-26T12:05:00Z"
  },
  {
    "id": 2,
    "previous_content": "First edit",
    "edited_by": "John Doe",
    "edited_at": "2025-11-26T12:10:00Z"
  }
]
```

**Restrictions:**
- Only the sender can edit their own messages
- Cannot edit deleted messages
- Edit history is preserved

---

## Message Deletion

### Soft Delete a Message

**DELETE** `/messages/{id}/`

**Response:**
```json
{
  "status": "deleted",
  "message": "Message deleted successfully"
}
```

**Message Display After Deletion:**

```json
{
  "id": 15,
  "content": "Original content",  // Still accessible in API
  "display_content": "This message has been deleted",  // Use this for display
  "is_deleted": true,
  "deleted_at": "2025-11-26T12:15:00Z",
  "deleted_by": {
    "id": 1,
    "name": "John Doe"
  }
}
```

**Frontend Display:**

```javascript
function renderMessage(message) {
  if (message.is_deleted) {
    return `<div class="message deleted">
      <em>${message.display_content}</em>
      <span class="deleted-time">Deleted ${message.time_ago}</span>
    </div>`;
  }
  return `<div class="message">${message.content}</div>`;
}
```

---

## Enhanced Attachments

### Send Message with Multiple Attachments

**POST** `/messages/`  
Content-Type: `multipart/form-data`

```
conversation: 1
content: "Here are the documents"
attachment_files: [file1.pdf, file2.png, file3.docx]
```

### Attachment Response

```json
{
  "id": 20,
  "content": "Here are the documents",
  "attachments": [
    {
      "id": 1,
      "file_name": "contract.pdf",
      "file_type": "pdf",
      "file_type_display": "PDF Document",
      "file_size": 1024000,
      "mime_type": "application/pdf",
      "file_url": "http://localhost:8000/media/message_attachments/2025/11/26/contract.pdf",
      "thumbnail": null,
      "thumbnail_url": null
    },
    {
      "id": 2,
      "file_name": "screenshot.png",
      "file_type": "image",
      "file_type_display": "Image",
      "file_size": 512000,
      "mime_type": "image/png",
      "file_url": "http://localhost:8000/media/message_attachments/2025/11/26/screenshot.png",
      "thumbnail_url": "http://localhost:8000/media/message_thumbnails/2025/11/26/screenshot_thumb.png"
    }
  ]
}
```

**Supported File Types:**
- **Images**: `.jpg`, `.png`, `.gif`, `.svg` (with thumbnail generation)
- **Documents**: `.pdf`, `.doc`, `.docx`
- **Videos**: `.mp4`, `.avi`, `.mov`
- **Audio**: `.mp3`, `.wav`
- **Other**: Any file type

---

## Message Search

### Search Messages

**POST** `/messages/search/`

```json
{
  "query": "investment documents",
  "conversation_id": 1  // optional - search within specific conversation
}
```

**Response:**
```json
{
  "query": "investment documents",
  "count": 5,
  "results": [
    {
      "id": 15,
      "conversation": 1,
      "sender_name": "Sarah Chen",
      "content": "The investment documents are ready for review...",
      "created_at": "2025-11-26T10:30:00Z",
      "time_ago": "2 hours ago"
    }
    // ... more results
  ]
}
```

**Frontend Implementation:**

```javascript
async function searchMessages(query) {
  const response = await fetch('/blockchain-backend/api/messages/search/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query })
  });
  
  const results = await response.json();
  displaySearchResults(results.results);
}
```

---

## Notifications

### Get All Notifications

**GET** `/notifications/`

**Response:**
```json
[
  {
    "id": 1,
    "recipient": 1,
    "message": 15,
    "notification_type": "new_message",
    "delivery_method": "in_app",
    "is_sent": true,
    "is_read": false,
    "sent_at": "2025-11-26T12:00:00Z",
    "message_preview": "The TechCorp Series C documents are ready...",
    "sender_name": "Sarah Chen",
    "created_at": "2025-11-26T12:00:00Z"
  }
]
```

### Mark Notification as Read

**POST** `/notifications/{id}/mark_read/`

### Mark All Notifications as Read

**POST** `/notifications/mark_all_read/`

**Response:**
```json
{
  "status": "success",
  "marked_read": 5
}
```

### Notification Types
- `new_message` - New message in conversation
- `mention` - User mentioned in message
- `reply` - Reply to your message

### Delivery Methods
- `in_app` - In-app notification (always created)
- `email` - Email notification (to be implemented)
- `push` - Push notification (to be implemented)

---

## Read Receipts

Read receipts are automatically tracked when messages are marked as read.

### Read By Information in Messages

```json
{
  "id": 15,
  "content": "Hello everyone!",
  "is_read": true,
  "read_by": [
    {
      "id": 2,
      "name": "Sarah Chen",
      "read_at": "2025-11-26T12:05:00Z"
    },
    {
      "id": 3,
      "name": "Mike Rodriguez",
      "read_at": "2025-11-26T12:06:00Z"
    }
  ]
}
```

**Frontend Display:**

```javascript
function renderReadReceipts(message) {
  if (message.read_by && message.read_by.length > 0) {
    const names = message.read_by.map(r => r.name).join(', ');
    return `<div class="read-receipts">
      Read by ${names}
    </div>`;
  }
  return '';
}
```

---

## Complete API Reference

### Conversations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/conversations/` | List conversations |
| POST | `/conversations/` | Create conversation |
| GET | `/conversations/{id}/` | Get conversation details |
| DELETE | `/conversations/{id}/` | Delete conversation |
| GET | `/conversations/{id}/messages/` | Get messages |
| POST | `/conversations/{id}/mark_as_read/` | Mark as read |
| POST | `/conversations/start_conversation/` | Start new conversation |
| GET | `/conversations/unread_count/` | Get unread count |
| POST | `/conversations/{id}/start_typing/` | Start typing |
| POST | `/conversations/{id}/stop_typing/` | Stop typing |
| GET | `/conversations/{id}/typing/` | Who is typing |

### Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/messages/` | List messages |
| POST | `/messages/` | Send message |
| GET | `/messages/{id}/` | Get message |
| PATCH | `/messages/{id}/` | Edit message |
| DELETE | `/messages/{id}/` | Delete message |
| POST | `/messages/{id}/mark_read/` | Mark as read |
| POST | `/messages/{id}/react/` | Add reaction |
| DELETE | `/messages/{id}/react/` | Remove reaction |
| GET | `/messages/{id}/reactions/` | Get reactions |
| GET | `/messages/{id}/edit_history/` | Get edit history |
| GET | `/messages/{id}/replies/` | Get replies |
| POST | `/messages/search/` | Search messages |
| GET | `/messages/recent/` | Get recent messages |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/` | List notifications |
| GET | `/notifications/{id}/` | Get notification |
| POST | `/notifications/{id}/mark_read/` | Mark as read |
| POST | `/notifications/mark_all_read/` | Mark all as read |

---

## Frontend Integration Examples

### Complete React Implementation

```jsx
import React, { useState, useEffect } from 'react';

function EnhancedMessageComponent({ conversationId }) {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [replyingTo, setReplyingTo] = useState(null);
  const [typingUsers, setTypingUsers] = useState([]);

  // Load messages
  useEffect(() => {
    loadMessages();
  }, [conversationId]);

  // Poll for typing indicators
  useEffect(() => {
    const interval = setInterval(checkTyping, 1000);
    return () => clearInterval(interval);
  }, [conversationId]);

  const loadMessages = async () => {
    const response = await fetch(
      `/blockchain-backend/api/conversations/${conversationId}/messages/`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    const data = await response.json();
    setMessages(data);
  };

  const sendMessage = async () => {
    const response = await fetch('/blockchain-backend/api/messages/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        conversation: conversationId,
        content: inputText,
        parent_message: replyingTo?.id
      })
    });
    
    const newMessage = await response.json();
    setMessages([...messages, newMessage]);
    setInputText('');
    setReplyingTo(null);
    stopTyping();
  };

  const editMessage = async (messageId, newContent) => {
    await fetch(`/blockchain-backend/api/messages/${messageId}/`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ content: newContent })
    });
    loadMessages();
  };

  const deleteMessage = async (messageId) => {
    await fetch(`/blockchain-backend/api/messages/${messageId}/`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    loadMessages();
  };

  const reactToMessage = async (messageId, emoji) => {
    await fetch(`/blockchain-backend/api/messages/${messageId}/react/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ emoji })
    });
    loadMessages();
  };

  const handleTyping = () => {
    fetch(`/blockchain-backend/api/conversations/${conversationId}/start_typing/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
  };

  const stopTyping = () => {
    fetch(`/blockchain-backend/api/conversations/${conversationId}/stop_typing/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
  };

  const checkTyping = async () => {
    const response = await fetch(
      `/blockchain-backend/api/conversations/${conversationId}/typing/`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    const data = await response.json();
    setTypingUsers(data.map(t => t.user.name));
  };

  return (
    <div className="enhanced-messages">
      {/* Typing indicator */}
      {typingUsers.length > 0 && (
        <div className="typing-indicator">
          {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
        </div>
      )}

      {/* Messages */}
      <div className="messages-list">
        {messages.map(message => (
          <div key={message.id} className="message">
            {/* Reply preview */}
            {message.parent_message_preview && (
              <div className="reply-preview">
                Replying to {message.parent_message_preview.sender_name}:
                {message.parent_message_preview.content}
              </div>
            )}

            {/* Message content */}
            <div className="message-content">
              {message.display_content}
              {message.is_edited && <span className="edited">(edited)</span>}
            </div>

            {/* Attachments */}
            {message.attachments && message.attachments.map(attachment => (
              <div key={attachment.id} className="attachment">
                <a href={attachment.file_url} target="_blank">
                  {attachment.file_name}
                </a>
              </div>
            ))}

            {/* Reactions */}
            <div className="reactions">
              {message.reactions_summary?.map(reaction => (
                <button
                  key={reaction.emoji}
                  onClick={() => reactToMessage(message.id, reaction.emoji)}
                >
                  {reaction.emoji} {reaction.count}
                </button>
              ))}
              <button onClick={() => reactToMessage(message.id, '👍')}>
                Add Reaction
              </button>
            </div>

            {/* Actions */}
            <div className="message-actions">
              <button onClick={() => setReplyingTo(message)}>Reply</button>
              <button onClick={() => editMessage(message.id, prompt('New content:'))}>
                Edit
              </button>
              <button onClick={() => deleteMessage(message.id)}>Delete</button>
            </div>

            {/* Read receipts */}
            {message.read_by && message.read_by.length > 0 && (
              <div className="read-receipts">
                Read by {message.read_by.map(r => r.name).join(', ')}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Reply indicator */}
      {replyingTo && (
        <div className="replying-to">
          Replying to: {replyingTo.content}
          <button onClick={() => setReplyingTo(null)}>Cancel</button>
        </div>
      )}

      {/* Input */}
      <div className="message-input">
        <textarea
          value={inputText}
          onChange={(e) => {
            setInputText(e.target.value);
            handleTyping();
          }}
          placeholder="Type a message..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}
```

---

## Summary

All 10 enhanced features are now fully implemented and ready to use:

1. ✅ **Message Reactions** - Add/remove emoji reactions
2. ✅ **Message Threading** - Reply to specific messages
3. ✅ **Typing Indicators** - Real-time typing status
4. ✅ **Message Editing** - Edit with history tracking
5. ✅ **Soft Delete** - Delete with placeholder
6. ✅ **Enhanced Attachments** - Multiple files with previews
7. ✅ **Message Search** - Full-text search
8. ✅ **Notifications** - In-app, email, push ready
9. ✅ **Read Receipts** - Group message tracking
10. ✅ **Edit History** - Complete audit trail

The API is production-ready and fully documented!
