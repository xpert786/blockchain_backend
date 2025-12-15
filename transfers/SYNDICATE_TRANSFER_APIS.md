# Syndicate Transfer & Request Management APIs

> **Note:** All APIs are already implemented in the codebase. This documentation provides complete payloads and endpoint details.

---

## 📊 API Overview (Based on Figma Screens)

| Screen | APIs Used |
|--------|-----------|
| Transfer Management (30) | `/api/transfers/`, `/api/transfers/statistics/`, `/api/transfers/{id}/approve/`, `/api/transfers/{id}/reject/` |
| Transfer Request Details (31) | `/api/transfers/{id}/`, `/api/transfer-documents/{id}/download/` |
| Reject Transfer Modal (32) | `/api/transfers/{id}/reject/` |
| Request & Approval System (33) | `/api/requests/`, `/api/requests/statistics/`, `/api/requests/{id}/approve/`, `/api/requests/{id}/reject/` |

---

## 🔄 Transfer Management APIs

### 1. Get Transfer Statistics

```http
GET /api/transfers/statistics/
Authorization: Bearer {token}
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
    "urgent_count": 2
}
```

---

### 2. List All Transfers

```http
GET /api/transfers/
Authorization: Bearer {token}
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `pending_approval`, `approved`, `completed`, `rejected` |
| `spv` | integer | Filter by SPV ID |
| `search` | string | Search by transfer ID, participants, SPV name |

**Examples:**
```http
GET /api/transfers/?status=pending_approval
GET /api/transfers/?status=completed
GET /api/transfers/?status=rejected
GET /api/transfers/?search=TXN-001
```

**Response:**
```json
[
    {
        "id": 1,
        "transfer_id": "TXN-001",
        "requester": 1,
        "requester_detail": {
            "id": 1,
            "username": "alice_investor",
            "email": "alice@email.com",
            "full_name": "Alice Investor"
        },
        "recipient": 2,
        "recipient_detail": {
            "id": 2,
            "username": "bob_smith",
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
        "investor_name": "Michael Investor",
        "requested_at": "2024-03-16T10:00:00Z",
        "documents_count": 2,
        "is_urgent": false
    }
]
```

---

### 3. Get Transfer Details

```http
GET /api/transfers/{id}/
Authorization: Bearer {token}
```

**Response:**
```json
{
    "id": 1,
    "transfer_id": "TXN-001",
    "requester": 1,
    "requester_detail": {
        "id": 1,
        "username": "alice_investor",
        "email": "alice@email.com",
        "full_name": "Alice Investor"
    },
    "recipient": 2,
    "recipient_detail": {
        "id": 2,
        "username": "bob_smith",
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
    "description": "Request To Transfer Tokens To External Wallet For Liquidity Purposes.",
    "investor_name": "Michael Investor",
    "documents": [
        {
            "id": 1,
            "file": "/media/transfers/1/documents/transfer_form.pdf",
            "original_filename": "Transfer Request Form.Pdf",
            "file_size": 245678,
            "file_size_mb": 0.23,
            "mime_type": "application/pdf",
            "uploaded_by": 1,
            "uploaded_by_detail": {
                "id": 1,
                "username": "alice_investor",
                "email": "alice@email.com"
            },
            "uploaded_at": "2024-01-14T10:30:00Z"
        }
    ],
    "documents_count": 2,
    "is_urgent": false,
    "requested_at": "2024-01-14T10:00:00Z",
    "updated_at": "2024-01-14T10:30:00Z"
}
```

---

### 4. Create Transfer Request (Investor)

```http
POST /api/transfers/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
    "recipient": 2,
    "spv": 1,
    "shares": 125,
    "amount": 50000,
    "transfer_fee": 250,
    "description": "Request To Transfer Tokens To External Wallet For Liquidity Purposes.",
    "investor_name": "Michael Investor"
}
```

**Response:**
```json
{
    "id": 1,
    "transfer_id": "TXN-A1B2C3",
    "status": "pending_approval",
    ...
}
```

---

### 5. Approve Transfer (Syndicate/Admin)

```http
POST /api/transfers/{id}/approve/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:** (optional)
```json
{}
```

**Response:**
```json
{
    "message": "Transfer approved successfully",
    "data": {
        "id": 1,
        "transfer_id": "TXN-001",
        "status": "approved",
        "approved_by": 5,
        "approved_by_detail": {
            "id": 5,
            "username": "john_doe",
            "email": "john@syndicate.com"
        },
        "approved_at": "2024-03-16T14:30:00Z",
        ...
    }
}
```

---

### 6. Reject Transfer (Syndicate/Admin)

```http
POST /api/transfers/{id}/reject/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
    "rejection_reason": "invalid_documents",
    "rejection_notes": "The transfer request form is missing required signatures."
}
```

**Rejection Reason Options:**

| Value | Display |
|-------|---------|
| `recipient_not_verified` | Recipient is not a verified investor |
| `insufficient_funds` | Insufficient funds |
| `invalid_documents` | Invalid or missing documents |
| `compliance_issue` | Compliance issue |
| `other` | Other |

**Response:**
```json
{
    "message": "Transfer rejected successfully",
    "data": {
        "id": 1,
        "transfer_id": "TXN-001",
        "status": "rejected",
        "rejection_reason": "invalid_documents",
        "rejection_notes": "The transfer request form is missing required signatures.",
        "rejected_by": 5,
        "rejected_by_detail": {
            "id": 5,
            "username": "john_doe",
            "email": "john@syndicate.com"
        },
        "rejected_at": "2024-03-16T14:30:00Z",
        ...
    }
}
```

---

### 7. Complete Transfer (After Approval)

```http
POST /api/transfers/{id}/complete/
Authorization: Bearer {token}
```

**Response:**
```json
{
    "message": "Transfer completed successfully",
    "data": {
        "id": 1,
        "transfer_id": "TXN-001",
        "status": "completed",
        "completed_at": "2024-03-17T10:00:00Z",
        ...
    }
}
```

---

### 8. Add Document to Transfer

```http
POST /api/transfers/{id}/add_document/
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
file: <binary file>
```

**Response:**
```json
{
    "message": "Document added successfully",
    "data": {
        "id": 1,
        "original_filename": "Transfer Request Form.Pdf",
        "file_size": 245678,
        "file_size_mb": 0.23,
        ...
    }
}
```

---

### 9. Download Transfer Document

```http
GET /api/transfer-documents/{id}/download/
Authorization: Bearer {token}
```

**Response:** Binary file download

---

## 📋 Request & Approval System APIs

### 1. Get Request Statistics

```http
GET /api/requests/statistics/
Authorization: Bearer {token}
```

**Response:**
```json
{
    "total_requests": 5,
    "pending": 2,
    "approved_today": 3,
    "rejected": 2,
    "high_priority": 1,
    "overdue": 0
}
```

---

### 2. List All Requests

```http
GET /api/requests/
Authorization: Bearer {token}
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | `pending`, `approved`, `rejected` |
| `priority` | string | `low`, `medium`, `high`, `urgent` |
| `request_type` | string | See request types below |
| `spv` | integer | Filter by SPV ID |
| `search` | string | Search by ID, title, description |

**Request Types:**

| Value | Display |
|-------|---------|
| `spv_update` | Update SPV Investment Terms |
| `contact_update` | Update Contact Information |
| `document_approval` | Document Approval |
| `kyc_update` | KYC Update |
| `investment_change` | Investment Change |
| `transfer_approval` | Transfer Approval |
| `other` | Other |

**Examples:**
```http
GET /api/requests/?status=pending
GET /api/requests/?priority=high
GET /api/requests/?request_type=spv_update
```

**Response:**
```json
[
    {
        "id": 1,
        "request_id": "SPV-001",
        "request_type": "spv_update",
        "title": "Update SPV Investment Terms",
        "priority": "high",
        "requester": 1,
        "requester_detail": {
            "id": 1,
            "username": "john_investor",
            "email": "john@email.com",
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
        "created_at": "2024-03-15T16:00:00Z",
        "due_date": null,
        "documents_count": 0,
        "is_overdue": false,
        "is_urgent_priority": true
    }
]
```

---

### 3. Get Request Details

```http
GET /api/requests/{id}/
Authorization: Bearer {token}
```

**Response:**
```json
{
    "id": 1,
    "request_id": "SPV-001",
    "request_type": "spv_update",
    "title": "Update SPV Investment Terms",
    "description": "Request to increase maximum cap from $5M to $8M for Tech Startup Fund Q4",
    "priority": "high",
    "requester": 1,
    "requester_detail": {...},
    "related_entity": "SPV-001",
    "spv": 1,
    "spv_detail": {...},
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
    "created_at": "2024-03-15T16:00:00Z",
    "updated_at": "2024-03-15T16:00:00Z",
    "due_date": null
}
```

---

### 4. Create Request (Investor)

```http
POST /api/requests/
Authorization: Bearer {token}
Content-Type: application/json
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
    "due_date": "2024-03-20T23:59:59Z"
}
```

---

### 5. Approve Request (Syndicate/Admin)

```http
POST /api/requests/{id}/approve/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
    "approval_notes": "Approved. Cap increase has been processed."
}
```

**Response:**
```json
{
    "message": "Request approved successfully",
    "data": {
        "id": 1,
        "request_id": "SPV-001",
        "status": "approved",
        "approved_by": 5,
        "approved_by_detail": {
            "id": 5,
            "username": "john_doe",
            "email": "john@syndicate.com"
        },
        "approved_at": "2024-03-16T10:00:00Z",
        "approval_notes": "Approved. Cap increase has been processed.",
        ...
    }
}
```

---

### 6. Reject Request (Syndicate/Admin)

```http
POST /api/requests/{id}/reject/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
    "rejection_reason": "The requested cap increase exceeds regulatory limits for this fund type."
}
```

**Response:**
```json
{
    "message": "Request rejected successfully",
    "data": {
        "id": 1,
        "request_id": "SPV-001",
        "status": "rejected",
        "rejected_by": 5,
        "rejected_by_detail": {...},
        "rejected_at": "2024-03-16T10:00:00Z",
        "rejection_reason": "The requested cap increase exceeds regulatory limits for this fund type.",
        ...
    }
}
```

---

### 7. Add Document to Request

```http
POST /api/requests/{id}/add_document/
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
file: <binary file>
```

---

### 8. Download Request Document

```http
GET /api/request-documents/{id}/download/
Authorization: Bearer {token}
```

---

## 🔐 Permissions

| Action | Investor | Syndicate/Admin |
|--------|----------|-----------------|
| List own transfers/requests | ✅ | ✅ (all) |
| View details | ✅ (own) | ✅ (all) |
| Create transfer/request | ✅ | ✅ |
| Approve | ❌ | ✅ |
| Reject | ❌ | ✅ |
| Complete | ❌ | ✅ |
| Add documents | ✅ (own) | ✅ |
| Download documents | ✅ (own) | ✅ (all) |

---

## 📁 Status Values

### Transfer Status

| Status | Description |
|--------|-------------|
| `pending_approval` | Awaiting syndicate approval |
| `approved` | Approved, awaiting completion |
| `completed` | Transfer completed |
| `rejected` | Transfer rejected |

### Request Status

| Status | Description |
|--------|-------------|
| `pending` | Awaiting approval |
| `approved` | Request approved |
| `rejected` | Request rejected |
