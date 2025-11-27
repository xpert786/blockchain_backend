# Messaging System - Quick Start Guide

## Overview

The Messaging System provides a complete API for investor-syndicate communication. It supports:
- ✅ 1-on-1 conversations between investors and syndicate leads
- ✅ Group conversations
- ✅ Real-time message tracking
- ✅ Unread message counters
- ✅ Message read receipts
- ✅ File attachments
- ✅ Search functionality

## Quick Start

### 1. Installation Complete ✅

The app has been installed and migrations have been run. The database tables are ready.

### 2. Main Endpoints

**Base URL:** `/blockchain-backend/api/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/conversations/` | List all conversations |
| GET | `/conversations/{id}/` | Get conversation details |
| POST | `/conversations/start_conversation/` | Start new conversation |
| GET | `/conversations/{id}/messages/` | Get messages |
| POST | `/conversations/{id}/mark_as_read/` | Mark as read |
| GET | `/conversations/unread_count/` | Get unread count |
| POST | `/messages/` | Send a message |

### 3. Frontend Integration Examples

#### List Conversations
```javascript
const response = await fetch('/blockchain-backend/api/conversations/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const conversations = await response.json();
```

#### Start Conversation with Syndicate Lead
```javascript
const response = await fetch('/blockchain-backend/api/conversations/start_conversation/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    participant_id: syndicateLeadId,
    initial_message: "Hello! I have a question about...",
    subject: "Investment Question"
  })
});
const conversation = await response.json();
```

#### Send Message
```javascript
const response = await fetch('/blockchain-backend/api/messages/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    conversation: conversationId,
    content: messageText
  })
});
const message = await response.json();
```

## Response Examples

### Conversation List Response
```json
[
  {
    "id": 1,
    "participant_info": {
      "name": "Sarah Chen",
      "role": "syndicate",
      "initials": "SC"
    },
    "last_message": {
      "content": "The TechCorp Series C documents are ready for review.",
      "time_ago": "2 hours ago"
    },
    "unread_count": 3,
    "status": "Online"
  }
]
```

### Message Response
```json
{
  "id": 15,
  "sender_name": "Sarah Chen",
  "content": "The investment is complete and we're ready to move forward.",
  "created_at": "2025-11-26T10:30:00Z",
  "time_ago": "2 hours ago",
  "is_read": false
}
```

## UI Components Needed

Based on the Figma design, you'll need:

1. **Conversations Sidebar**
   - List of conversations with avatars (use `participant_info.initials`)
   - Last message preview
   - Timestamp (`last_message.time_ago`)
   - Unread badge (`unread_count`)
   - Online/offline status indicator

2. **Message Thread**
   - Message bubbles (different styles for sent/received)
   - Sender name and timestamp
   - Read status indicators

3. **Message Input**
   - Text area for message composition
   - Send button
   - File attachment button (optional)

4. **Search Bar**
   - Filter conversations by participant name or subject

## Admin Interface

Access the admin panel at:
`http://localhost:8000/blockchain-backend/admin/messaging/`

You can:
- View all conversations
- View all messages
- Create test data
- Monitor message activity

## Testing the API

Use these curl commands to test:

```bash
# Get conversations
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/blockchain-backend/api/conversations/

# Start conversation
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"participant_id": 2, "initial_message": "Hello!", "subject": "Test"}' \
  http://localhost:8000/blockchain-backend/api/conversations/start_conversation/

# Send message
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conversation": 1, "content": "Hello!"}' \
  http://localhost:8000/blockchain-backend/api/messages/

# Get unread count
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/blockchain-backend/api/conversations/unread_count/
```

## Files Created

```
messaging/
├── __init__.py
├── admin.py              # Admin interface configuration
├── apps.py               # App configuration
├── models.py             # Conversation, Message, MessageReadReceipt models
├── serializers.py        # API serializers
├── views.py              # API viewsets and endpoints
├── urls.py               # URL routing
├── tests.py              # Unit tests (to be implemented)
├── API_DOCUMENTATION.md  # Comprehensive API documentation
├── README.md             # This file
└── migrations/
    └── 0001_initial.py   # Initial database schema
```

## Next Steps

1. **Test the Endpoints**: Use Postman or curl to test the API
2. **Integrate with Frontend**: Use the JavaScript examples above
3. **Add Real-time Updates**: Consider implementing polling or WebSockets
4. **Enhance UI**: Add features like typing indicators, message reactions, etc.

## Support

For detailed API documentation, see `API_DOCUMENTATION.md` in this directory.

For questions or issues, contact the development team.
