# Investor Onboarding API - Complete Documentation

## Overview

Complete 6-step investor onboarding API matching the Unlocksley platform UI. Includes document upload, identity verification, bank details, and accreditation tracking.

## Base URL
```
/blockchain-backend/api/profiles/
```

## Authentication
All endpoints require JWT authentication:
```
Authorization: Bearer <your_jwt_token>
```

---

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/choices/` | Get all dropdown options |
| POST | `/` | Create investor profile (Step 1) |
| GET | `/my_profile/` | Get authenticated user's profile |
| PATCH | `/{id}/update_step1/` | Update Step 1: Basic Information |
| PATCH | `/{id}/update_step2/` | Update Step 2: KYC / Identity Verification |
| PATCH | `/{id}/update_step3/` | Update Step 3: Bank Details / Payment Setup |
| PATCH | `/{id}/update_step4/` | Update Step 4: Accreditation (Optional) |
| PATCH | `/{id}/update_step5/` | Update Step 5: Accept Agreements |
| GET | `/{id}/final_review/` | Step 6: Final Review |
| POST | `/{id}/submit_application/` | Submit completed application |
| GET | `/{id}/progress/` | Get progress status |

---

## Detailed Endpoint Documentation

### 1. Create Investor Profile (Step 1)

**Endpoint:** `POST /blockchain-backend/api/profiles/`

**Request:**
```json
{
    "full_name": "John Doe",
    "email_address": "john.doe@example.com",
    "phone_number": "+1-000-000-0000",
    "country_of_residence": "United States"
}
```

**Response:**
```json
{
    "id": 1,
    "user": 5,
    "full_name": "John Doe",
    "current_step": 1,
    "step1_completed": true
}
```

---

### 2. Update Step 2: KYC / Identity Verification

**Endpoint:** `PATCH /blockchain-backend/api/profiles/{id}/update_step2/`

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `government_id`: File (PDF, JPG, PNG)
- `date_of_birth`: Date (YYYY-MM-DD)
- `street_address`: String
- `city`: String
- `state_province`: String
- `zip_postal_code`: String
- `country`: String

**JavaScript Example:**
```javascript
const formData = new FormData();
formData.append('government_id', fileInput.files[0]);
formData.append('date_of_birth', '1990-01-15');
formData.append('street_address', '123 Main Street');
formData.append('city', 'New York');
formData.append('state_province', 'New York');
formData.append('zip_postal_code', '10001');
formData.append('country', 'United States');

fetch('/blockchain-backend/api/profiles/1/update_step2/', {
    method: 'PATCH',
    headers: {'Authorization': 'Bearer ' + token},
    body: formData
});
```

---

### 3. Update Step 3: Bank Details / Payment Setup

**Endpoint:** `PATCH /blockchain-backend/api/profiles/{id}/update_step3/`

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `bank_account_number`: String
- `bank_name`: String
- `account_holder_name`: String
- `swift_ifsc_code`: String
- `proof_of_bank_ownership`: File (PDF, JPG)

---

### 4. Update Step 4: Accreditation (Optional)

**Endpoint:** `PATCH /blockchain-backend/api/profiles/{id}/update_step4/`

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `is_accredited_investor`: Boolean
- `meets_local_investment_thresholds`: Boolean
- `proof_of_income_net_worth`: File (optional)

---

### 5. Update Step 5: Accept Agreements

**Endpoint:** `PATCH /blockchain-backend/api/profiles/{id}/update_step5/`

**Request:**
```json
{
    "terms_and_conditions_accepted": true,
    "risk_disclosure_accepted": true,
    "privacy_policy_accepted": true,
    "confirmation_of_true_information": true
}
```

**Note:** All four agreements must be true.

---

### 6. Final Review

**Endpoint:** `GET /blockchain-backend/api/profiles/{id}/final_review/`

Returns complete profile for review before submission.

---

### 7. Submit Application

**Endpoint:** `POST /blockchain-backend/api/profiles/{id}/submit_application/`

**Response:**
```json
{
    "detail": "Application submitted successfully",
    "profile": {
        "application_status": "submitted",
        "application_submitted": true,
        "submitted_at": "2025-11-25T10:30:00Z"
    }
}
```

---

### 8. Get Progress

**Endpoint:** `GET /blockchain-backend/api/profiles/{id}/progress/`

**Response:**
```json
{
    "current_step": 3,
    "total_steps": 6,
    "steps_completed": {
        "step1_basic_info": true,
        "step2_kyc": true,
        "step3_bank_details": false,
        "step4_accreditation": false,
        "step5_agreements": false,
        "step6_submitted": false
    },
    "can_submit": false
}
```

---

## Complete Frontend Flow

```javascript
// 1. Create Profile
const response1 = await fetch('/blockchain-backend/api/profiles/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        full_name: 'John Doe',
        email_address: 'john@example.com',
        phone_number: '+1-555-0000',
        country_of_residence: 'United States'
    })
});
const profile = await response1.json();
const profileId = profile.id;

// 2. Update KYC
const kycData = new FormData();
kycData.append('government_id', govIdFile);
kycData.append('date_of_birth', '1990-01-15');
kycData.append('street_address', '123 Main St');
kycData.append('city', 'New York');
kycData.append('state_province', 'NY');
kycData.append('zip_postal_code', '10001');
kycData.append('country', 'United States');

await fetch(`/blockchain-backend/api/profiles/${profileId}/update_step2/`, {
    method: 'PATCH',
    headers: {'Authorization': `Bearer ${token}`},
    body: kycData
});

// 3. Update Bank Details
const bankData = new FormData();
bankData.append('bank_account_number', '1234567890');
bankData.append('bank_name', 'Chase Bank');
bankData.append('account_holder_name', 'John Doe');
bankData.append('swift_ifsc_code', 'CHASUS33');
bankData.append('proof_of_bank_ownership', bankProofFile);

await fetch(`/blockchain-backend/api/profiles/${profileId}/update_step3/`, {
    method: 'PATCH',
    headers: {'Authorization': `Bearer ${token}`},
    body: bankData
});

// 4. Skip Accreditation (Optional) or Update
// ...

// 5. Accept Agreements
await fetch(`/blockchain-backend/api/profiles/${profileId}/update_step5/`, {
    method: 'PATCH',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        terms_and_conditions_accepted: true,
        risk_disclosure_accepted: true,
        privacy_policy_accepted: true,
        confirmation_of_true_information: true
    })
});

// 6. Get Final Review
const review = await fetch(`/blockchain-backend/api/profiles/${profileId}/final_review/`, {
    headers: {'Authorization': `Bearer ${token}`}
});

// 7. Submit
await fetch(`/blockchain-backend/api/profiles/${profileId}/submit_application/`, {
    method: 'POST',
    headers: {'Authorization': `Bearer ${token}`}
});
```

---

## File Upload Requirements

### Accepted Formats
- **Documents**: PDF, DOCX
- **Images**: JPG, JPEG, PNG, PPTX
- **Max Size**: 5MB per file

### Required Files
1. **Step 2**: Government ID (passport, driver's license)
2. **Step 3**: Proof of bank ownership (bank statement, cancelled check)
3. **Step 4** (Optional): Proof of income/net worth

---

## Validation Rules

### Step Order
- Steps must be completed in order (1 → 2 → 3 → 5 → 6)
- Step 4 is optional
- Cannot skip required steps

### Field Requirements
**Step 1:** All fields required  
**Step 2:** All fields + government_id file required  
**Step 3:** All fields + proof_of_bank_ownership file required  
**Step 4:** Optional  
**Step 5:** All four agreements must be true  

### Submission Requirements
- Steps 1, 2, 3, and 5 must be completed
- Cannot submit twice

---

## Error Handling

### Common Errors

**400 Bad Request - Step Not Complete**
```json
{
    "detail": "Please complete Step 1: Basic Information first"
}
```

**400 Bad Request - Missing Agreement**
```json
{
    "terms_and_conditions_accepted": ["You must accept: terms_and_conditions_accepted"]
}
```

**404 Not Found**
```json
{
    "detail": "Investor profile not found"
}
```

**401 Unauthorized**
```json
{
    "detail": "Authentication credentials were not provided."
}
```

---

## Application Status Flow

```
draft → submitted → under_review → approved / rejected
```

- **draft**: User filling out application
- **submitted**: Application submitted for review
- **under_review**: Admin reviewing
- **approved**: User can start investing
- **rejected**: Application declined

---

## Testing with cURL

```bash
# 1. Create Profile
curl -X POST http://localhost:8000/blockchain-backend/api/profiles/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name":"John Doe","email_address":"john@example.com","phone_number":"+1-555-0000","country_of_residence":"United States"}'

# 2. Update KYC
curl -X PATCH http://localhost:8000/blockchain-backend/api/profiles/1/update_step2/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "government_id=@/path/to/id.pdf" \
  -F "date_of_birth=1990-01-15" \
  -F "street_address=123 Main St" \
  -F "city=New York" \
  -F "state_province=NY" \
  -F "zip_postal_code=10001" \
  -F "country=United States"

# 3. Submit Application
curl -X POST http://localhost:8000/blockchain-backend/api/profiles/1/submit_application/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Dashboard & Portfolio APIs

### Base URL
```
/blockchain-backend/api/
```

### 1. Dashboard Overview

Get complete dashboard overview including KYC status, portfolio summary, recent investments, and notifications.

**Endpoint:** `GET /blockchain-backend/api/dashboard/overview/`

**Response:**
```json
{
    "kyc_status": {
        "status": "approved",
        "submitted_at": "2024-01-15T10:30:00Z",
        "reviewed_at": "2024-01-16T14:20:00Z",
        "reviewer_notes": "All documents verified"
    },
    "portfolio_summary": {
        "total_invested": "500000.00",
        "current_value": "575000.00",
        "unrealized_gain": "75000.00",
        "portfolio_growth_percentage": "15.00",
        "total_investments": 5,
        "active_investments": 4
    },
    "recent_investments": [
        {
            "id": 1,
            "syndicate_name": "Tech Ventures Fund",
            "sector": "technology",
            "investment_type": "syndicate_deal",
            "amount_invested": "100000.00",
            "current_value": "120000.00",
            "status": "active"
        }
    ],
    "notification_summary": {
        "total_count": 15,
        "unread_count": 5,
        "action_required_count": 2
    }
}
```

### 2. Get My Portfolio

Get complete portfolio details with all investments.

**Endpoint:** `GET /blockchain-backend/api/portfolio/my_portfolio/`

**Response:**
```json
{
    "id": 1,
    "total_invested": "500000.00",
    "current_value": "575000.00",
    "unrealized_gain": "75000.00",
    "portfolio_growth_percentage": "15.00",
    "total_investments": 5,
    "active_investments": 4,
    "investments": [
        {
            "id": 1,
            "syndicate_name": "Tech Ventures Fund",
            "sector": "technology",
            "amount_invested": "100000.00",
            "current_value": "120000.00",
            "status": "active"
        }
    ]
}
```

### 3. Get My Investments

Get all user investments with filtering.

**Endpoint:** `GET /blockchain-backend/api/investments/my_investments/`

**Query Parameters:**
- `investment_type`: syndicate_deal, top_syndicate, or invite
- `sector`: technology, healthcare, real_estate, etc.
- `status`: pending, active, completed, cancelled

**Response:**
```json
[
    {
        "id": 1,
        "syndicate_name": "Tech Ventures Fund",
        "sector": "technology",
        "investment_type": "syndicate_deal",
        "amount_invested": "100000.00",
        "current_value": "120000.00",
        "gain_loss": "20000.00",
        "gain_loss_percentage": "20.00",
        "status": "active",
        "investment_date": "2024-01-15"
    }
]
```

### 4. Get My Notifications

Get all user notifications.

**Endpoint:** `GET /blockchain-backend/api/notifications/my_notifications/`

**Query Parameters:**
- `type`: investment, document, transfer, system
- `status`: unread, read, archived
- `priority`: low, medium, high, urgent
- `action_required`: true/false

**Response:**
```json
[
    {
        "id": 1,
        "notification_type": "investment",
        "title": "Investment Opportunity",
        "message": "New syndicate deal available",
        "status": "unread",
        "priority": "high",
        "action_required": true,
        "created_at": "2024-01-20T10:00:00Z"
    }
]
```

### 5. Mark Notification as Read

**Endpoint:** `POST /blockchain-backend/api/notifications/{id}/mark_read/`

### 6. Mark All Notifications as Read

**Endpoint:** `POST /blockchain-backend/api/notifications/mark_all_read/`

**Response:**
```json
{
    "message": "All notifications marked as read",
    "count": 5
}
```

### 7. Get Notification Statistics

**Endpoint:** `GET /blockchain-backend/api/notifications/stats/`

**Response:**
```json
{
    "total": 15,
    "unread": 5,
    "action_required": 2,
    "by_type": {
        "investment": 6,
        "document": 4,
        "transfer": 3,
        "system": 2
    }
}
```

---

## Notes

- File uploads automatically stored in `/media/investor_documents/{user_id}/`
- All dates in ISO 8601 format (YYYY-MM-DD)
- Phone numbers can include country codes
- Admins can manage applications via Django Admin interface
- Portfolio values are automatically recalculated
- Notifications support filtering by type, status, and priority

For support, refer to main documentation or contact the development team.
