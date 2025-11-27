# Documents App - API Documentation

## Overview

The Documents app manages investment-related documents, agreements, signatures, and document generation from templates. It provides a complete document lifecycle management system with digital signature workflows.

## Key Features

- ✅ Document upload and management
- ✅ Version control for documents
- ✅ Multi-party digital signature workflow
- ✅ Document templates with dynamic field generation
- ✅ Access control (owner/admin permissions)
- ✅ Document status tracking (Draft → Review → Signatures → Signed → Finalized)
- ✅ File download with proper content types
- ✅ Document statistics and analytics
- ✅ Template-based document generation

---

## Data Models

### 1. Document Model

**Fields:**
- `document_id` - Auto-generated unique ID (e.g., "INV-A2B3C4")
- `title` - Document title
- `description` - Document description
- `document_type` - Type of document (investment_agreement, kyc_documentation, term_sheet, etc.)
- `file` - Uploaded file (PDF, DOC, DOCX, XLS, XLSX, TXT)
- `original_filename` - Original name of uploaded file
- `file_size` - Size in bytes
- `mime_type` - File MIME type
- `version` - Version number (e.g., "1.0")
- `parent_document` - Reference to parent for version tracking
- `status` - Current status (draft, pending_review, pending_signatures, signed, finalized, rejected)
- `requires_admin_review` - Boolean flag
- `review_notes` - Admin review notes
- `created_by` - User who created the document
- `spv` - Associated SPV (optional)
- `syndicate` - Associated Syndicate (optional)
- `finalized_at` - Timestamp when finalized

### 2. DocumentSignatory Model

**Fields:**
- `document` - Reference to Document
- `user` - User who needs to sign
- `role` - Signatory role (e.g., "Investor", "Manager")
- `signed` - Boolean (signed or not)
- `signed_at` - Timestamp when signed
- `signature_ip` - IP address when signed
- `signature_location` - Location when signed
- `notes` - Additional notes
- `invited_at` - When invited to sign
- `invited_by` - User who invited this signatory

### 3. DocumentTemplate Model

**Fields:**
- `name` - Template name
- `description` - Template description
- `version` - Template version
- `category` - Category (legal, compliance, informational, financial, other)
- `template_file` - Template file (DOCX, PDF, JSON)
- `required_fields` - JSON array of required fields with validation rules
- `enable_digital_signature` - Whether to enable signature workflow
- `is_active` - Whether template is active
- `created_by` - Creator user

### 4. DocumentGeneration Model

**Fields:**
- `template` - Reference to DocumentTemplate
- `generated_document` - Reference to generated Document
- `generation_data` - JSON data used for generation
- `generated_by` - User who generated the document
- `generated_at` - Timestamp
- `enable_digital_signature` - Whether signature workflow was enabled

---

## API Endpoints

### Documents Management

#### 1. List All Documents
```http
GET /blockchain-backend/api/documents/
```

**Query Parameters:**
- `status` - Filter by status (draft, pending_review, etc.)
- `document_type` - Filter by document type
- `search` - Search in title, document_id, description, filename

**Response:**
```json
[
  {
    "id": 1,
    "document_id": "INV-A2B3C4",
    "title": "Investment Agreement - John Doe",
    "document_type": "investment_agreement",
    "status": "pending_signatures",
    "version": "1.0",
    "file_size_mb": 0.52,
    "signatories_count": 3,
    "signed_count": 1,
    "pending_signatures_count": 2,
    "created_by_name": "Admin User",
    "created_at": "2025-11-26T10:00:00Z",
    "updated_at": "2025-11-26T12:00:00Z"
  }
]
```

#### 2. Create Document
```http
POST /blockchain-backend/api/documents/
Content-Type: multipart/form-data
```

**Request Body:**
```json
{
  "title": "Investment Agreement",
  "description": "Main investment agreement for Series A",
  "document_type": "investment_agreement",
  "file": "<FILE>",
  "version": "1.0",
  "status": "draft",
  "spv": 1,
  "syndicate": 2
}
```

**Response:** (201 Created)

```json
{
  "id": 1,
  "document_id": "INV-A2B3C4",
  "title": "Investment Agreement",
  "document_type": "investment_agreement",
  "status": "draft",
  "file": "/media/documents/investment_agreement/uuid.pdf",
  "created_by_detail": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Admin User"
  },
  "signatories": [],
  "created_at": "2025-11-26T10:00:00Z"
}
```

#### 3. Get Document Details
```http
GET /blockchain-backend/api/documents/{id}/
```

**Response:**
```json
{
  "id": 1,
  "document_id": "INV-A2B3C4",
  "title": "Investment Agreement",
  "description": "Main investment agreement",
  "document_type": "investment_agreement",
  "file": "/media/documents/investment_agreement/uuid.pdf",
  "original_filename": "investment_agreement.pdf",
  "file_size": 523456,
  "file_size_mb": 0.52,
  "mime_type": "application/pdf",
  "version": "1.0",
  "parent_document": null,
  "status": "pending_signatures",
  "requires_admin_review": false,
  "review_notes": null,
  "created_by": 1,
  "created_by_detail": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Admin User"
  },
  "spv": 1,
  "spv_detail": {
    "id": 1,
    "display_name": "SPV Fund A",
    "status": "active"
  },
  "syndicate": null,
  "syndicate_detail": null,
  "signatories": [
    {
      "id": 1,
      "user_detail": {
        "id": 2,
        "username": "investor1",
        "email": "investor@example.com",
        "full_name": "John Investor"
      },
      "role": "Investor",
      "signed": false,
      "signed_at": null,
      "invited_at": "2025-11-26T10:30:00Z"
    }
  ],
  "signatories_count": 3,
  "signed_count": 1,
  "pending_signatures_count": 2,
  "finalized_at": null,
  "created_at": "2025-11-26T10:00:00Z",
  "updated_at": "2025-11-26T12:00:00Z"
}
```

#### 4. Update Document
```http
PATCH /blockchain-backend/api/documents/{id}/
```

**Request Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "status": "pending_review"
}
```

#### 5. Delete Document
```http
DELETE /blockchain-backend/api/documents/{id}/
```

### Document Actions

#### 6. Download Document
```http
GET /blockchain-backend/api/documents/{id}/download/
```

**Response:** File download with proper content-type and filename

#### 7. Update Document Status
```http
PATCH /blockchain-backend/api/documents/{id}/update_status/
```

**Request Body:**
```json
{
  "status": "finalized"
}
```

**Valid Statuses:**
- `draft` - Initial draft
- `pending_review` - Awaiting admin review
- `pending_signatures` - Awaiting signatures
- `signed` - All parties signed
- `finalized` - Finalized by admin
- `rejected` - Rejected by admin

**Note:** Only admins can set status to `finalized` or `rejected`.

#### 8. Get Document Statistics
```http
GET /blockchain-backend/api/documents/statistics/
```

**Response:**
```json
{
  "total_documents": 45,
  "pending_signatures": 12,
  "signed_documents": 20,
  "rejected": 2,
  "draft": 5,
  "pending_review": 3,
  "finalized": 18
}
```

### Signatory Management

#### 9. Add Signatory to Document
```http
POST /blockchain-backend/api/documents/{id}/add_signatory/
```

**Request Body:**
```json
{
  "user_id": 2,
  "role": "Investor"
}
```

**Response:**
```json
{
  "message": "Signatory added successfully",
  "data": {
    "id": 1,
    "document": 1,
    "user_detail": {
      "id": 2,
      "username": "investor1",
      "email": "investor@example.com",
      "full_name": "John Investor"
    },
    "role": "Investor",
    "signed": false,
    "signed_at": null,
    "invited_at": "2025-11-26T10:30:00Z",
    "invited_by_detail": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com"
    }
  }
}
```

#### 10. Sign Document
```http
POST /blockchain-backend/api/documents/{id}/sign/
```

**Description:** Current user signs the document (must be a signatory).

**Response:**
```json
{
  "message": "Document signed successfully",
  "data": {
    "id": 1,
    "signed": true,
    "signed_at": "2025-11-26T14:30:00Z",
    "signature_ip": "192.168.1.1"
  }
}
```

**Auto Status Update:** If all signatories have signed, document status automatically changes to `signed`.

#### 11. List Document Signatories
```http
GET /blockchain-backend/api/document-signatories/
```

**Query Parameters:**
- `document` - Filter by document ID

**Response:**
```json
[
  {
    "id": 1,
    "document": 1,
    "user_detail": {
      "id": 2,
      "username": "investor1",
      "email": "investor@example.com",
      "full_name": "John Investor"
    },
    "role": "Investor",
    "signed": true,
    "signed_at": "2025-11-26T14:30:00Z",
    "signature_ip": "192.168.1.1",
    "signature_location": null,
    "notes": null,
    "invited_at": "2025-11-26T10:30:00Z",
    "invited_by_detail": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com"
    }
  }
]
```

### Document Templates

#### 12. List Templates
```http
GET /blockchain-backend/api/document-templates/
```

**Query Parameters:**
- `category` - Filter by category (legal, compliance, etc.)
- `search` - Search in name, description

**Response:**
```json
[
  {
    "id": 1,
    "name": "Standard Investment Agreement",
    "description": "Template for standard investment agreements",
    "version": "1.0",
    "category": "legal",
    "enable_digital_signature": true,
    "is_active": true,
    "created_at": "2025-11-20T10:00:00Z"
  }
]
```

#### 13. Get Template Details
```http
GET /blockchain-backend/api/document-templates/{id}/
```

**Response:**
```json
{
  "id": 1,
  "name": "Standard Investment Agreement",
  "description": "Template for standard investment agreements",
  "version": "1.0",
  "category": "legal",
  "template_file": "/media/document_templates/agreement_template.docx",
  "required_fields": [
    {
      "name": "investor_name",
      "label": "Investor Name",
      "type": "text",
      "required": true
    },
    {
      "name": "investment_amount",
      "label": "Investment Amount",
      "type": "number",
      "required": true
    },
    {
      "name": "investment_date",
      "label": "Investment Date",
      "type": "date",
      "required": true
    }
  ],
  "enable_digital_signature": true,
  "is_active": true,
  "created_by": 1,
  "created_by_detail": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com"
  },
  "created_at": "2025-11-20T10:00:00Z",
  "updated_at": "2025-11-20T10:00:00Z"
}
```

#### 14. Create Template
```http
POST /blockchain-backend/api/document-templates/
Content-Type: multipart/form-data
```

**Request Body:**
```json
{
  "name": "Investment Agreement Template",
  "description": "Standard investment agreement",
  "version": "1.0",
  "category": "legal",
  "template_file": "<FILE>",
  "required_fields": [
    {
      "name": "investor_name",
      "label": "Investor Name",
      "type": "text",
      "required": true
    }
  ],
  "enable_digital_signature": true,
  "is_active": true
}
```

#### 15. Get Template Required Fields
```http
GET /blockchain-backend/api/document-templates/{id}/required_fields/
```

**Response:**
```json
{
  "template_id": 1,
  "template_name": "Standard Investment Agreement",
  "required_fields": [
    {
      "name": "investor_name",
      "label": "Investor Name",
      "type": "text",
      "required": true
    },
    {
      "name": "investment_amount",
      "label": "Investment Amount",
      "type": "number",
      "required": true
    }
  ],
  "enable_digital_signature": true
}
```

#### 16. Duplicate Template
```http
POST /blockchain-backend/api/document-templates/{id}/duplicate/
```

**Description:** Creates a new version of the template (increments version by 0.1).

**Response:**
```json
{
  "message": "Template duplicated successfully",
  "data": {
    "id": 2,
    "name": "Standard Investment Agreement",
    "version": "1.1",
    "...": "..."
  }
}
```

### Document Generation

#### 17. Generate Document from Template
```http
POST /blockchain-backend/api/documents/generate-from-template/
```

**Request Body:**
```json
{
  "template_id": 1,
  "field_data": {
    "investor_name": "John Doe",
    "investment_amount": 50000,
    "investment_date": "2025-12-01",
    "company_name": "Tech Startup Inc."
  },
  "enable_digital_signature": true,
  "title": "Investment Agreement - John Doe",
  "description": "Generated investment agreement",
  "spv_id": 1,
  "syndicate_id": 2,
  "signatories": [
    {
      "user_id": 2,
      "role": "Investor"
    },
    {
      "user_id": 3,
      "role": "Manager"
    }
  ]
}
```

**Response:**
```json
{
  "message": "Document generated successfully",
  "data": {
    "document": {
      "id": 10,
      "document_id": "OTH-F3A1B2",
      "title": "Investment Agreement - John Doe",
      "status": "pending_signatures",
      "signatories": [
        {
          "user_detail": {
            "id": 2,
            "username": "investor1",
            "full_name": "John Doe"
          },
          "role": "Investor",
          "signed": false
        }
      ]
    },
    "generation": {
      "id": 1,
      "template_detail": {
        "id": 1,
        "name": "Standard Investment Agreement",
        "version": "1.0"
      },
      "generation_data": {
        "investor_name": "John Doe",
        "investment_amount": 50000
      },
      "generated_by_detail": {
        "id": 1,
        "username": "admin",
        "full_name": "Admin User"
      },
      "generated_at": "2025-11-26T15:00:00Z",
      "enable_digital_signature": true
    }
  }
}
```

#### 18. Get Generated Documents
```http
GET /blockchain-backend/api/documents/generated-documents/
```

**Query Parameters:**
- `template` - Filter by template ID

**Response:**
```json
[
  {
    "id": 1,
    "template_detail": {
      "id": 1,
      "name": "Standard Investment Agreement",
      "version": "1.0"
    },
    "generated_document_detail": {
      "id": 10,
      "document_id": "OTH-F3A1B2",
      "title": "Investment Agreement - John Doe",
      "status": "signed"
    },
    "generation_data": {
      "investor_name": "John Doe",
      "investment_amount": 50000
    },
    "generated_by_detail": {
      "id": 1,
      "username": "admin",
      "full_name": "Admin User"
    },
    "generated_at": "2025-11-26T15:00:00Z",
    "enable_digital_signature": true
  }
]
```

---

## Complete Workflow Flows

### Flow 1: Standard Document Upload and Signature

```
1. Admin/User uploads document
   POST /api/documents/
   → Document created with status: "draft"

2. Admin reviews and adds signatories
   POST /api/documents/{id}/add_signatory/ (for each signatory)
   → Signatories added with signed=false

3. Admin changes status to pending_signatures
   PATCH /api/documents/{id}/update_status/
   { "status": "pending_signatures" }

4. Each signatory signs the document
   POST /api/documents/{id}/sign/
   → signed=true, signed_at recorded

5. When all sign, status auto-changes to "signed"

6. Admin finalizes
   PATCH /api/documents/{id}/update_status/
   { "status": "finalized" }
```

### Flow 2: Template-Based Document Generation

```
1. Admin creates template with required fields
   POST /api/document-templates/
   → Template created with required_fields JSON

2. User generates document from template
   POST /api/documents/generate-from-template/
   → Validates required fields
   → Creates Document record
   → Creates DocumentGeneration record
   → Adds signatories if provided
   → Sets status to "pending_signatures" if digital signature enabled

3. Signature workflow (same as Flow 1, steps 4-6)

4. Track generation history
   GET /api/documents/generated-documents/
```

### Flow 3: Document Version Control

```
1. Create original document (version 1.0)
   POST /api/documents/
   { "version": "1.0", "parent_document": null }

2. Create new version
   POST /api/documents/
   { "version": "1.1", "parent_document": <original_id> }

3. Track versions via parent_document relationship
```

---

## Permission Model

### User Roles:
- **Admin/Staff**: Full access to all documents
- **Regular User**: Can only access:
  - Documents they created
  - Documents they need to sign

### Endpoint Permissions:
- ✅ All authenticated users can list/create documents
- ✅ Only document owner or admin can update/delete
- ✅ Only signatories can sign documents
- ✅ Only admins can finalize or reject documents
- ✅ Only admins can create templates

---

## Status Lifecycle

```
draft
  ↓
pending_review (optional)
  ↓
pending_signatures
  ↓
signed (auto when all sign)
  ↓
finalized (admin only)

OR

rejected (admin only, at any stage)
```

---

## Frontend Integration Example

### Upload Document with Signature Workflow

```javascript
// 1. Upload document
const formData = new FormData();
formData.append('title', 'Investment Agreement');
formData.append('document_type', 'investment_agreement');
formData.append('file', fileInput.files[0]);
formData.append('status', 'draft');

const response = await fetch('/blockchain-backend/api/documents/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});

const document = await response.json();

// 2. Add signatories
const signatories = [2, 3, 5]; // user IDs
for (const userId of signatories) {
  await fetch(`/blockchain-backend/api/documents/${document.id}/add_signatory/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      user_id: userId,
      role: 'Investor'
    })
  });
}

// 3. Update status to pending signatures
await fetch(`/blockchain-backend/api/documents/${document.id}/update_status/`, {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    status: 'pending_signatures'
  })
});
```

### Generate Document from Template

```javascript
const response = await fetch('/blockchain-backend/api/documents/generate-from-template/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    template_id: 1,
    field_data: {
      investor_name: 'John Doe',
      investment_amount: 50000,
      investment_date: '2025-12-01'
    },
    enable_digital_signature: true,
    title: 'Investment Agreement - John Doe',
    signatories: [
      { user_id: 2, role: 'Investor' },
      { user_id: 3, role: 'Manager' }
    ]
  })
});

const result = await response.json();
console.log('Document generated:', result.data.document);
```

### Sign Document (Signatory View)

```javascript
const response = await fetch(`/blockchain-backend/api/documents/${documentId}/sign/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const result = await response.json();
if (result.message === 'Document signed successfully') {
  alert('Document signed!');
}
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
- `403` - Forbidden (permission denied)
- `404` - Not Found
- `500` - Internal Server Error

---

## Tips for Frontend Developers

1. **File Uploads**: Use `FormData` and `multipart/form-data`
2. **Download Documents**: Use `<a>` tag or `fetch` with blob response
3. **Track Signatures**: Poll document details or use WebSocket for real-time updates
4. **Validation**: Check `required_fields` before generating documents from templates
5. **Status Colors**: Use different colors for each status in UI
6. **Permissions**: Hide action buttons based on user role and document status

---

## Database Relationships

```
Document
  ├── created_by (User)
  ├── spv (SPV) [optional]
  ├── syndicate (SyndicateProfile) [optional]
  ├── parent_document (Document) [optional, for versions]
  └── signatories (DocumentSignatory) [multiple]

DocumentSignatory
  ├── document (Document)
  ├── user (User)
  └── invited_by (User)

DocumentTemplate
  └── created_by (User) [optional]

DocumentGeneration
  ├── template (DocumentTemplate)
  ├── generated_document (Document)
  └── generated_by (User)
```

---

## Summary

The Documents app provides a comprehensive document management system with:
- ✅ Full CRUD operations
- ✅ Digital signature workflows
- ✅ Template-based generation
- ✅ Version control
- ✅ Access control
- ✅ Audit trail via DocumentGeneration
- ✅ Flexible status management
- ✅ SPV/Syndicate association

Perfect for managing investment agreements, KYC documents, and compliance paperwork! 📄✨
