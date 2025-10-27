# Syndicate Onboarding API - Postman Test Bodies

This guide provides complete request bodies for testing the multi-step syndicate onboarding process in Postman.

## Base URL
```
http://192.168.0.146:8000/api/onboarding/
```

## Step 1: Lead Info
**POST** `/api/onboarding/step1_lead_info/`

**Content-Type:** `application/json`

### Request Body:
```json
{
    "username": "john_manager",
    "email": "john@techventures.com",
    "password": "securepass123",
    "password2": "securepass123",
    "first_name": "John",
    "last_name": "Manager",
    "accredited": "Yes",
    "syndicate_name": "Tech Ventures Syndicate",
    "description": "A syndicate focused on early-stage technology investments, specializing in AI, blockchain, and SaaS companies.",
    "sector_ids": [1, 2, 3],
    "geography_ids": [1, 2, 4],
    "lp_network_count": "We have a network of 50+ accredited investors including angel investors, VCs, and family offices",
    "enable_lp_network": "Yes"
}
```

### Expected Response (201):
```json
{
    "success": true,
    "message": "Step 1 completed successfully",
    "user_id": 39,
    "syndicate_id": 3,
    "next_step": "step2_entity_profile"
}
```

---

## Step 2: Entity Profile
**POST** `/api/onboarding/step2_entity_profile/`

**Content-Type:** `application/json`

### Request Body:
```json
{
    "syndicate_id": 3,
    "firm_name": "Tech Ventures LLC",
    "description": "Tech Ventures LLC is a leading syndicate focused on early-stage technology investments. We specialize in identifying and supporting innovative startups in AI, blockchain, and SaaS sectors.",
    "team_member": "John Manager (Managing Partner), Sarah Smith (Investment Analyst), Mike Johnson (Legal Counsel), Lisa Chen (Due Diligence Specialist)"
}
```

### Expected Response (200):
```json
{
    "success": true,
    "message": "Step 2 completed successfully",
    "syndicate_id": 3,
    "next_step": "step3_kyb_verification"
}
```

---

## Step 3: KYB Verification
**POST** `/api/onboarding/step3_kyb_verification/`

**Content-Type:** `application/json`

### Request Body:
```json
{
    "syndicate_id": 3,
    "company_legal_name": "Tech Ventures LLC",
    "contact_name": "John Manager",
    "contact_position": "Managing Partner",
    "address_1": "123 Silicon Valley Blvd",
    "address_2": "Suite 456",
    "city": "San Francisco",
    "postal_code": "94105",
    "country": "United States",
    "contact_number": "+1-555-123-4567",
    "contact_email": "john@techventures.com",
    "sie_eligibility": "Yes",
    "notary_required": "No",
    "deed_required": "No",
    "terms_agreed": true
}
```

### Expected Response (200):
```json
{
    "success": true,
    "message": "Step 3 completed successfully",
    "syndicate_id": 3,
    "next_step": "step4_compliance"
}
```

---

## Step 4: Compliance & Attestation
**POST** `/api/onboarding/step4_compliance/`

**Content-Type:** `application/json`

### Request Body:
```json
{
    "syndicate_id": 3,
    "risk_regulatory_attestation": "This syndicate complies with all SEC regulations and operates under Regulation D, Rule 506(c). All investors must be accredited. We maintain strict KYC/AML procedures and conduct regular compliance audits.",
    "jurisdictional_requirements": "United States (all 50 states), Canada, United Kingdom, European Union. We comply with local securities laws in each jurisdiction.",
    "additional_compliance_policies": "KYC/AML policies enforced, Annual audits conducted, GDPR compliant, Regular compliance training for team members, Anti-money laundering procedures, Sanctions screening, Beneficial ownership disclosure"
}
```

### Expected Response (200):
```json
{
    "success": true,
    "message": "Step 4 completed successfully",
    "syndicate_id": 3,
    "next_step": "step5_final_review"
}
```

---

## Step 5: Final Review & Submit
**POST** `/api/onboarding/step5_final_review/`

**Content-Type:** `application/json`

### Request Body:
```json
{
    "syndicate_id": 3
}
```

### Expected Response (200):
```json
{
    "success": true,
    "message": "Syndicate onboarding completed successfully!",
    "syndicate": {
        "id": 3,
        "name": "Tech Ventures Syndicate",
        "description": "Tech Ventures LLC is a leading syndicate...",
        "accredited": "Yes",
        "firm_name": "Tech Ventures LLC",
        "manager": 39,
        "time_of_register": "2025-01-16T15:30:00Z"
    },
    "user": {
        "id": 39,
        "username": "john_manager",
        "email": "john@techventures.com",
        "first_name": "John",
        "last_name": "Manager",
        "role": "syndicate_manager"
    },
    "tokens": {
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}
```

---

## Get Syndicate Progress
**GET** `/api/onboarding/get_syndicate_progress/?syndicate_id=3`

### Expected Response (200):
```json
{
    "syndicate_id": 3,
    "progress": {
        "step1_completed": true,
        "step2_completed": true,
        "step3_completed": true,
        "step4_completed": true,
        "step5_completed": true,
        "current_step": "step5_final_review"
    },
    "syndicate_data": {
        "id": 3,
        "name": "Tech Ventures Syndicate",
        "description": "Tech Ventures LLC is a leading syndicate...",
        "accredited": "Yes",
        "firm_name": "Tech Ventures LLC",
        "manager": 39
    }
}
```

---

## Postman Collection Setup

### Environment Variables:
Create these variables in your Postman environment:

```
base_url = http://192.168.0.146:8000
syndicate_id = 3
user_id = 39
access_token = (from step 5 response)
```

### Testing Workflow:

1. **Step 1: Lead Info**
   - Use the Step 1 request body
   - Save `user_id` and `syndicate_id` from response
   - Update environment variables

2. **Step 2: Entity Profile**
   - Use `syndicate_id` from Step 1
   - Use the Step 2 request body

3. **Step 3: KYB Verification**
   - Use `syndicate_id` from previous steps
   - Use the Step 3 request body

4. **Step 4: Compliance**
   - Use `syndicate_id` from previous steps
   - Use the Step 4 request body

5. **Step 5: Final Review**
   - Use `syndicate_id` from previous steps
   - Save `access_token` from response
   - Update environment variables

6. **Get Progress**
   - Test the progress endpoint with `syndicate_id`

---

## Alternative: Complete Onboarding in One Request

You can also test the complete onboarding by sending all data in Step 1:

### Extended Step 1 Body:
```json
{
    "username": "complete_manager",
    "email": "complete@techventures.com",
    "password": "securepass123",
    "password2": "securepass123",
    "first_name": "Complete",
    "last_name": "Manager",
    "accredited": "Yes",
    "syndicate_name": "Complete Ventures Syndicate",
    "description": "A comprehensive syndicate for testing complete onboarding flow.",
    "sector_ids": [1, 2, 3],
    "geography_ids": [1, 2, 4],
    "lp_network_count": "Network of 100+ investors",
    "enable_lp_network": "Yes",
    "firm_name": "Complete Ventures LLC",
    "team_member": "Complete Manager (CEO), Test Analyst (CFO)",
    "company_legal_name": "Complete Ventures LLC",
    "contact_name": "Complete Manager",
    "contact_position": "CEO",
    "address_1": "456 Test Street",
    "city": "New York",
    "postal_code": "10001",
    "country": "United States",
    "contact_number": "+1-555-999-8888",
    "contact_email": "complete@techventures.com",
    "sie_eligibility": "Yes",
    "notary_required": "No",
    "deed_required": "No",
    "terms_agreed": true,
    "risk_regulatory_attestation": "Complete compliance with all regulations",
    "jurisdictional_requirements": "Global compliance",
    "additional_compliance_policies": "Complete compliance framework"
}
```

---

## Error Testing

### Test Missing Required Fields:
```json
{
    "username": "test_user",
    "email": "test@example.com"
    // Missing password, password2, accredited
}
```

**Expected Error (400):**
```json
{
    "error": "Field \"password\" is required"
}
```

### Test Password Mismatch:
```json
{
    "username": "test_user",
    "email": "test@example.com",
    "password": "password123",
    "password2": "differentpassword",
    "accredited": "Yes"
}
```

**Expected Error (400):**
```json
{
    "error": "Passwords do not match"
}
```

### Test Invalid Syndicate ID:
```json
{
    "syndicate_id": 99999,
    "firm_name": "Test Firm"
}
```

**Expected Error (404):**
```json
{
    "error": "Syndicate not found"
}
```

---

## Testing Checklist

- [ ] Step 1: Create user and syndicate
- [ ] Step 2: Update entity profile
- [ ] Step 3: Complete KYB verification
- [ ] Step 4: Add compliance information
- [ ] Step 5: Final review and get tokens
- [ ] Get progress: Verify all steps completed
- [ ] Test error handling: Missing fields
- [ ] Test error handling: Invalid data
- [ ] Test error handling: Invalid syndicate ID
- [ ] Test complete onboarding in one request

---

## Notes

1. **Sequential Testing**: Steps must be completed in order
2. **Syndicate ID**: Use the `syndicate_id` from Step 1 for all subsequent steps
3. **Authentication**: Step 5 returns JWT tokens for authenticated access
4. **Error Handling**: Each step validates required fields and data
5. **Progress Tracking**: Use the progress endpoint to check completion status
