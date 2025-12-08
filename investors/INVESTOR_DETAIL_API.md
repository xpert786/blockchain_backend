# Investor Detail API Documentation

## Overview
Complete investor information and portfolio management endpoints providing detailed insights into individual investor profiles, investment history, KYC status, and risk profiles.

## Endpoints

### 1. Get Investor Detail

**Endpoint:** `GET /api/investors/{investor_id}/`

**Description:** Get comprehensive information about a specific investor including profile data, investment metrics, KYC status, and contact information.

**Authentication:** Required (JWT Bearer Token)

**Permissions:** 
- Investor can view their own profile
- Admin/Staff can view any investor profile

**URL Parameters:**
- `investor_id` (integer, required): The ID of the investor profile

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "investor_id": 1,
    "user_id": 5,
    "header": {
      "full_name": "Michael Investor",
      "email": "m.investor@example.com",
      "phone": "+1 (555) 123-4567",
      "kyc_status": "approved",
      "kyc_status_label": "Approved",
      "is_accredited": true
    },
    "investment_metrics": {
      "investment_amount": 50000,
      "current_value": 57500,
      "ownership_percentage": 3,
      "return_percentage": 15,
      "currency": "USD"
    },
    "profile": {
      "full_name": "Michael Investor",
      "nationality": "United States",
      "email_address": "m.investor@example.com",
      "kyc_status": "approved",
      "kyc_status_label": "Approved",
      "kyc_approved": true
    },
    "contact_info": {
      "phone_number": "+1 (555) 123-4567",
      "email": "m.investor@example.com",
      "country": "United States"
    },
    "kyc_accreditation": {
      "full_legal_name": "Michael James Investor",
      "legal_place_of_residence": "New York, USA",
      "date_of_birth": "1980-06-15",
      "investor_type": "individual",
      "investor_type_label": "Individual Investor",
      "is_accredited_investor": true,
      "accreditation_method": "net_worth",
      "meets_local_thresholds": true,
      "application_status": "approved",
      "application_submitted": true,
      "submitted_at": "2024-01-15T10:30:00Z"
    },
    "residential_address": {
      "street_address": "123 Investment Ave",
      "city": "New York",
      "state_province": "NY",
      "zip_postal_code": "10001",
      "country": "United States"
    },
    "payment_details": {
      "bank_name": "Chase Bank",
      "account_holder_name": "Michael Investor",
      "account_number": "****1234",
      "swift_ifsc_code": "CHASUS33",
      "proof_of_ownership_submitted": true
    },
    "documents": {
      "government_id_submitted": true,
      "proof_of_income_submitted": true,
      "proof_of_bank_ownership_submitted": true
    },
    "agreements": {
      "terms_and_conditions_accepted": true,
      "risk_disclosure_accepted": true,
      "privacy_policy_accepted": true,
      "confirmation_accepted": true,
      "all_accepted": true
    },
    "risk_profile": {
      "investor_type": "individual",
      "investor_type_label": "Individual Investor",
      "is_accredited": true
    }
  }
}
```

**Error Responses:**
- `403 Forbidden`: No permission to view this investor
- `404 Not Found`: Investor not found

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/investors/1/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

---

### 2. Get Investor Investments

**Endpoint:** `GET /api/investors/{investor_id}/investments/`

**Description:** Retrieve investment history and portfolio details for an investor, including all SPVs they're invested in with their current values and returns.

**Authentication:** Required (JWT Bearer Token)

**Permissions:**
- Investor can view their own investments
- Admin/Staff can view any investor's investments

**URL Parameters:**
- `investor_id` (integer, required): The ID of the investor profile

**Query Parameters:**
- `page` (integer, optional): Page number for pagination (default: 1)
- `page_size` (integer, optional): Number of items per page (default: 10)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "investor_id": 1,
    "investor_name": "Michael Investor",
    "portfolio_summary": {
      "total_invested": 150000,
      "total_current_value": 157500,
      "total_return": 7500,
      "total_return_percentage": 5.0,
      "number_of_investments": 3,
      "average_return_percentage": 5.0
    },
    "investments": [
      {
        "spv_id": 1,
        "spv_name": "Tech Startup Fund Q4 2024",
        "investment_amount": 50000,
        "current_value": 57500,
        "ownership_percentage": 3,
        "return_percentage": 15,
        "investment_date": "2024-09-28",
        "status": "active",
        "portfolio_company": "TechStartup Inc",
        "round": "Series A",
        "stage": "Series A"
      },
      {
        "spv_id": 2,
        "spv_name": "Real Estate Opportunity",
        "investment_amount": 50000,
        "current_value": 50000,
        "ownership_percentage": 25,
        "return_percentage": 0,
        "investment_date": "2024-02-15",
        "status": "active",
        "portfolio_company": "Real Estate Inc",
        "round": "Series B",
        "stage": "Growth"
      },
      {
        "spv_id": 3,
        "spv_name": "Healthcare Innovation",
        "investment_amount": 50000,
        "current_value": 50000,
        "ownership_percentage": 25,
        "return_percentage": 0,
        "investment_date": "2024-11-20",
        "status": "active",
        "portfolio_company": "HealthTech Inc",
        "round": "Seed",
        "stage": "Early Stage"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 1,
      "page_size": 10,
      "total_count": 3
    }
  }
}
```

**Error Responses:**
- `403 Forbidden`: No permission to view this investor's investments
- `404 Not Found`: Investor not found

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/investors/1/investments/?page=1&page_size=10" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

---

### 3. Get Investor KYC Status

**Endpoint:** `GET /api/investors/{investor_id}/kyc-status/`

**Description:** Get detailed KYC/Know Your Customer verification status including application status, document submissions, agreement acceptances, and compliance checklist.

**Authentication:** Required (JWT Bearer Token)

**Permissions:**
- Investor can view their own KYC status
- Admin/Staff can view any investor's KYC status

**URL Parameters:**
- `investor_id` (integer, required): The ID of the investor profile

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "investor_id": 1,
    "investor_name": "Michael Investor",
    "application_status": {
      "current_status": "approved",
      "status_label": "Approved",
      "submitted": true,
      "submitted_at": "2024-01-15T10:30:00Z",
      "is_approved": true
    },
    "accreditation": {
      "is_accredited_investor": true,
      "investor_type": "individual",
      "investor_type_label": "Individual Investor",
      "accreditation_method": "net_worth",
      "accreditation_method_label": "Net Worth",
      "meets_local_thresholds": true
    },
    "agreements": {
      "terms_and_conditions": {
        "accepted": true,
        "label": "Terms & Conditions"
      },
      "risk_disclosure": {
        "accepted": true,
        "label": "Risk Disclosure"
      },
      "privacy_policy": {
        "accepted": true,
        "label": "Privacy Policy"
      },
      "confirmation_of_information": {
        "accepted": true,
        "label": "Confirmation of True Information"
      },
      "all_agreements_accepted": true
    },
    "documents": {
      "government_id": {
        "submitted": true,
        "label": "Government-Issued ID"
      },
      "proof_of_income_net_worth": {
        "submitted": true,
        "label": "Proof of Income/Net Worth"
      },
      "proof_of_bank_ownership": {
        "submitted": true,
        "label": "Proof of Bank Ownership"
      },
      "all_documents_submitted": true
    },
    "completion_checklist": [
      {
        "step": 1,
        "title": "Basic Information",
        "completed": true,
        "items": [
          {
            "label": "Full Name",
            "completed": true
          },
          {
            "label": "Email",
            "completed": true
          },
          {
            "label": "Phone",
            "completed": true
          }
        ]
      },
      {
        "step": 2,
        "title": "KYC / Identity Verification",
        "completed": true,
        "items": [
          {
            "label": "Government ID",
            "completed": true
          },
          {
            "label": "Date of Birth",
            "completed": true
          }
        ]
      },
      {
        "step": 3,
        "title": "Bank Details",
        "completed": true,
        "items": [
          {
            "label": "Bank Name",
            "completed": true
          },
          {
            "label": "Account Details",
            "completed": true
          }
        ]
      },
      {
        "step": 4,
        "title": "Accreditation",
        "completed": true,
        "items": [
          {
            "label": "Accreditation Verified",
            "completed": true
          },
          {
            "label": "Proof Submitted",
            "completed": true
          }
        ]
      },
      {
        "step": 5,
        "title": "Agreements",
        "completed": true,
        "items": [
          {
            "label": "Terms & Conditions",
            "completed": true
          },
          {
            "label": "Risk Disclosure",
            "completed": true
          },
          {
            "label": "Privacy Policy",
            "completed": true
          }
        ]
      }
    ]
  }
}
```

**Error Responses:**
- `403 Forbidden`: No permission to view this investor's KYC status
- `404 Not Found`: Investor not found

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/investors/1/kyc-status/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

---

### 4. Get Investor Risk Profile

**Endpoint:** `GET /api/investors/{investor_id}/risk-profile/`

**Description:** Retrieve investor's risk profile, investment preferences, accreditation status, and compliance information.

**Authentication:** Required (JWT Bearer Token)

**Permissions:**
- Investor can view their own risk profile
- Admin/Staff can view any investor's risk profile

**URL Parameters:**
- `investor_id` (integer, required): The ID of the investor profile

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "investor_id": 1,
    "investor_name": "Michael Investor",
    "risk_profile": {
      "investor_type": "individual",
      "investor_type_label": "Individual Investor",
      "is_accredited": true,
      "accreditation_status": "Net Worth"
    },
    "investment_details": {
      "full_legal_name": "Michael James Investor",
      "legal_place_of_residence": "New York, USA",
      "country_of_residence": "United States",
      "meets_local_thresholds": true
    },
    "compliance": {
      "terms_accepted": true,
      "risk_acknowledged": true,
      "privacy_agreed": true,
      "information_verified": true,
      "all_compliance_complete": true
    }
  }
}
```

**Error Responses:**
- `403 Forbidden`: No permission to view this investor's risk profile
- `404 Not Found`: Investor not found

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/investors/1/risk-profile/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

---

## Authentication

All endpoints require JWT Bearer token authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Response Format

All endpoints follow the standard response format:

```json
{
  "success": true,
  "message": "Optional message",
  "data": {
    // Endpoint-specific data
  }
}
```

## Error Handling

### Common Error Responses

**403 Forbidden:**
```json
{
  "error": "You do not have permission to access this investor profile"
}
```

**404 Not Found:**
```json
{
  "error": "Not found."
}
```

## Implementation Notes

### Data Calculations
- **Investment Amount**: Total amount invested by investor
- **Current Value**: Current valuation of investment
- **Ownership Percentage**: Investor's ownership stake (%)
- **Return Percentage**: Gain/Loss on investment (%)
- **Total Return**: Current Value - Investment Amount

### KYC Status Levels
- `draft`: Profile not yet submitted
- `submitted`: Awaiting review
- `under_review`: Being reviewed by compliance
- `approved`: KYC approved
- `rejected`: KYC rejected

### Investor Types
- `individual`: Individual investor
- `institutional`: Institutional investor (fund, corporation, etc.)
- `accredited`: Accredited individual investor

### Accreditation Methods
- `net_worth`: Accredited by net worth
- `income`: Accredited by income
- `professional`: Accredited by professional credentials

### Status Codes
- `200 OK`: Successful GET request
- `201 Created`: Successful POST request
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid request parameters
- `403 Forbidden`: No permission to access resource
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Usage Examples

### Example 1: Get Complete Investor Profile
```bash
curl -X GET "http://localhost:8000/api/investors/1/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

### Example 2: Get Investor's Investment Portfolio
```bash
curl -X GET "http://localhost:8000/api/investors/1/investments/?page=1&page_size=20" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

### Example 3: Check KYC Approval Status
```bash
curl -X GET "http://localhost:8000/api/investors/1/kyc-status/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

### Example 4: Get Risk Profile Information
```bash
curl -X GET "http://localhost:8000/api/investors/1/risk-profile/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

## Permission Rules

| Endpoint | Self Access | Admin Access |
|----------|------------|-------------|
| Get Investor Detail | ✅ | ✅ |
| Get Investor Investments | ✅ | ✅ |
| Get KYC Status | ✅ | ✅ |
| Get Risk Profile | ✅ | ✅ |

## Related Endpoints

- Syndicate Settings: `/api/syndicate-settings/`
- SPV Details: `/api/spv/{id}/details/`
- SPV Investors: `/api/spv/{id}/investors/`

## Field Definitions

### Investor Status Fields
- **application_status**: KYC application status (draft, submitted, under_review, approved, rejected)
- **kyc_status**: Same as application_status, short form
- **is_accredited_investor**: Boolean indicating accredited investor status

### Investment Metric Fields
- **investment_amount**: USD amount invested
- **current_value**: Current USD valuation
- **ownership_percentage**: Ownership stake in the deal (0-100)
- **return_percentage**: Return on investment (negative for losses)

### Document Fields
- **government_id**: Upload of government-issued ID
- **proof_of_income_net_worth**: Documentation proving income or net worth
- **proof_of_bank_ownership**: Bank account verification document

### Agreement Fields
- **terms_and_conditions_accepted**: Accepted platform T&Cs
- **risk_disclosure_accepted**: Acknowledged investment risks
- **privacy_policy_accepted**: Accepted privacy policy
- **confirmation_of_true_information**: Confirmed all information is accurate

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12-20 | Initial release with 4 endpoints |
