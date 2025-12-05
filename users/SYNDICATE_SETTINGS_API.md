# Syndicate Settings API Documentation

## Overview

The Syndicate Settings APIs allow syndicate users to manage their profile settings after completing the onboarding process. These endpoints provide access to various configuration options including general information, team management, compliance documents, and more.

## Base URL

```
/blockchain-backend/api/syndicate/settings/
```

## Authentication

All settings endpoints require:
- **Authentication**: JWT Bearer token
- **Role**: User must have `role='syndicate'`
- **Profile**: Syndicate profile must exist (onboarding completed)

---

## API Endpoints

### 1. Settings Overview

Get all settings data at once.

```http
GET /api/syndicate/settings/overview/
```

**Response:**
```json
{
  "success": true,
  "data": {
    "general_info": {
      "first_name": "John",
      "last_name": "Doe",
      "bio": "Experienced venture capital manager with 10+ years in early-stage technology investments.",
      "link": "https://extrmallinks.com",
      "logo": "/media/syndicate_logos/logo.png"
    },
    "kyb_verification": {
      "firm_name": "Tech Ventures LLC",
      "description": "Leading early-stage technology fund",
      "risk_regulatory_attestation": true,
      "jurisdictional_compliance_acknowledged": true,
      "additional_compliance_policies": "/media/syndicate_compliance/policy.pdf"
    },
    "compliance": {
      "risk_regulatory_attestation": true,
      "jurisdictional_compliance_acknowledged": true,
      "additional_compliance_policies": "/media/syndicate_compliance/policy.pdf"
    },
    "team_management": {
      "enable_role_based_access_controls": true
    },
    "jurisdictional": {
      "jurisdictional_compliance_acknowledged": true,
      "geographies": [
        {"id": 1, "name": "United States", "region": "North America"}
      ]
    },
    "portfolio": {
      "sectors": [
        {"id": 1, "name": "Technology"}
      ],
      "enable_platform_lp_access": true,
      "existing_lp_count": "11-25"
    },
    "user": {
      "email": "john@example.com",
      "phone_number": "+1234567890",
      "email_verified": true,
      "phone_verified": true
    }
  }
}
```

---

### 2. General Information

Manage general profile information (Screen 35).

```http
GET /api/syndicate/settings/general-info/
PATCH /api/syndicate/settings/general-info/
```

**GET Response:**
```json
{
  "success": true,
  "data": {
    "first_name": "John",
    "last_name": "Doe",
    "bio": "Experienced venture capital manager with 10+ years in early-stage technology investments.",
    "link": "https://extrmallinks.com",
    "logo": "/media/syndicate_logos/logo.png"
  }
}
```

**PATCH Request (JSON):**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "bio": "Experienced venture capital manager with 10+ years in early-stage technology investments.",
  "link": "https://extrmallinks.com"
}
```

**PATCH Request (Multipart for logo upload):**
```
Content-Type: multipart/form-data

first_name: John
last_name: Doe
bio: Experienced venture capital manager...
link: https://extrmallinks.com
logo: <FILE>
```

**PATCH Response:**
```json
{
  "success": true,
  "message": "General information updated successfully",
  "data": {
    "first_name": "John",
    "last_name": "Doe",
    "bio": "Experienced venture capital manager with 10+ years in early-stage technology investments.",
    "link": "https://extrmallinks.com",
    "logo": "/media/syndicate_logos/logo_updated.png"
  }
}
```

---

### 3. Team Management

Manage team members and role-based access controls (Screen 36).

```http
GET /api/syndicate/settings/team-management/
```

**Response:**
```json
{
  "success": true,
  "message": "Team management endpoint - team member models to be implemented",
  "data": {
    "syndicate_id": 1,
    "firm_name": "Tech Ventures LLC",
    "enable_role_based_access_controls": true,
    "team_members": []
  }
}
```

**Note:** Full team member CRUD operations will be implemented in separate team member endpoints.

---

### 4. KYB Verification

Manage KYB (Know Your Business) verification data (Screen 35 - bottom section).

```http
GET /api/syndicate/settings/kyb-verification/
PATCH /api/syndicate/settings/kyb-verification/
```

**GET Response:**
```json
{
  "success": true,
  "data": {
    "firm_name": "Tech Ventures LLC",
    "description": "Leading early-stage technology fund",
    "risk_regulatory_attestation": true,
    "jurisdictional_compliance_acknowledged": true,
    "additional_compliance_policies": "/media/syndicate_compliance/policy.pdf"
  }
}
```

**PATCH Request:**
```json
{
  "firm_name": "Tech Ventures LLC",
  "description": "Leading early-stage technology fund",
  "risk_regulatory_attestation": true,
  "jurisdictional_compliance_acknowledged": true
}
```

**PATCH Response:**
```json
{
  "success": true,
  "message": "KYB verification data updated successfully",
  "data": {
    "firm_name": "Tech Ventures LLC",
    "description": "Updated description",
    "risk_regulatory_attestation": true,
    "jurisdictional_compliance_acknowledged": true,
    "additional_compliance_policies": "/media/syndicate_compliance/policy.pdf"
  }
}
```

---

### 5. Compliance & Accreditation

Manage compliance documents and attestations (Screen 37).

```http
GET /api/syndicate/settings/compliance/
PATCH /api/syndicate/settings/compliance/
```

**GET Response:**
```json
{
  "success": true,
  "data": {
    "risk_regulatory_attestation": true,
    "jurisdictional_compliance_acknowledged": true,
    "additional_compliance_policies": "/media/syndicate_compliance/policy.pdf",
    "compliance_file_url": "http://localhost:8000/media/syndicate_compliance/policy.pdf"
  }
}
```

**PATCH Request (Multipart for file upload):**
```
Content-Type: multipart/form-data

risk_regulatory_attestation: true
jurisdictional_compliance_acknowledged: true
additional_compliance_policies: <FILE>
```

**PATCH Response:**
```json
{
  "success": true,
  "message": "Compliance data updated successfully",
  "data": {
    "risk_regulatory_attestation": true,
    "jurisdictional_compliance_acknowledged": true,
    "additional_compliance_policies": "/media/syndicate_compliance/new_policy.pdf",
    "compliance_file_url": "http://localhost:8000/media/syndicate_compliance/new_policy.pdf"
  }
}
```

---

### 6. Jurisdictional Settings

Manage legal and compliance configurations for your selected jurisdiction.

```http
GET /api/syndicate/settings/jurisdictional/
PATCH /api/syndicate/settings/jurisdictional/
GET /api/syndicate/settings/jurisdictional/<id>/
```

**GET All Jurisdictions Response:**
```json
{
  "success": true,
  "message": "Jurisdictional settings endpoint",
  "data": {
    "jurisdictional_compliance_acknowledged": true,
    "geographies": [
      {
        "id": 1,
        "name": "United States",
        "region": "North America",
        "country_code": "US"
      },
      {
        "id": 2,
        "name": "United Kingdom",
        "region": "Europe",
        "country_code": "GB"
      }
    ]
  }
}
```

**GET Specific Geography Response:**
```json
{
  "success": true,
  "message": "Geography details retrieved successfully",
  "data": {
    "id": 1,
    "name": "United States",
    "region": "North America",
    "country_code": "US",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**PATCH Request:**
```json
{
  "jurisdictional_compliance_acknowledged": true,
  "geography_ids": [1, 2, 3]
}
```

**PATCH Response:**
```json
{
  "success": true,
  "message": "Jurisdictional settings updated successfully",
  "data": {
    "jurisdictional_compliance_acknowledged": true,
    "geographies": [
      {
        "id": 1,
        "name": "United States",
        "region": "North America",
        "country_code": "US"
      },
      {
        "id": 2,
        "name": "United Kingdom",
        "region": "Europe",
        "country_code": "GB"
      },
      {
        "id": 3,
        "name": "Canada",
        "region": "North America",
        "country_code": "CA"
      }
    ]
  }
}
```

---

### 7. Portfolio Company Outreach

Manage platform contact permissions for portfolio company valuation, tax reporting, and compliance purposes.

```http
GET /api/syndicate/settings/portfolio/
PATCH /api/syndicate/settings/portfolio/
```

**Description:**
This endpoint controls whether the platform is allowed to contact your portfolio companies directly for valuation, tax reporting, and compliance purposes. Use the `restrict` or `allow` fields in PATCH requests to control this setting.

**GET Portfolio Settings Response:**
```json
{
  "success": true,
  "message": "Portfolio company outreach settings retrieved successfully",
  "data": {
    "restrict": false,
    "allow": true
  }
}
```

**PATCH Request - Allow Platform Contact:**
```json
{
  "allow": true
}
```

**PATCH Request - Restrict Platform Contact:**
```json
{
  "restrict": true
}
```

**PATCH Response:**
```json
{
  "success": true,
  "message": "Portfolio company outreach settings updated successfully",
  "data": {
    "restrict": true,
    "allow": false
  }
}
```

**Field Definitions:**
- `restrict` (boolean, read-only): `true` if platform cannot contact portfolio companies directly
- `allow` (boolean, read-only): `true` if platform can contact portfolio companies directly
- `restrict` (boolean, write-only in PATCH): Set to `true` to prevent platform contact
- `allow` (boolean, write-only in PATCH): Set to `true` to allow platform contact

**Note:** `restrict` and `allow` are inverse of each other. Sending either field in a PATCH request will update the setting accordingly.

---

### 8. Notifications & Communication

Manage notification and communication preferences.

```http
GET /api/syndicate/settings/notifications/
PATCH /api/syndicate/settings/notifications/
GET /api/syndicate/settings/notifications/<preference_type>/
```

**GET All Notification Settings Response:**
```json
{
  "success": true,
  "message": "Notifications & communication settings",
  "data": {
    "email": "john@example.com",
    "phone_number": "+1234567890",
    "email_verified": true,
    "phone_verified": true,
    "two_factor_enabled": true,
    "two_factor_method": "email",
    "notification_preference": "email",
    "notify_email_preference": true,
    "notify_new_lp_alerts": true,
    "notify_deal_updates": true
  }
}
```

**GET Specific Notification Preference Response:**

Supported preference types: `email_preference`, `lp_alerts`, `deal_updates`

```json
{
  "success": true,
  "message": "Email Preference notification preference retrieved",
  "data": {
    "type": "email_preference",
    "label": "Email Preference",
    "description": "Receive email notifications",
    "enabled": true,
    "user_email": "john@example.com",
    "user_phone_number": "+1234567890"
  }
}
```

**PATCH Request:**
```json
{
  "notification_preference": "lp_alerts",
  "notify_email_preference": true,
  "notify_new_lp_alerts": false,
  "notify_deal_updates": true
}
```

**PATCH Response:**
```json
{
  "success": true,
  "message": "Notification settings updated successfully",
  "data": {
    "email": "john@example.com",
    "phone_number": "+1234567890",
    "email_verified": true,
    "phone_verified": true,
    "two_factor_enabled": true,
    "two_factor_method": "email",
    "notification_preference": "lp_alerts",
    "notify_email_preference": true,
    "notify_new_lp_alerts": false,
    "notify_deal_updates": true
  }
}
```

---

### 9. Fee Recipient Setup

Manage fee recipient information for payment distribution.

```http
GET /api/syndicate/settings/fee-recipient/
PATCH /api/syndicate/settings/fee-recipient/
GET /api/syndicate/settings/fee-recipient/<id>/
```

**GET Fee Recipient Response:**
```json
{
  "success": true,
  "message": "Fee recipient setup",
  "data": {
    "id": 1,
    "recipient_type": "individual",
    "recipient_type_display": "Individual",
    "entity_name": "John Doe",
    "residence": "Delaware",
    "tax_id": "12-3456789",
    "id_document": "/media/fee_recipient_documents/id_doc.pdf",
    "id_document_url": "http://localhost:8000/media/fee_recipient_documents/id_doc.pdf",
    "proof_of_address": "/media/fee_recipient_documents/proof.pdf",
    "proof_of_address_url": "http://localhost:8000/media/fee_recipient_documents/proof.pdf",
    "created_at": "2024-01-20T10:15:00Z",
    "updated_at": "2024-01-20T10:15:00Z"
  }
}
```

**PATCH Request (Multipart for file uploads):**
```
Content-Type: multipart/form-data

recipient_type: individual
entity_name: John Doe
residence: Delaware
tax_id: 12-3456789
id_document: <FILE>
proof_of_address: <FILE>
```

**PATCH Response:**
```json
{
  "success": true,
  "message": "Fee recipient settings updated successfully",
  "data": {
    "id": 1,
    "recipient_type": "individual",
    "recipient_type_display": "Individual",
    "entity_name": "John Doe",
    "residence": "Delaware",
    "tax_id": "12-3456789",
    "id_document": "/media/fee_recipient_documents/id_doc_updated.pdf",
    "id_document_url": "http://localhost:8000/media/fee_recipient_documents/id_doc_updated.pdf",
    "proof_of_address": "/media/fee_recipient_documents/proof_updated.pdf",
    "proof_of_address_url": "http://localhost:8000/media/fee_recipient_documents/proof_updated.pdf",
    "created_at": "2024-01-20T10:15:00Z",
    "updated_at": "2024-01-20T11:30:00Z"
  }
}
```

---

### 10. Bank Details

Manage credit cards and bank accounts.

#### Get All Bank Details

```http
GET /api/syndicate/settings/bank-details/
```

**Response:**
```json
{
  "success": true,
  "message": "Bank details retrieved successfully",
  "data": {
    "credit_cards": [
      {
        "id": 1,
        "card_category": "credit_card",
        "card_category_display": "Credit Card",
        "card_type": "visa",
        "card_type_display": "Visa",
        "card_number": "XXXX-XXXX-XXXX-4155",
        "card_holder_name": "SMITH RHODES",
        "expiry_date": "07/29",
        "status": "active",
        "status_display": "Active",
        "is_primary": true,
        "created_at": "2025-01-15T10:30:00Z",
        "updated_at": "2025-01-15T10:30:00Z"
      },
      {
        "id": 2,
        "card_category": "debit_card",
        "card_category_display": "Debit Card",
        "card_type": "mastercard",
        "card_type_display": "Mastercard",
        "card_number": "XXXX-XXXX-XXXX-6296",
        "card_holder_name": "SMITH RHODES",
        "expiry_date": "08/26",
        "status": "active",
        "status_display": "Active",
        "is_primary": false,
        "created_at": "2025-01-16T11:20:00Z",
        "updated_at": "2025-01-16T11:20:00Z"
      }
    ],
    "bank_accounts": [
      {
        "id": 1,
        "bank_name": "ICICI Bank",
        "account_type": "checking",
        "account_type_display": "Checking",
        "account_number": "XXXX-XXXX-XXXX-9025",
        "routing_number": "021000021",
        "swift_code": "ICICINBB",
        "iban": null,
        "account_holder_name": "Tech Ventures LLC",
        "status": "active",
        "status_display": "Active",
        "is_primary": true,
        "created_at": "2025-01-10T09:15:00Z",
        "updated_at": "2025-01-10T09:15:00Z"
      }
    ]
  }
}
```

#### Add Credit Card

```http
POST /api/syndicate/settings/bank-details/
```

**Request Body:**
```json
{
  "type": "credit_card",
  "card_type": "visa",
  "card_number": "4111-1111-1111-4155",
  "card_holder_name": "SMITH RHODES",
  "expiry_date": "07/29",
  "cvv": "123",
  "status": "active",
  "is_primary": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Credit Card added successfully",
  "data": {
    "id": 3,
    "card_category": "credit_card",
    "card_category_display": "Credit Card",
    "card_type": "visa",
    "card_type_display": "Visa",
    "card_number": "XXXX-XXXX-XXXX-4155",
    "card_holder_name": "SMITH RHODES",
    "expiry_date": "07/29",
    "status": "active",
    "status_display": "Active",
    "is_primary": false,
    "created_at": "2025-01-20T14:45:00Z",
    "updated_at": "2025-01-20T14:45:00Z"
  }
}
```

#### Add Debit Card

```http
POST /api/syndicate/settings/bank-details/
```

**Request Body:**
```json
{
  "type": "debit_card",
  "card_type": "mastercard",
  "card_number": "5555-4444-3333-6296",
  "card_holder_name": "SMITH RHODES",
  "expiry_date": "08/26",
  "cvv": "456",
  "status": "active",
  "is_primary": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Debit Card added successfully",
  "data": {
    "id": 4,
    "card_category": "debit_card",
    "card_category_display": "Debit Card",
    "card_type": "mastercard",
    "card_type_display": "Mastercard",
    "card_number": "XXXX-XXXX-XXXX-6296",
    "card_holder_name": "SMITH RHODES",
    "expiry_date": "08/26",
    "status": "active",
    "status_display": "Active",
    "is_primary": true,
    "created_at": "2025-01-20T15:10:00Z",
    "updated_at": "2025-01-20T15:10:00Z"
  }
}
```

#### Add Bank Account

```http
POST /api/syndicate/settings/bank-details/
```

**Request Body:**
```json
{
  "type": "bank_account",
  "bank_name": "Chase Bank",
  "account_type": "checking",
  "account_number": "1234567890",
  "routing_number": "021000021",
  "account_holder_name": "Tech Ventures LLC",
  "status": "active",
  "is_primary": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Bank account added successfully",
  "data": {
    "id": 2,
    "bank_name": "Chase Bank",
    "account_type": "checking",
    "account_type_display": "Checking",
    "account_number": "XXXX-XXXX-XXXX-7890",
    "routing_number": "021000021",
    "swift_code": null,
    "iban": null,
    "account_holder_name": "Tech Ventures LLC",
    "status": "active",
    "status_display": "Active",
    "is_primary": false,
    "created_at": "2025-01-20T15:00:00Z",
    "updated_at": "2025-01-20T15:00:00Z"
  }
}
```

#### Get Specific Credit Card

```http
GET /api/syndicate/settings/bank-details/card/<card_id>/
```

**Response:**
```json
{
  "success": true,
  "message": "Credit card details retrieved successfully",
  "data": {
    "id": 1,
    "card_category": "credit_card",
    "card_category_display": "Credit Card",
    "card_type": "visa",
    "card_type_display": "Visa",
    "card_number": "XXXX-XXXX-XXXX-4155",
    "card_holder_name": "SMITH RHODES",
    "expiry_date": "07/29",
    "status": "active",
    "status_display": "Active",
    "is_primary": true,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  }
}
```

#### Update Credit Card

```http
PATCH /api/syndicate/settings/bank-details/card/<card_id>/
```

**Request Body:**
```json
{
  "status": "suspended",
  "is_primary": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Credit card updated successfully",
  "data": {
    "id": 1,
    "card_category": "credit_card",
    "card_category_display": "Credit Card",
    "card_type": "visa",
    "card_type_display": "Visa",
    "card_number": "XXXX-XXXX-XXXX-4155",
    "card_holder_name": "SMITH RHODES",
    "expiry_date": "07/29",
    "status": "suspended",
    "status_display": "Suspended",
    "is_primary": false,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T16:00:00Z"
  }
}
```

#### Delete Credit Card

```http
DELETE /api/syndicate/settings/bank-details/card/<card_id>/
```

**Response:**
```json
{
  "success": true,
  "message": "Credit card deleted successfully"
}
```

#### Get Specific Bank Account

```http
GET /api/syndicate/settings/bank-details/account/<account_id>/
```

**Response:**
```json
{
  "success": true,
  "message": "Bank account details retrieved successfully",
  "data": {
    "id": 1,
    "bank_name": "ICICI Bank",
    "account_type": "checking",
    "account_type_display": "Checking",
    "account_number": "XXXX-XXXX-XXXX-9025",
    "routing_number": "021000021",
    "swift_code": "ICICINBB",
    "iban": null,
    "account_holder_name": "Tech Ventures LLC",
    "status": "active",
    "status_display": "Active",
    "is_primary": true,
    "created_at": "2025-01-10T09:15:00Z",
    "updated_at": "2025-01-10T09:15:00Z"
  }
}
```

#### Update Bank Account

```http
PATCH /api/syndicate/settings/bank-details/account/<account_id>/
```

**Request Body:**
```json
{
  "status": "inactive",
  "is_primary": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Bank account updated successfully",
  "data": {
    "id": 1,
    "bank_name": "ICICI Bank",
    "account_type": "checking",
    "account_type_display": "Checking",
    "account_number": "XXXX-XXXX-XXXX-9025",
    "routing_number": "021000021",
    "swift_code": "ICICINBB",
    "iban": null,
    "account_holder_name": "Tech Ventures LLC",
    "status": "inactive",
    "status_display": "Inactive",
    "is_primary": false,
    "created_at": "2025-01-10T09:15:00Z",
    "updated_at": "2025-01-20T16:30:00Z"
  }
}
```

#### Delete Bank Account

```http
DELETE /api/syndicate/settings/bank-details/account/<account_id>/
```

**Response:**
```json
{
  "success": true,
  "message": "Bank account deleted successfully"
}
```

---

## Common Workflow

### Update General Information

```javascript
// Update text fields
const response = await fetch('/api/syndicate/settings/general-info/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    first_name: 'John',
    last_name: 'Doe',
    bio: 'Experienced venture capital manager with 10+ years in early-stage technology investments.',
    link: 'https://extrmallinks.com'
  })
});

const result = await response.json();
console.log(result.message); // "General information updated successfully"
```

### Upload Logo

```javascript
// Upload logo with multipart/form-data
const formData = new FormData();
formData.append('logo', fileInput.files[0]);
formData.append('first_name', 'John');
formData.append('last_name', 'Doe');

const response = await fetch('/api/syndicate/settings/general-info/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${accessToken}`
    // Don't set Content-Type - browser sets it automatically with boundary
  },
  body: formData
});

const result = await response.json();
console.log(result.data.logo); // "/media/syndicate_logos/new_logo.png"
```

### Upload Compliance Documents

```javascript
const formData = new FormData();
formData.append('additional_compliance_policies', fileInput.files[0]);
formData.append('risk_regulatory_attestation', 'true');
formData.append('jurisdictional_compliance_acknowledged', 'true');

const response = await fetch('/api/syndicate/settings/compliance/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});

const result = await response.json();
console.log(result.data.compliance_file_url);
```

---

## Error Responses

### Not Authenticated
```json
{
  "detail": "Authentication credentials were not provided."
}
```
**Status:** 401 Unauthorized

### Wrong Role
```json
{
  "error": "Only users with syndicate role can access this endpoint"
}
```
**Status:** 403 Forbidden

### Profile Not Found
```json
{
  "error": "Syndicate profile not found. Please complete onboarding first."
}
```
**Status:** 404 Not Found

### Validation Error
```json
{
  "success": false,
  "errors": {
    "link": ["Enter a valid URL."]
  }
}
```
**Status:** 400 Bad Request

---

## Settings Navigation Mapping

Based on Figma screens, here's the navigation structure:

| Screen | Endpoint | Method | Purpose |
|--------|----------|--------|---------|
| **35 - General Info** | `/settings/general-info/` | GET, PATCH | First name, last name, bio, link, logo |
| **36 - Team Management** | `/settings/team-management/` | GET | Team members list with roles & permissions |
| **35 - KYB Verification** | `/settings/kyb-verification/` | GET, PATCH | Company legal name, full name, position, documents |
| **37 - Compliance** | `/settings/compliance/` | GET, PATCH | Upload compliance documents, view status |
| Compliance & Accreditation | `/settings/compliance/` | GET, PATCH | Risk attestations, compliance docs |
| Jurisdictional Settings | `/settings/jurisdictional/` | GET, PATCH | Geography compliance settings |
| Portfolio Company Outreach | `/settings/portfolio/` | GET, PATCH | Sectors, LP network access |
| Notifications & Communication | `/settings/notifications/` | GET, PATCH | Email/SMS preferences, 2FA |
| Fee Recipient Setup | `/settings/fee-recipient/` | GET, POST, PATCH, DELETE | Payment recipient configuration |
| **45 - Bank Details** | `/settings/bank-details/` | GET, POST, PATCH, DELETE | Credit cards and bank accounts |

---

## Data Models

### SyndicateProfile Fields

```python
# Settings: General Info
first_name = CharField(max_length=100)
last_name = CharField(max_length=100)
bio = TextField()
link = URLField(max_length=500)
logo = ImageField(upload_to='syndicate_logos/')

# Settings: Compliance
risk_regulatory_attestation = BooleanField()
jurisdictional_compliance_acknowledged = BooleanField()
additional_compliance_policies = FileField(upload_to='syndicate_compliance/')

# Settings: Team Management
enable_role_based_access_controls = BooleanField()

# Settings: Entity Profile
firm_name = CharField(max_length=255)
description = TextField()

# Settings: Portfolio
sectors = ManyToManyField(Sector)
geographies = ManyToManyField(Geography)
enable_platform_lp_access = BooleanField()
existing_lp_count = CharField(choices=LP_NETWORK_CHOICES)
```

---

## Tips for Frontend Integration

1. **File Uploads**: Always use `multipart/form-data` when uploading logo or compliance documents
2. **Separate Endpoints**: Use specific endpoints for each settings section for better performance
3. **Overview Endpoint**: Use `/settings/overview/` to load all settings at once on initial page load
4. **Save Buttons**: Call PATCH endpoints when "Save changes" button is clicked
5. **File Preview**: Display existing logo/documents using the returned URLs
6. **Validation**: Show inline validation errors from the API response
7. **Progress Indicators**: Show loading states during file uploads
8. **Success Messages**: Display success messages from API responses

---

## Summary

The Syndicate Settings APIs provide:
- ✅ Complete profile customization after onboarding
- ✅ General information (name, bio, link, logo)
- ✅ KYB verification data management
- ✅ Compliance document upload and tracking
- ✅ Team management overview (full CRUD to be implemented)
- ✅ Jurisdictional and portfolio settings view
- ✅ User notification preferences
- ✅ File upload support for logo and documents
- ✅ Proper validation and error handling

All endpoints follow REST conventions and return consistent JSON responses! 🎉
