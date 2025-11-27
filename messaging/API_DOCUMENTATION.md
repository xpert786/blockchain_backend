# Messages API Documentation

This document provides comprehensive documentation for the Messages API endpoints for the Investor Portal.

## Overview

The Messages API allows investors to communicate with syndicate leads, support teams, and other relevant parties. It provides endpoints for managing conversations and sending/receiving messages.

## Base URL

All endpoints are prefixed with: `/blockchain-backend/api/`

## Authentication

All endpoints require JWT authentication. Include the access token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

---

## Endpoints

### 1. List All Conversations

**GET** `/conversations/`

Get all conversations for the authenticated user.

**Query Parameters:**
- `search` (optional): Search conversations by subject or participant name

**Response:**
```json
[
  {
    "id": 1,
    "subject": "TechCorp Series C Investment",
    "is_group_conversation": false,
    "participants": [
      {
        "id": 2,
        "username": "sarah.chen",
        "email": "sarah@example.com",
        "name": "Sarah Chen",
        "first_name": "Sarah",
        "last_name": "Chen",
        "role": "syndicate"
      }
    ],
    "other_participant": {
      "id": 2,
      "username": "sarah.chen",
      "email": "sarah@example.com",
      "name": "Sarah Chen",
      "first_name": "Sarah",
      "last_name": "Chen",
      "role": "syndicate"
    },
    "participant_info": {
      "name": "Sarah Chen",
      "role": "syndicate",
      "initials": "SC"
    },
    "last_message": {
      "id": 15,
      "content": "The TechCorp Series C documents are ready for review.",
      "sender": "Sarah Chen",
      "sender_id": 2,
      "created_at": "2025-11-26T10:30:00Z",
      "time_ago": "2 hours ago"
    },
    "unread_count": 3,
    "status": "Online",
    "created_at": "2025-11-20T09:00:00Z",
    "updated_at": "2025-11-26T10:30:00Z"
  }
]
```

---

### 2. Get Conversation Details

**GET** `/conversations/{id}/`

Get detailed information about a specific conversation including all messages.

**Response:**
```json
{
  "id": 1,
  "subject": "TechCorp Series C Investment",
  "is_group_conversation": false,
  "participants": [
    {
      "id": 1,
      "username": "john.doe",
      "email": "john@example.com",
      "name": "John Doe",
      "role": "investor"
    },
    {
      "id": 2,
      "username": "sarah.chen",
      "email": "sarah@example.com",
      "name": "Sarah Chen",
      "role": "syndicate"
    }
  ],
  "messages": [
    {
      "id": 14,
      "conversation": 1,
      "sender": {
        "id": 1,
        "username": "john.doe",
        "email": "john@example.com",
        "name": "John Doe",
        "role": "investor"
      },
      "sender_name": "John Doe",
      "content": "Hi, I wanted to update you on the TechCorp Series C investment.",
      "attachment": null,
      "attachment_name": null,
      "is_read": true,
      "read_at": "2025-11-26T10:15:00Z",
      "created_at": "2025-11-26T10:00:00Z",
      "updated_at": "2025-11-26T10:00:00Z",
      "time_ago": "2 hours ago"
    },
    {
      "id": 15,
      "conversation": 1,
      "sender": {
        "id": 2,
        "username": "sarah.chen",
        "email": "sarah@example.com",
        "name": "Sarah Chen",
        "role": "syndicate"
      },
      "sender_name": "Sarah Chen",
      "content": "The investment is complete and we're ready to move forward.",
      "attachment": null,
      "attachment_name": null,
      "is_read": false,
      "read_at": null,
      "created_at": "2025-11-26T10:30:00Z",
      "updated_at": "2025-11-26T10:30:00Z",
      "time_ago": "2 hours ago"
    }
  ],
  "unread_count": 1,
  "created_at": "2025-11-20T09:00:00Z",
  "updated_at": "2025-11-26T10:30:00Z"
}
```

---

### 3. Start a New Conversation

**POST** `/conversations/start_conversation/`

Start a new conversation with one or more users.

**Request Body:**
```json
{
  "participant_id": 2,  // For 1-on-1 conversation
  "initial_message": "Hello! I have a question about the investment.",
  "subject": "Investment Question"
}
```

OR for group conversation:
```json
{
  "participant_ids": [2, 3, 4],  // For group conversation
  "initial_message": "Hello everyone!",
  "subject": "Group Discussion",
  "is_group_conversation": true
}
```

**Response:** Returns the created conversation with details (same format as GET conversation detail)

**Status Codes:**
- `201 Created`: Conversation created successfully
- `200 OK`: Existing conversation returned (for 1-on-1)
- `400 Bad Request`: Missing required fields

---

### 4. Create Conversation (Alternative Method)

**POST** `/conversations/`

Create a new conversation directly.

**Request Body:**
```json
{
  "subject": "Investment Question",
  "participant_ids": [2],
  "initial_message": "Hello!",
  "is_group_conversation": false
}
```

**Response:** Same as conversation detail

---

### 5. Get Messages in Conversation

**GET** `/conversations/{id}/messages/`

Get all messages in a specific conversation.

**Response:** Array of message objects (see message format above)

---

### 6. Mark Conversation as Read

**POST** `/conversations/{id}/mark_as_read/`

Mark all unread messages in a conversation as read for the current user.

**Response:**
```json
{
  "status": "success",
  "marked_read": 3
}
```

---

### 7. Get Total Unread Count

**GET** `/conversations/unread_count/`

Get the total number of unread messages across all conversations.

**Response:**
```json
{
  "unread_count": 5
}
```

---

### 8. Send a Message

**POST** `/messages/`

Send a new message in an existing conversation.

**Request Body:**
```json
{
  "conversation": 1,
  "content": "Thank you for the update!"
}
```

**With Attachment:**
```json
{
  "conversation": 1,
  "content": "Here's the document you requested",
  "attachment": "<file_upload>"
}
```

**Response:**
```json
{
  "id": 16,
  "conversation": 1,
  "sender": {
    "id": 1,
    "username": "john.doe",
    "email": "john@example.com",
    "name": "John Doe",
    "role": "investor"
  },
  "sender_name": "John Doe",
  "content": "Thank you for the update!",
  "attachment": null,
  "attachment_name": null,
  "is_read": false,
  "read_at": null,
  "created_at": "2025-11-26T12:00:00Z",
  "updated_at": "2025-11-26T12:00:00Z",
  "time_ago": "just now"
}
```

---

### 9. Mark Message as Read

**POST** `/messages/{id}/mark_read/`

Mark a specific message as read.

**Response:**
```json
{
  "status": "success",
  "message_id": 15,
  "is_read": true
}
```

---

### 10. Get Recent Messages

**GET** `/messages/recent/`

Get the 50 most recent messages for the current user across all conversations.

**Response:** Array of message objects

---

### 11. Delete Conversation

**DELETE** `/conversations/{id}/`

Delete a conversation.

**Response:** `204 No Content`

---

### 12. Delete Message

**DELETE** `/messages/{id}/`

Delete a specific message.

**Response:** `204 No Content`

---

## Frontend Integration Guide

### 1. Display Conversations List

```javascript
// Fetch conversations
fetch('/blockchain-backend/api/conversations/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
})
.then(res => res.json())
.then(conversations => {
  // Display conversations with:
  // - participant_info.name
  // - participant_info.initials (for avatar)
  // - last_message.content
  // - last_message.time_ago
  // - unread_count (show badge if > 0)
  // - status (Online/Offline indicator)
});
```

### 2. Load Conversation Messages

```javascript
// Fetch conversation detail
fetch(`/blockchain-backend/api/conversations/${conversationId}/`, {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
})
.then(res => res.json())
.then(conversation => {
  // Display messages in chat interface
  // Mark conversation as read when opened
  markAsRead(conversationId);
});
```

### 3. Send a Message

```javascript
// Send message
fetch('/blockchain-backend/api/messages/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    conversation: conversationId,
    content: messageText
  })
})
.then(res => res.json())
.then(message => {
  // Add message to UI
  // Update conversation list
});
```

### 4. Mark as Read

```javascript
// Mark conversation as read when opened
function markAsRead(conversationId) {
  fetch(`/blockchain-backend/api/conversations/${conversationId}/mark_as_read/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
}
```

### 5. Start New Conversation

```javascript
// Start conversation with syndicate lead
fetch('/blockchain-backend/api/conversations/start_conversation/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    participant_id: syndicateLeadId,
    initial_message: "Hello, I have a question about...",
    subject: "Investment Question"
  })
})
.then(res => res.json())
.then(conversation => {
  // Navigate to conversation
  openConversation(conversation.id);
});
```

### 6. Search Conversations

```javascript
// Search conversations
fetch(`/blockchain-backend/api/conversations/?search=${searchQuery}`, {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
})
.then(res => res.json())
.then(results => {
  // Display filtered conversations
});
```

### 7. Real-time Updates (WebSocket - Optional Enhancement)

For real-time messaging, consider implementing WebSocket support using Django Channels in the future. The current REST API works well with polling:

```javascript
// Poll for new messages every 5 seconds
setInterval(() => {
  fetch('/blockchain-backend/api/conversations/unread_count/', {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  })
  .then(res => res.json())
  .then(data => {
    updateUnreadBadge(data.unread_count);
  });
}, 5000);
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Successful GET request
- `201 Created`: Successful POST request (resource created)
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: User doesn't have permission
- `404 Not Found`: Resource doesn't exist
- `500 Internal Server Error`: Server error

Error responses include a message:
```json
{
  "error": "Error message description"
}
```

---

## Database Migrations

After implementing this API, run migrations:

```bash
python manage.py makemigrations messaging
python manage.py migrate
```

---

## Testing

Use the Django admin interface to:
1. View all conversations
2. View all messages
3. Manually create test data

Admin URL: `/blockchain-backend/admin/messaging/`

---

## Future Enhancements

1. **WebSocket Support**: Real-time message delivery using Django Channels
2. **Message Reactions**: Allow users to react to messages with emojis
3. **Message Threading**: Reply to specific messages
4. **File Attachments**: Enhanced file upload with previews
5. **Message Search**: Full-text search across all messages
6. **Notifications**: Email/push notifications for new messages
7. **Typing Indicators**: Show when other users are typing
8. **Message Editing**: Allow users to edit sent messages
9. **Message Deletion**: Soft delete with "Message deleted" placeholder
10. **Read Receipts**: Show which users have read messages in group chats
