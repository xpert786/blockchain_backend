# KYB (Know Your Business) Verification API Documentation

Complete API documentation for KYB verification in syndicate settings.

## Table of Contents
1. [Overview](#overview)
2. [Endpoint](#endpoint)
3. [Field Reference](#field-reference)
4. [Request/Response Examples](#requestresponse-examples)
5. [Validation Rules](#validation-rules)
6. [File Upload Guidelines](#file-upload-guidelines)
7. [Testing Guide](#testing-guide)

---

## Overview

The KYB Verification API allows syndicates to complete their Know Your Business verification by providing company information, contact details, document uploads, and compliance confirmations.

### Key Features
- Company legal information
- Document uploads (COI, bank statements, proof of address, beneficiary documents)
- Address information
- Signing preferences
- Contact information
- Terms agreement

### Base URL
```
/api/syndicate/settings/kyb-verification/
```

### Authentication
All requests require JWT authentication:
```
Authorization: Bearer <your_jwt_token>
```

---

## Endpoint

### Get KYB Verification Data

**Method:** `GET`

**URL:** `/api/syndicate/settings/kyb-verification/`

**Description:** Retrieve current KYB verification data for the authenticated syndicate.

**Response:**
```json
{
    "success": true,
    "data": {
        "company_legal_name": "Acme Ventures LLC",
        "kyb_full_name": "John Doe",
        "kyb_position": "Managing Partner",
        "certificate_of_incorporation": "/media/kyb_documents/coi/certificate.pdf",
        "certificate_of_incorporation_url": "http://localhost:8000/media/kyb_documents/coi/certificate.pdf",
        "company_bank_statement": "/media/kyb_documents/bank_statements/statement.pdf",
        "company_bank_statement_url": "http://localhost:8000/media/kyb_documents/bank_statements/statement.pdf",
        "address_line_1": "123 Main Street",
        "address_line_2": "Suite 100",
        "town_city": "New York",
        "postal_code": "10001",
        "country": "United States",
        "company_proof_of_address": "/media/kyb_documents/proof_of_address/utility_bill.pdf",
        "company_proof_of_address_url": "http://localhost:8000/media/kyb_documents/proof_of_address/utility_bill.pdf",
        "beneficiary_owner_identity_document": "/media/kyb_documents/beneficiary_identity/passport.pdf",
        "beneficiary_owner_identity_document_url": "http://localhost:8000/media/kyb_documents/beneficiary_identity/passport.pdf",
        "beneficiary_owner_proof_of_address": "/media/kyb_documents/beneficiary_address/proof.pdf",
        "beneficiary_owner_proof_of_address_url": "http://localhost:8000/media/kyb_documents/beneficiary_address/proof.pdf",
        "sse_eligibility": "hidden",
        "is_notary_wet_signing": "no",
        "will_require_unlockley": "no",
        "investee_company_contact_number": "+1-555-0123",
        "investee_company_email": "contact@acmeventures.com",
        "agree_to_investee_terms": false,
        "kyb_verification_completed": false,
        "kyb_verification_submitted_at": null
    }
}
```

---

### Update KYB Verification Data

**Method:** `PATCH`

**URL:** `/api/syndicate/settings/kyb-verification/`

**Description:** Update KYB verification data. Supports partial updates and file uploads.

**Content-Type:** `multipart/form-data` (when uploading files) or `application/json`

**Request Body (JSON example):**
```json
{
    "company_legal_name": "Acme Ventures LLC",
    "kyb_full_name": "John Doe",
    "kyb_position": "Managing Partner",
    "address_line_1": "123 Main Street",
    "address_line_2": "Suite 100",
    "town_city": "New York",
    "postal_code": "10001",
    "country": "United States",
    "sse_eligibility": "yes",
    "is_notary_wet_signing": "no",
    "will_require_unlockley": "no",
    "investee_company_contact_number": "+1-555-0123",
    "investee_company_email": "contact@acmeventures.com",
    "agree_to_investee_terms": true
}
```

**Request Body (with file uploads using multipart/form-data):**
```
company_legal_name: "Acme Ventures LLC"
kyb_full_name: "John Doe"
kyb_position: "Managing Partner"
certificate_of_incorporation: [binary file data]
company_bank_statement: [binary file data]
address_line_1: "123 Main Street"
town_city: "New York"
postal_code: "10001"
country: "United States"
company_proof_of_address: [binary file data]
beneficiary_owner_identity_document: [binary file data]
beneficiary_owner_proof_of_address: [binary file data]
investee_company_email: "contact@acmeventures.com"
agree_to_investee_terms: true
```

**Response:**
```json
{
    "success": true,
    "message": "KYB verification data updated successfully",
    "data": {
        "company_legal_name": "Acme Ventures LLC",
        "kyb_full_name": "John Doe",
        "kyb_position": "Managing Partner",
        "certificate_of_incorporation": "/media/kyb_documents/coi/certificate.pdf",
        "certificate_of_incorporation_url": "http://localhost:8000/media/kyb_documents/coi/certificate.pdf",
        ...
    }
}
```

**Error Response (400 Bad Request):**
```json
{
    "success": false,
    "errors": {
        "company_legal_name": ["This field is required."],
        "agree_to_investee_terms": ["You must agree to investee terms to complete KYB verification"]
    }
}
```

---

## Field Reference

### Company Information

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `company_legal_name` | String (255) | Yes* | Legal name of the company |
| `kyb_full_name` | String (255) | Yes* | Full name of the person completing KYB |
| `kyb_position` | String (150) | Yes* | Position/title in the company |

### Document Uploads

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `certificate_of_incorporation` | File | No | Company Certificate of Incorporation |
| `company_bank_statement` | File | No | Bank statement of the account to receive investments |
| `company_proof_of_address` | File | No | Proof of company address |
| `beneficiary_owner_identity_document` | File | No | Beneficiary owner identity document |
| `beneficiary_owner_proof_of_address` | File | No | Beneficiary owner proof of address |

**File URL Fields (Read-only):**
- `certificate_of_incorporation_url`
- `company_bank_statement_url`
- `company_proof_of_address_url`
- `beneficiary_owner_identity_document_url`
- `beneficiary_owner_proof_of_address_url`

### Address Information

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `address_line_1` | String (255) | Yes* | Primary address line |
| `address_line_2` | String (255) | No | Secondary address line |
| `town_city` | String (150) | Yes* | Town or city |
| `postal_code` | String (20) | Yes* | Postal/ZIP code |
| `country` | String (100) | Yes* | Country |

### S/SE Eligibility

| Field | Type | Required | Default | Options | Description |
|-------|------|----------|---------|---------|-------------|
| `sse_eligibility` | Choice | No | 'hidden' | 'hidden', 'yes', 'no' | S/SE eligibility status |

### Signing Requirements

| Field | Type | Required | Default | Options | Description |
|-------|------|----------|---------|---------|-------------|
| `is_notary_wet_signing` | Choice | No | 'no' | 'yes', 'no' | Is notary/wet signing of document required at close or conversion of share |
| `will_require_unlockley` | Choice | No | 'no' | 'yes', 'no' | Will you require Unlockley to sign a deed of adherence to close the deal |

### Contact Information

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `investee_company_contact_number` | String (20) | No | Contact phone number |
| `investee_company_email` | Email | Yes* | Contact email address |

### Agreement & Status

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `agree_to_investee_terms` | Boolean | Yes* | false | Agreement to investee terms |
| `kyb_verification_completed` | Boolean | No | false | Mark KYB verification as completed |
| `kyb_verification_submitted_at` | DateTime | Read-only | null | Timestamp when KYB was completed |

**\* Required when marking `kyb_verification_completed` as `true`**

---

## Request/Response Examples

### Example 1: Update Basic Information

**Request:**
```bash
curl -X PATCH http://localhost:8000/api/syndicate/settings/kyb-verification/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_legal_name": "Acme Ventures LLC",
    "kyb_full_name": "John Doe",
    "kyb_position": "Managing Partner",
    "address_line_1": "123 Main Street",
    "town_city": "New York",
    "postal_code": "10001",
    "country": "United States"
  }'
```

**Response:**
```json
{
    "success": true,
    "message": "KYB verification data updated successfully",
    "data": {
        "company_legal_name": "Acme Ventures LLC",
        "kyb_full_name": "John Doe",
        "kyb_position": "Managing Partner",
        "address_line_1": "123 Main Street",
        "address_line_2": null,
        "town_city": "New York",
        "postal_code": "10001",
        "country": "United States",
        ...
    }
}
```

---

### Example 2: Upload Certificate of Incorporation

**Request:**
```bash
curl -X PATCH http://localhost:8000/api/syndicate/settings/kyb-verification/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "certificate_of_incorporation=@/path/to/certificate.pdf"
```

**Response:**
```json
{
    "success": true,
    "message": "KYB verification data updated successfully",
    "data": {
        "certificate_of_incorporation": "/media/kyb_documents/coi/certificate.pdf",
        "certificate_of_incorporation_url": "http://localhost:8000/media/kyb_documents/coi/certificate.pdf",
        ...
    }
}
```

---

### Example 3: Complete KYB Verification

**Request:**
```bash
curl -X PATCH http://localhost:8000/api/syndicate/settings/kyb-verification/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agree_to_investee_terms": true,
    "kyb_verification_completed": true
  }'
```

**Response (Success):**
```json
{
    "success": true,
    "message": "KYB verification data updated successfully",
    "data": {
        "company_legal_name": "Acme Ventures LLC",
        "kyb_full_name": "John Doe",
        "kyb_position": "Managing Partner",
        "address_line_1": "123 Main Street",
        "town_city": "New York",
        "postal_code": "10001",
        "country": "United States",
        "investee_company_email": "contact@acmeventures.com",
        "agree_to_investee_terms": true,
        "kyb_verification_completed": true,
        "kyb_verification_submitted_at": "2024-01-15T14:30:00Z"
    }
}
```

**Response (Error - Missing Required Fields):**
```json
{
    "success": false,
    "errors": {
        "error": "Required fields missing: company_legal_name, kyb_full_name, kyb_position, address_line_1, town_city, postal_code, country, investee_company_email"
    }
}
```

---

### Example 4: Upload Multiple Documents

**Request:**
```bash
curl -X PATCH http://localhost:8000/api/syndicate/settings/kyb-verification/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "certificate_of_incorporation=@certificate.pdf" \
  -F "company_bank_statement=@bank_statement.pdf" \
  -F "company_proof_of_address=@utility_bill.pdf" \
  -F "beneficiary_owner_identity_document=@passport.pdf" \
  -F "beneficiary_owner_proof_of_address=@address_proof.pdf"
```

**Response:**
```json
{
    "success": true,
    "message": "KYB verification data updated successfully",
    "data": {
        "certificate_of_incorporation": "/media/kyb_documents/coi/certificate.pdf",
        "certificate_of_incorporation_url": "http://localhost:8000/media/kyb_documents/coi/certificate.pdf",
        "company_bank_statement": "/media/kyb_documents/bank_statements/bank_statement.pdf",
        "company_bank_statement_url": "http://localhost:8000/media/kyb_documents/bank_statements/bank_statement.pdf",
        "company_proof_of_address": "/media/kyb_documents/proof_of_address/utility_bill.pdf",
        "company_proof_of_address_url": "http://localhost:8000/media/kyb_documents/proof_of_address/utility_bill.pdf",
        "beneficiary_owner_identity_document": "/media/kyb_documents/beneficiary_identity/passport.pdf",
        "beneficiary_owner_identity_document_url": "http://localhost:8000/media/kyb_documents/beneficiary_identity/passport.pdf",
        "beneficiary_owner_proof_of_address": "/media/kyb_documents/beneficiary_address/address_proof.pdf",
        "beneficiary_owner_proof_of_address_url": "http://localhost:8000/media/kyb_documents/beneficiary_address/address_proof.pdf",
        ...
    }
}
```

---

## Validation Rules

### Completing KYB Verification

When setting `kyb_verification_completed` to `true`, the following fields are **required**:

1. `company_legal_name`
2. `kyb_full_name`
3. `kyb_position`
4. `address_line_1`
5. `town_city`
6. `postal_code`
7. `country`
8. `investee_company_email`
9. `agree_to_investee_terms` (must be `true`)

### Auto-Submission Timestamp

When `kyb_verification_completed` is set to `true` for the first time:
- `kyb_verification_submitted_at` is automatically set to the current timestamp
- This field is read-only and cannot be manually set

### Partial Updates

- All fields are optional for partial updates
- You can update any subset of fields without affecting others
- File uploads will replace existing files

---

## File Upload Guidelines

### Supported File Types
- PDF (`.pdf`)
- DOCX (`.docx`)
- Images: JPEG (`.jpg`, `.jpeg`), PNG (`.png`)

### File Size Limits
- Maximum file size: **25 MB** per file
- For larger files, consider compressing or splitting into multiple documents

### File Storage Structure
```
media/
└── kyb_documents/
    ├── coi/                        # Certificate of Incorporation
    ├── bank_statements/            # Bank statements
    ├── proof_of_address/          # Company proof of address
    ├── beneficiary_identity/      # Beneficiary owner identity docs
    └── beneficiary_address/       # Beneficiary owner address proof
```

### Upload Methods

#### Method 1: Using multipart/form-data
```bash
curl -X PATCH http://localhost:8000/api/syndicate/settings/kyb-verification/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "certificate_of_incorporation=@certificate.pdf" \
  -F "company_legal_name=Acme Ventures LLC"
```

#### Method 2: Using JavaScript FormData
```javascript
const formData = new FormData();
formData.append('certificate_of_incorporation', fileInput.files[0]);
formData.append('company_legal_name', 'Acme Ventures LLC');

fetch('/api/syndicate/settings/kyb-verification/', {
    method: 'PATCH',
    headers: {
        'Authorization': `Bearer ${token}`
    },
    body: formData
});
```

---

## Testing Guide

### Test Checklist

- [ ] **Get KYB data** - `GET` request returns current data
- [ ] **Update company info** - Update company_legal_name, kyb_full_name, kyb_position
- [ ] **Update address** - Update all address fields
- [ ] **Upload COI** - Upload certificate_of_incorporation
- [ ] **Upload bank statement** - Upload company_bank_statement
- [ ] **Upload proof of address** - Upload company_proof_of_address
- [ ] **Upload beneficiary docs** - Upload beneficiary identity and address proof
- [ ] **Set SSE eligibility** - Test 'hidden', 'yes', 'no' options
- [ ] **Set signing options** - Test is_notary_wet_signing and will_require_unlockley
- [ ] **Update contact info** - Update phone and email
- [ ] **Agree to terms** - Set agree_to_investee_terms to true
- [ ] **Complete verification** - Mark kyb_verification_completed as true
- [ ] **Validation errors** - Try completing without required fields
- [ ] **File size validation** - Test with files > 25MB (should fail)
- [ ] **Partial updates** - Update only specific fields

### Sample Test Data

```json
{
    "company_legal_name": "Test Ventures LLC",
    "kyb_full_name": "Jane Smith",
    "kyb_position": "Chief Executive Officer",
    "address_line_1": "456 Tech Boulevard",
    "address_line_2": "Floor 5",
    "town_city": "San Francisco",
    "postal_code": "94105",
    "country": "United States",
    "sse_eligibility": "yes",
    "is_notary_wet_signing": "no",
    "will_require_unlockley": "yes",
    "investee_company_contact_number": "+1-415-555-0199",
    "investee_company_email": "admin@testventures.com",
    "agree_to_investee_terms": true
}
```

---

## Integration with Frontend (Screen 35)

### Form Fields Mapping

Based on the Figma screens, here's how API fields map to UI:

| UI Label | API Field |
|----------|-----------|
| Company Legal Name * | `company_legal_name` |
| Your Full Name * | `kyb_full_name` |
| Your Position | `kyb_position` |
| Company certificate of incorporation | `certificate_of_incorporation` (file upload) |
| Company Bank statement of the account you wish to receive | `company_bank_statement` (file upload) |
| Address Line 1 | `address_line_1` |
| Address Line 2 | `address_line_2` |
| Town/City | `town_city` |
| Postal Code/ Zip Code | `postal_code` |
| Country | `country` |
| Company Proof Of Address | `company_proof_of_address` (file upload) |
| Beneficiary Owner Identity Document | `beneficiary_owner_identity_document` (file upload) |
| Beneficiary Owner Proof Of Address | `beneficiary_owner_proof_of_address` (file upload) |
| S/SE Eligibility | `sse_eligibility` (dropdown: Hidden/Yes/No) |
| Is Notary / Wet signing Of Document At Close Or Conversion Of Share | `is_notary_wet_signing` (Yes/No) |
| Will You Required Unlockley To Sign a Deed Of adherence in Order To Close The Deal | `will_require_unlockley` (Yes/No) |
| Investee Company Contact Number | `investee_company_contact_number` |
| Investee Company Email | `investee_company_email` |
| I Agree To Investee Terms | `agree_to_investee_terms` (checkbox) |

### Sample React/JavaScript Integration

```javascript
// Fetch KYB data
async function getKYBData() {
    const response = await fetch('/api/syndicate/settings/kyb-verification/', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    const result = await response.json();
    return result.data;
}

// Update KYB data with file uploads
async function updateKYBData(formData) {
    const response = await fetch('/api/syndicate/settings/kyb-verification/', {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData // FormData object with files and fields
    });
    return await response.json();
}

// Complete KYB verification
async function completeKYB() {
    const response = await fetch('/api/syndicate/settings/kyb-verification/', {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            agree_to_investee_terms: true,
            kyb_verification_completed: true
        })
    });
    return await response.json();
}
```

---

## Error Codes

| HTTP Status | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Validation errors |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - User is not a syndicate |
| 404 | Not Found - Syndicate profile not found |

---

## Notes

- All file uploads are optional but recommended for verification
- Documents can be uploaded individually or all at once
- Once `kyb_verification_completed` is set to `true`, the `kyb_verification_submitted_at` timestamp is automatically recorded
- Partial updates are supported - you don't need to send all fields every time
- File URLs are automatically generated and returned in responses
- Empty/null values are acceptable for optional fields

---

## Support

For technical issues or questions about the KYB Verification API, contact the development team.
