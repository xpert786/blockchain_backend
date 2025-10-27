# Complete Registration Flow with Terms of Service

This guide covers the complete registration flow from signup to terms acceptance, matching your frontend design exactly.

## Base URL
```
http://127.0.0.1:8000/api/registration-flow/
```

## Complete Registration Flow

### Step 1: Register User
**POST** `/api/registration-flow/register/`

Register a new user with basic information.

**Request Body:**
```json
{
    "username": "suneha4",
    "email": "suneha@itinfonity.com",
    "password": "Pass123!",
    "confirm_password": "Pass123!",
    "full_name": "Suneha Sharma",
    "role": "investor"
}
```

**Response:**
```json
{
    "success": true,
    "message": "User registered successfully",
    "user_id": 18,
    "username": "suneha4",
    "email": "suneha@itinfonity.com",
    "full_name": "Suneha Sharma",
    "tokens": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    },
    "next_step": "choose_verification_method"
}
```

### Step 2: Choose Verification Method
**POST** `/api/registration-flow/choose_verification_method/`

Choose between email or mobile verification.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body (Email):**
```json
{
    "method": "email"
}
```

**Response:**
```json
{
    "success": true,
    "message": "A verification code has been sent to suneha@itinfonity.com",
    "email": "suneha@itinfonity.com",
    "method": "email",
    "next_step": "verify_code"
}
```

### Step 3: Verify Code
**POST** `/api/registration-flow/verify_code/`

Enter the 6-digit verification code received via email.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "code": "736155",
    "method": "email"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Verification successful! Your account is now active.",
    "user": {
        "id": 18,
        "username": "suneha4",
        "email": "suneha@itinfonity.com",
        "email_verified": true,
        "phone_verified": false,
        "role": "investor"
    },
    "next_step": "accept_terms"
}
```

### Step 4: Get Terms of Service
**GET** `/api/registration-flow/get_terms/`

Get available terms of service documents.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "terms": [
        {
            "id": "general_terms",
            "title": "General terms of services",
            "description": "General terms and conditions for using the platform"
        },
        {
            "id": "investing_banking_terms",
            "title": "Investing banking Terms",
            "description": "Terms specific to investment banking services"
        },
        {
            "id": "e_sign_consent",
            "title": "E-Sign Consent",
            "description": "Electronic signature consent agreement"
        },
        {
            "id": "infrafi_deposit",
            "title": "Short Deposit Repayment and Custodial Agreement",
            "description": "Deposit placement and custodial agreement terms"
        },
        {
            "id": "cookie_consent",
            "title": "Cookie consent preferences",
            "description": "Cookie usage and privacy preferences"
        }
    ],
    "message": "Terms of service documents available for review"
}
```

### Step 5: Accept Terms of Service
**POST** `/api/registration-flow/accept_terms/`

Accept all required terms of service.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "terms": [
        {
            "terms_type": "general_terms",
            "accepted": true
        },
        {
            "terms_type": "investing_banking_terms",
            "accepted": true
        },
        {
            "terms_type": "e_sign_consent",
            "accepted": true
        },
        {
            "terms_type": "infrafi_deposit",
            "accepted": true
        },
        {
            "terms_type": "cookie_consent",
            "accepted": true
        }
    ]
}
```

**Response:**
```json
{
    "success": true,
    "message": "Terms of service accepted successfully",
    "accepted_terms": [
        {
            "terms_type": "general_terms",
            "accepted": true,
            "accepted_at": "2025-01-16T12:00:00Z"
        },
        {
            "terms_type": "investing_banking_terms",
            "accepted": true,
            "accepted_at": "2025-01-16T12:00:00Z"
        },
        {
            "terms_type": "e_sign_consent",
            "accepted": true,
            "accepted_at": "2025-01-16T12:00:00Z"
        },
        {
            "terms_type": "infrafi_deposit",
            "accepted": true,
            "accepted_at": "2025-01-16T12:00:00Z"
        },
        {
            "terms_type": "cookie_consent",
            "accepted": true,
            "accepted_at": "2025-01-16T12:00:00Z"
        }
    ],
    "next_step": "registration_complete"
}
```

### Step 6: Complete Registration
**POST** `/api/registration-flow/complete_registration/`

Final step to complete the registration process.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{}
```

**Response:**
```json
{
    "success": true,
    "message": "Registration completed successfully! Welcome to the platform.",
    "user": {
        "id": 18,
        "username": "suneha4",
        "email": "suneha@itinfonity.com",
        "email_verified": true,
        "phone_verified": false,
        "role": "investor"
    },
    "registration_complete": true
}
```

## Complete cURL Examples

### 1. Register User
```bash
curl --location 'http://127.0.0.1:8000/api/registration-flow/register/' \
--header 'Content-Type: application/json' \
--data '{
    "username": "suneha4",
    "email": "suneha@itinfonity.com",
    "password": "Pass123!",
    "confirm_password": "Pass123!",
    "full_name": "Suneha Sharma",
    "role": "investor"
}'
```

### 2. Choose Email Verification
```bash
curl --location 'http://127.0.0.1:8000/api/registration-flow/choose_verification_method/' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--data '{
    "method": "email"
}'
```

### 3. Verify Code
```bash
curl --location 'http://127.0.0.1:8000/api/registration-flow/verify_code/' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--data '{
    "code": "736155",
    "method": "email"
}'
```

### 4. Get Terms
```bash
curl --location 'http://127.0.0.1:8000/api/registration-flow/get_terms/' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

### 5. Accept Terms
```bash
curl --location 'http://127.0.0.1:8000/api/registration-flow/accept_terms/' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--data '{
    "terms": [
        {"terms_type": "general_terms", "accepted": true},
        {"terms_type": "investing_banking_terms", "accepted": true},
        {"terms_type": "e_sign_consent", "accepted": true},
        {"terms_type": "infrafi_deposit", "accepted": true},
        {"terms_type": "cookie_consent", "accepted": true}
    ]
}'
```

### 6. Complete Registration
```bash
curl --location 'http://127.0.0.1:8000/api/registration-flow/complete_registration/' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--data '{}'
```

## Frontend Integration Flow

### JavaScript Example

```javascript
// Step 1: Register
const registerResponse = await fetch('/api/registration-flow/register/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'suneha4',
        email: 'suneha@itinfonity.com',
        password: 'Pass123!',
        confirm_password: 'Pass123!',
        full_name: 'Suneha Sharma',
        role: 'investor'
    })
});

const registerData = await registerResponse.json();
const accessToken = registerData.tokens.access;

// Step 2: Choose email verification
const verificationResponse = await fetch('/api/registration-flow/choose_verification_method/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
        method: 'email'
    })
});

// Step 3: Verify code (after user enters code)
const verifyResponse = await fetch('/api/registration-flow/verify_code/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
        code: '736155',
        method: 'email'
    })
});

// Step 4: Get terms
const termsResponse = await fetch('/api/registration-flow/get_terms/', {
    headers: {
        'Authorization': `Bearer ${accessToken}`
    }
});

const termsData = await termsResponse.json();

// Step 5: Accept terms
const acceptTermsResponse = await fetch('/api/registration-flow/accept_terms/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
        terms: [
            { terms_type: 'general_terms', accepted: true },
            { terms_type: 'investing_banking_terms', accepted: true },
            { terms_type: 'e_sign_consent', accepted: true },
            { terms_type: 'infrafi_deposit', accepted: true },
            { terms_type: 'cookie_consent', accepted: true }
        ]
    })
});

// Step 6: Complete registration
const completeResponse = await fetch('/api/registration-flow/complete_registration/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({})
});
```

## Terms of Service Types

The system supports these terms types that match your frontend:

1. **general_terms** - "General terms of services"
2. **investing_banking_terms** - "Investing banking Terms"
3. **e_sign_consent** - "E-Sign Consent"
4. **infrafi_deposit** - "Short Deposit Repayment and Custodial Agreement"
5. **cookie_consent** - "Cookie consent preferences"

## Features

✅ **Complete Registration Flow** - From signup to completion  
✅ **Email Verification** - 6-digit codes via email  
✅ **Terms of Service** - All 5 terms matching your frontend  
✅ **Audit Trail** - IP address and user agent tracking  
✅ **Error Handling** - Comprehensive error responses  
✅ **Frontend Ready** - Matches your UI design exactly  

## Notes

- All endpoints return JSON responses
- Authentication tokens are provided immediately after registration
- Terms acceptance is tracked with IP address and user agent
- The flow matches your frontend design perfectly
- Email verification codes expire in 15 minutes
