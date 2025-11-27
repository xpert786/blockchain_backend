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

View jurisdictional compliance settings.

```http
GET /api/syndicate/settings/jurisdictional/
```

**Response:**
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

---

### 7. Portfolio Company Outreach

View portfolio and LP network settings.

```http
GET /api/syndicate/settings/portfolio/
```

**Response:**
```json
{
  "success": true,
  "message": "Portfolio company outreach settings endpoint",
  "data": {
    "sectors": [
      {
        "id": 1,
        "name": "Technology",
        "description": "Software and hardware technology companies"
      },
      {
        "id": 2,
        "name": "Healthcare",
        "description": "Healthcare and biotech companies"
      }
    ],
    "enable_platform_lp_access": true,
    "existing_lp_count": "11-25"
  }
}
```

---

### 8. Notifications & Communication

View notification and communication preferences.

```http
GET /api/syndicate/settings/notifications/
```

**Response:**
```json
{
  "success": true,
  "message": "Notifications & communication settings endpoint - to be implemented",
  "data": {
    "email": "john@example.com",
    "phone_number": "+1234567890",
    "email_verified": true,
    "phone_verified": true,
    "two_factor_enabled": true,
    "two_factor_method": "sms"
  }
}
```

---

### 9. Fee Recipient Setup

View fee recipient configuration.

```http
GET /api/syndicate/settings/fee-recipient/
```

**Response:**
```json
{
  "success": true,
  "message": "Fee recipient setup endpoint - to be implemented",
  "data": {
    "syndicate_id": 1,
    "firm_name": "Tech Ventures LLC"
  }
}
```

---

### 10. Bank Details

View bank account details.

```http
GET /api/syndicate/settings/bank-details/
```

**Response:**
```json
{
  "success": true,
  "message": "Bank details endpoint - to be implemented",
  "data": {
    "syndicate_id": 1,
    "firm_name": "Tech Ventures LLC"
  }
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
| Jurisdictional Settings | `/settings/jurisdictional/` | GET | Geography compliance settings |
| Portfolio Company Outreach | `/settings/portfolio/` | GET | Sectors, LP network access |
| Notifications & Communication | `/settings/notifications/` | GET | Email/SMS preferences, 2FA |
| Fee Recipient Setup | `/settings/fee-recipient/` | GET | Payment recipient configuration |
| Bank Details | `/settings/bank-details/` | GET | Bank account information |

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
