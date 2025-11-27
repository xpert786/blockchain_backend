# Transfers & Requests API Documentation

## Overview

The Transfers & Requests system manages ownership transfers and general approval workflows for investments. It provides complete transfer lifecycle management with document handling, multi-party approvals, and request tracking.

## Key Features

- ✅ Transfer ownership management with approval workflow
- ✅ General request & approval system for various operations
- ✅ Document upload for both transfers and requests
- ✅ Status tracking (Pending → Approved → Completed or Rejected)
- ✅ Priority-based request management
- ✅ Transfer fee calculation
- ✅ Statistics and analytics
- ✅ Admin approval/rejection workflows
- ✅ Document download functionality

---

## Data Models

### 1. Transfer Model

**Purpose:** Manages SPV share ownership transfers between users

**Fields:**
- `transfer_id` - Auto-generated ID (e.g., "TXN-A2B3C4")
- `requester` - User requesting the transfer
- `recipient` - User receiving the transfer
- `spv` - Associated SPV
- `shares` - Number of shares to transfer
- `amount` - Transfer amount
- `transfer_fee` - Transfer fee
- `net_amount` - Net amount after fees (auto-calculated)
- `status` - pending_approval, approved, completed, rejected
- `rejection_reason` - Reason if rejected
- `rejection_notes` - Additional rejection notes
- `rejected_by` - Admin who rejected
- `rejected_at` - Rejection timestamp
- `approved_by` - Admin who approved
- `approved_at` - Approval timestamp
- `completed_at` - Completion timestamp
- `description` - Transfer description
- `investor_name` - Investor name (if different)
- `requested_at` - Creation timestamp

**Properties:**
- `is_urgent` - True if pending > 7 days

### 2. TransferDocument Model

**Fields:**
- `transfer` - Reference to Transfer
- `file` - Uploaded document file
- `original_filename` - Original file name
- `file_size` - Size in bytes
- `mime_type` - File MIME type
- `uploaded_by` - User who uploaded
- `uploaded_at` - Upload timestamp

### 3. Request Model

**Purpose:** General approval request system for various operations

**Fields:**
- `request_id` - Auto-generated ID (e.g., "SPV-A2B3C4")
- `request_type` - spv_update, contact_update, document_approval, kyc_update, investment_change, transfer_approval, other
- `title` - Request title
- `description` - Detailed description
- `priority` - low, medium, high, urgent
- `requester` - User who submitted request
- `related_entity` - Related entity reference (e.g., "SPV-001")
- `spv` - Related SPV (optional)
- `status` - pending, approved, rejected
- `approved_by` - Admin who approved
- `approved_at` - Approval timestamp
- `approval_notes` - Approval notes
- `rejected_by` - Admin who rejected
- `rejected_at` - Rejection timestamp
- `rejection_reason` - Rejection reason
- `created_at` - Creation timestamp
- `due_date` - Optional due date

**Properties:**
- `is_overdue` - True if past due date
- `is_urgent_priority` - True if priority is high/urgent

### 4. RequestDocument Model

**Fields:**
- `request` - Reference to Request
- `file` - Uploaded document file
- `original_filename` - Original file name
- `file_size` - Size in bytes
- `mime_type` - File MIME type
- `uploaded_by` - User who uploaded
- `uploaded_at` - Upload timestamp

---

## API Endpoints

## TRANSFERS

### 1. List All Transfers
```http
GET /blockchain-backend/api/transfers/
```

**Query Parameters:**
- `status` - Filter by status (pending_approval, approved, completed, rejected)
- `spv` - Filter by SPV ID
- `search` - Search in transfer_id, usernames, emails, SPV name, description

**Response:**
```json
[
  {
    "id": 1,
    "transfer_id": "TXN-001",
    "requester": 1,
    "requester_detail": {
      "id": 1,
      "username": "alice",
      "email": "alice@email.com",
      "full_name": "Alice Investor"
    },
    "recipient": 2,
    "recipient_detail": {
      "id": 2,
      "username": "bob",
      "email": "bob@email.com",
      "full_name": "Bob Smith"
    },
    "spv": 1,
    "spv_detail": {
      "id": 1,
      "display_name": "SPV-001",
      "status": "active"
    },
    "shares": 125,
    "amount": "50000.00",
    "transfer_fee": "250.00",
    "net_amount": "49750.00",
    "status": "pending_approval",
    "investor_name": "Michael Investor",
    "requested_at": "2024-03-15T14:00:00Z",
    "documents_count": 2,
    "is_urgent": false
  }
]
```

### 2. Create Transfer
```http
POST /blockchain-backend/api/transfers/
```

**Request Body:**
```json
{
  "recipient": 2,
  "spv": 1,
  "shares": 125,
  "amount": "50000.00",
  "transfer_fee": "250.00",
  "description": "Request to transfer tokens to external wallet for liquidity purposes",
  "investor_name": "Michael Investor"
}
```

**Response:** (201 Created)
```json
{
  "id": 1,
  "transfer_id": "TXN-A2B3C4",
  "status": "pending_approval",
  "net_amount": "49750.00",
  "requester_detail": {...},
  "recipient_detail": {...},
  "requested_at": "2024-03-15T14:00:00Z"
}
```

### 3. Get Transfer Details
```http
GET /blockchain-backend/api/transfers/{id}/
```

**Response:**
```json
{
  "id": 1,
  "transfer_id": "TXN-001",
  "requester": 1,
  "requester_detail": {
    "id": 1,
    "username": "alice",
    "email": "alice@email.com",
    "full_name": "Alice Investor"
  },
  "recipient": 2,
  "recipient_detail": {
    "id": 2,
    "username": "bob",
    "email": "bob@email.com",
    "full_name": "Bob Smith"
  },
  "spv": 1,
  "spv_detail": {
    "id": 1,
    "display_name": "Tech Startup Fund Q4",
    "status": "active"
  },
  "shares": 125,
  "amount": "50000.00",
  "transfer_fee": "250.00",
  "net_amount": "49750.00",
  "status": "pending_approval",
  "rejection_reason": null,
  "rejection_notes": null,
  "rejected_by": null,
  "rejected_by_detail": null,
  "rejected_at": null,
  "approved_by": null,
  "approved_by_detail": null,
  "approved_at": null,
  "completed_at": null,
  "description": "Request to transfer tokens",
  "investor_name": "Michael Investor",
  "documents": [
    {
      "id": 1,
      "file": "/media/transfers/1/documents/document.pdf",
      "original_filename": "Transfer Request Form.pdf",
      "file_size": 524288,
      "file_size_mb": 0.5,
      "mime_type": "application/pdf",
      "uploaded_by_detail": {
        "id": 1,
        "username": "alice",
        "email": "alice@email.com"
      },
      "uploaded_at": "2024-03-15T14:30:00Z"
    }
  ],
  "documents_count": 1,
  "is_urgent": false,
  "requested_at": "2024-03-15T14:00:00Z",
  "updated_at": "2024-03-15T14:30:00Z"
}
```

### 4. Get Transfer Statistics
```http
GET /blockchain-backend/api/transfers/statistics/
```

**Response:**
```json
{
  "total_transfers": 4,
  "pending_approval": 1,
  "completed": 1,
  "rejected": 1,
  "approved": 1,
  "transfer_volume": "250000.00",
  "urgent_count": 0
}
```

### 5. Approve Transfer (Admin Only)
```http
POST /blockchain-backend/api/transfers/{id}/approve/
```

**Response:**
```json
{
  "message": "Transfer approved successfully",
  "data": {
    "id": 1,
    "status": "approved",
    "approved_by": 3,
    "approved_by_detail": {
      "id": 3,
      "username": "admin",
      "email": "admin@example.com"
    },
    "approved_at": "2024-03-15T15:00:00Z"
  }
}
```

### 6. Reject Transfer (Admin Only)
```http
POST /blockchain-backend/api/transfers/{id}/reject/
```

**Request Body:**
```json
{
  "rejection_reason": "recipient_not_verified",
  "rejection_notes": "Recipient KYC is not verified"
}
```

**Valid Rejection Reasons:**
- `recipient_not_verified` - Recipient is not a verified investor
- `insufficient_funds` - Insufficient funds
- `invalid_documents` - Invalid or missing documents
- `compliance_issue` - Compliance issue
- `other` - Other

**Response:**
```json
{
  "message": "Transfer rejected successfully",
  "data": {
    "id": 1,
    "status": "rejected",
    "rejection_reason": "recipient_not_verified",
    "rejection_notes": "Recipient KYC is not verified",
    "rejected_by": 3,
    "rejected_by_detail": {
      "id": 3,
      "username": "admin",
      "email": "admin@example.com"
    },
    "rejected_at": "2024-03-15T15:00:00Z"
  }
}
```

### 7. Complete Transfer (Admin Only)
```http
POST /blockchain-backend/api/transfers/{id}/complete/
```

**Note:** Transfer must be approved before completion.

**Response:**
```json
{
  "message": "Transfer completed successfully",
  "data": {
    "id": 1,
    "status": "completed",
    "completed_at": "2024-03-16T10:00:00Z"
  }
}
```

### 8. Add Document to Transfer
```http
POST /blockchain-backend/api/transfers/{id}/add_document/
Content-Type: multipart/form-data
```

**Request Body:**
```
file: <FILE>
```

**Response:**
```json
{
  "message": "Document added successfully",
  "data": {
    "id": 2,
    "transfer": 1,
    "file": "/media/transfers/1/documents/additional_doc.pdf",
    "original_filename": "additional_doc.pdf",
    "file_size": 1048576,
    "file_size_mb": 1.0,
    "uploaded_by_detail": {
      "id": 1,
      "username": "alice",
      "email": "alice@email.com"
    },
    "uploaded_at": "2024-03-15T16:00:00Z"
  }
}
```

### 9. Download Transfer Document
```http
GET /blockchain-backend/api/transfer-documents/{id}/download/
```

**Response:** File download with proper content-type

---

## REQUESTS & APPROVAL SYSTEM

### 10. List All Requests
```http
GET /blockchain-backend/api/requests/
```

**Query Parameters:**
- `status` - Filter by status (pending, approved, rejected)
- `priority` - Filter by priority (low, medium, high, urgent)
- `request_type` - Filter by type
- `spv` - Filter by SPV ID
- `search` - Search in request_id, title, description, related_entity

**Response:**
```json
[
  {
    "id": 1,
    "request_id": "SPV-A1B2C3",
    "request_type": "spv_update",
    "title": "Update SPV Investment Terms",
    "priority": "high",
    "requester": 1,
    "requester_detail": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      "full_name": "John Investor"
    },
    "related_entity": "SPV-001",
    "spv": 1,
    "spv_detail": {
      "id": 1,
      "display_name": "Tech Startup Fund Q4",
      "status": "active"
    },
    "status": "pending",
    "created_at": "2024-03-18T14:00:00Z",
    "due_date": "2024-03-25T00:00:00Z",
    "documents_count": 0,
    "is_overdue": false,
    "is_urgent_priority": true
  }
]
```

### 11. Create Request
```http
POST /blockchain-backend/api/requests/
```

**Request Body:**
```json
{
  "request_type": "spv_update",
  "title": "Update SPV Investment Terms",
  "description": "Request to increase maximum cap from $5M to $8M for Tech Startup Fund Q4",
  "priority": "high",
  "related_entity": "SPV-001",
  "spv": 1,
  "due_date": "2024-03-25T00:00:00Z"
}
```

**Request Types:**
- `spv_update` - Update SPV Investment Terms
- `contact_update` - Update Contact Information
- `document_approval` - Document Approval
- `kyc_update` - KYC Update
- `investment_change` - Investment Change
- `transfer_approval` - Transfer Approval
- `other` - Other

**Priority Levels:**
- `low` - Low priority
- `medium` - Medium priority
- `high` - High priority
- `urgent` - Urgent

**Response:** (201 Created)
```json
{
  "id": 1,
  "request_id": "SPV-A1B2C3",
  "request_type": "spv_update",
  "title": "Update SPV Investment Terms",
  "priority": "high",
  "status": "pending",
  "requester_detail": {...},
  "created_at": "2024-03-18T14:00:00Z"
}
```

### 12. Get Request Details
```http
GET /blockchain-backend/api/requests/{id}/
```

**Response:**
```json
{
  "id": 1,
  "request_id": "SPV-A1B2C3",
  "request_type": "spv_update",
  "title": "Update SPV Investment Terms",
  "description": "Request to increase maximum cap from $5M to $8M for Tech Startup Fund Q4",
  "priority": "high",
  "requester": 1,
  "requester_detail": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Investor"
  },
  "related_entity": "SPV-001",
  "spv": 1,
  "spv_detail": {
    "id": 1,
    "display_name": "Tech Startup Fund Q4",
    "status": "active"
  },
  "status": "pending",
  "approved_by": null,
  "approved_by_detail": null,
  "approved_at": null,
  "approval_notes": null,
  "rejected_by": null,
  "rejected_by_detail": null,
  "rejected_at": null,
  "rejection_reason": null,
  "documents": [],
  "documents_count": 0,
  "is_overdue": false,
  "is_urgent_priority": true,
  "created_at": "2024-03-18T14:00:00Z",
  "updated_at": "2024-03-18T14:00:00Z",
  "due_date": "2024-03-25T00:00:00Z"
}
```

### 13. Get Request Statistics
```http
GET /blockchain-backend/api/requests/statistics/
```

**Response:**
```json
{
  "total_requests": 6,
  "pending": 2,
  "approved_today": 3,
  "rejected": 2,
  "high_priority": 1,
  "overdue": 0
}
```

### 14. Approve Request (Admin Only)
```http
POST /blockchain-backend/api/requests/{id}/approve/
```

**Request Body (Optional):**
```json
{
  "approval_notes": "Approved with conditions"
}
```

**Response:**
```json
{
  "message": "Request approved successfully",
  "data": {
    "id": 1,
    "status": "approved",
    "approved_by": 3,
    "approved_by_detail": {
      "id": 3,
      "username": "admin",
      "email": "admin@example.com"
    },
    "approved_at": "2024-03-18T15:00:00Z",
    "approval_notes": "Approved with conditions"
  }
}
```

### 15. Reject Request (Admin Only)
```http
POST /blockchain-backend/api/requests/{id}/reject/
```

**Request Body:**
```json
{
  "rejection_reason": "Insufficient documentation provided"
}
```

**Response:**
```json
{
  "message": "Request rejected successfully",
  "data": {
    "id": 1,
    "status": "rejected",
    "rejected_by": 3,
    "rejected_by_detail": {
      "id": 3,
      "username": "admin",
      "email": "admin@example.com"
    },
    "rejected_at": "2024-03-18T15:00:00Z",
    "rejection_reason": "Insufficient documentation provided"
  }
}
```

### 16. Add Document to Request
```http
POST /blockchain-backend/api/requests/{id}/add_document/
Content-Type: multipart/form-data
```

**Request Body:**
```
file: <FILE>
```

**Response:**
```json
{
  "message": "Document added successfully",
  "data": {
    "id": 1,
    "request": 1,
    "file": "/media/requests/1/documents/support_doc.pdf",
    "original_filename": "support_doc.pdf",
    "file_size": 524288,
    "file_size_mb": 0.5,
    "uploaded_by_detail": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com"
    },
    "uploaded_at": "2024-03-18T14:30:00Z"
  }
}
```

### 17. Download Request Document
```http
GET /blockchain-backend/api/request-documents/{id}/download/
```

**Response:** File download with proper content-type

---

## Complete Workflow Flows

### Flow 1: Transfer Request & Approval

```
1. User creates transfer request
   POST /api/transfers/
   → Status: "pending_approval"
   → Transfer ID generated (e.g., TXN-001)

2. User uploads supporting documents
   POST /api/transfers/{id}/add_document/
   → Documents attached to transfer

3. Admin reviews transfer details
   GET /api/transfers/{id}/

4a. Admin approves transfer
    POST /api/transfers/{id}/approve/
    → Status: "approved"
    → approved_by, approved_at recorded

4b. OR Admin rejects transfer
    POST /api/transfers/{id}/reject/
    { "rejection_reason": "...", "rejection_notes": "..." }
    → Status: "rejected"
    → rejection_reason, rejected_by, rejected_at recorded

5. Admin marks transfer as completed (if approved)
   POST /api/transfers/{id}/complete/
   → Status: "completed"
   → completed_at recorded
```

### Flow 2: General Request & Approval

```
1. User creates request
   POST /api/requests/
   → Status: "pending"
   → Request ID generated based on type (e.g., SPV-001)
   → Priority assigned

2. User adds supporting documents (optional)
   POST /api/requests/{id}/add_document/

3. Admin views pending requests
   GET /api/requests/?status=pending&priority=high

4a. Admin approves request
    POST /api/requests/{id}/approve/
    { "approval_notes": "..." }
    → Status: "approved"

4b. OR Admin rejects request
    POST /api/requests/{id}/reject/
    { "rejection_reason": "..." }
    → Status: "rejected"
```

### Flow 3: Dashboard Statistics

```
1. Get transfer statistics
   GET /api/transfers/statistics/
   → Shows total, pending, completed, rejected, volume, urgent

2. Get request statistics
   GET /api/requests/statistics/
   → Shows total, pending, approved today, rejected, high priority, overdue
```

---

## Permission Model

### User Roles:
- **Admin/Staff**: Full access to all transfers and requests
- **Regular User**:
  - **Transfers**: Can view transfers where they are requester or recipient
  - **Requests**: Can only view their own requests

### Endpoint Permissions:
- ✅ All authenticated users can create transfers/requests
- ✅ Only requester/recipient can view transfer details
- ✅ Only requester can view request details
- ✅ Only admins can approve/reject/complete
- ✅ Requester and recipient can upload transfer documents
- ✅ Only requester can upload request documents

---

## Status Lifecycles

### Transfer Lifecycle:
```
pending_approval
  ↓
approved (admin action)
  ↓
completed (admin action)

OR

pending_approval
  ↓
rejected (admin action)
```

### Request Lifecycle:
```
pending
  ↓
approved (admin action)

OR

pending
  ↓
rejected (admin action)
```

---

## Frontend Integration Examples

### Create Transfer Request

```javascript
const response = await fetch('/blockchain-backend/api/transfers/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    recipient: 2,
    spv: 1,
    shares: 125,
    amount: "50000.00",
    transfer_fee: "250.00",
    description: "Transfer request",
    investor_name: "Michael Investor"
  })
});

const transfer = await response.json();
console.log('Transfer created:', transfer.transfer_id);
```

### Upload Transfer Document

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch(`/blockchain-backend/api/transfers/${transferId}/add_document/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});

const result = await response.json();
console.log('Document uploaded:', result.data.original_filename);
```

### Approve Transfer (Admin)

```javascript
const response = await fetch(`/blockchain-backend/api/transfers/${transferId}/approve/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const result = await response.json();
if (result.message === 'Transfer approved successfully') {
  alert('Transfer approved!');
}
```

### Create Request

```javascript
const response = await fetch('/blockchain-backend/api/requests/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    request_type: 'spv_update',
    title: 'Update SPV Investment Terms',
    description: 'Request to increase cap from $5M to $8M',
    priority: 'high',
    related_entity: 'SPV-001',
    spv: 1,
    due_date: '2024-03-25T00:00:00Z'
  })
});

const request = await response.json();
console.log('Request created:', request.request_id);
```

### Reject Request with Reason (Admin)

```javascript
const response = await fetch(`/blockchain-backend/api/requests/${requestId}/reject/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    rejection_reason: 'Insufficient documentation provided'
  })
});

const result = await response.json();
```

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": "Error message description"
}
```

**Common Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `403` - Forbidden (permission denied, admin-only action)
- `404` - Not Found
- `500` - Internal Server Error

---

## Database Relationships

```
Transfer
  ├── requester (User)
  ├── recipient (User)
  ├── spv (SPV)
  ├── approved_by (User) [optional]
  ├── rejected_by (User) [optional]
  └── documents (TransferDocument) [multiple]

TransferDocument
  ├── transfer (Transfer)
  └── uploaded_by (User)

Request
  ├── requester (User)
  ├── spv (SPV) [optional]
  ├── approved_by (User) [optional]
  ├── rejected_by (User) [optional]
  └── documents (RequestDocument) [multiple]

RequestDocument
  ├── request (Request)
  └── uploaded_by (User)
```

---

## UI Components from Figma

### Transfer Management Screen:
- **Stats Cards**: Total Transfers, Pending Approval, Completed, Transfer Volume
- **Tabs**: All Transfers, Approved, Pending, Completed, Rejected
- **Transfer Card**: Shows transfer ID, participants, SPV, shares, fees, status badge
- **Actions**: Approve Transfer, Reject, Review Details buttons

### Transfer Details Modal:
- Transfer ID, participants with avatars
- SPV details
- Amount breakdown (shares, transfer fee, net amount)
- Investor name
- Request date
- Description
- Document list with download buttons
- Action buttons (Approve, Reject)

### Rejection Modal:
- Dropdown for rejection reason selection
- Text area for additional notes
- Cancel and Submit buttons

### Request System Screen:
- **Stats Cards**: Pending Requests, Approved Today, Rejected, High Priority
- **Tabs**: All Requests, Approved, Pending, Rejected
- **Request Card**: Shows request type, title, requester, SPV, date, priority badge
- **Actions**: Approve Request, Reject, Review Details buttons

### New Request Form:
- Request Type dropdown
- Priority selector
- Request Title input
- Related Entity input (e.g., SPV-001, User ID)
- Description text area
- Submit button

---

## Tips for Frontend Developers

1. **Status Colors**: Use consistent color coding
   - 🟡 pending_approval/pending - Yellow
   - 🟢 approved/completed - Green
   - 🔴 rejected - Red

2. **Priority Badges**: Visual indicators for priority
   - Low - Gray
   - Medium - Blue
   - High - Orange  
   - Urgent - Red

3. **Urgent Indicators**: Show visual alerts for:
   - Transfers pending > 7 days (`is_urgent: true`)
   - Requests past due date (`is_overdue: true`)
   - High/Urgent priority requests (`is_urgent_priority: true`)

4. **Statistics**: Update dashboard stats on page load and after actions

5. **Document Handling**: Use proper file input and FormData for uploads

6. **Real-time Updates**: Consider polling or WebSocket for status changes

7. **Admin Actions**: Hide approve/reject buttons for non-admin users

8. **Validation**: Show rejection reason dropdown with predefined options for transfers

---

## Summary

The Transfers & Requests system provides:
- ✅ Complete transfer lifecycle management
- ✅ Flexible request & approval workflows
- ✅ Document management
- ✅ Multi-party participant tracking
- ✅ Admin approval workflows
- ✅ Statistics and analytics
- ✅ Priority-based request handling
- ✅ Comprehensive audit trail

Perfect for managing SPV ownership transfers and general approval workflows! 🚀📊
