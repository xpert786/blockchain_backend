# Complete Registration Flow API Guide

This guide covers the complete registration flow with email/mobile verification that matches your frontend design.

## Base URL
```
http://127.0.0.1:8000/api/
```

## Complete Registration Flow

### Step 1: Register User
**POST** `/api/registration-flow/register/`

Register a new user with basic information.

**Request Body:**
```json
{
    "username": "suneha",
    "email": "suneha@example.com",
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
    "user_id": 1,
    "username": "suneha",
    "email": "suneha@example.com",
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

**Request Body (Mobile/SMS):**
```json
{
    "method": "sms",
    "phone_number": "+1234567890"
}
```

**Response (Email):**
```json
{
    "success": true,
    "message": "A verification code has been sent to suneha@example.com",
    "email": "suneha@example.com",
    "method": "email",
    "next_step": "verify_code"
}
```

**Response (SMS):**
```json
{
    "success": true,
    "message": "A verification code has been sent to +1234567890",
    "phone_number": "+1234567890",
    "method": "sms",
    "next_step": "verify_code"
}
```

### Step 3: Verify Code
**POST** `/api/registration-flow/verify_code/`

Enter the 6-digit verification code received via email or SMS.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "code": "123456",
    "method": "email"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Verification successful! Your account is now active.",
    "user": {
        "id": 1,
        "username": "suneha",
        "email": "suneha@example.com",
        "email_verified": true,
        "phone_verified": false,
        "role": "investor"
    },
    "next_step": "complete"
}
```

### Step 4: Resend Code (Optional)
**POST** `/api/registration-flow/resend_code/`

Resend verification code if not received.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "method": "email"
}
```

**Response:**
```json
{
    "success": true,
    "message": "New verification code sent to suneha@example.com"
}
```

## Complete cURL Examples

### 1. Register User
```bash
curl --location 'http://127.0.0.1:8000/api/registration-flow/register/' \
--header 'Content-Type: application/json' \
--data '{
    "username": "suneha",
    "email": "suneha@example.com",
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

### 3. Choose Mobile Verification
```bash
curl --location 'http://127.0.0.1:8000/api/registration-flow/choose_verification_method/' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--data '{
    "method": "sms",
    "phone_number": "+1234567890"
}'
```

### 4. Verify Code
```bash
curl --location 'http://127.0.0.1:8000/api/registration-flow/verify_code/' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--data '{
    "code": "123456",
    "method": "email"
}'
```

### 5. Resend Code
```bash
curl --location 'http://127.0.0.1:8000/api/registration-flow/resend_code/' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--data '{
    "method": "email"
}'
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
        username: 'suneha',
        email: 'suneha@example.com',
        password: 'Pass123!',
        confirm_password: 'Pass123!',
        full_name: 'Suneha Sharma',
        role: 'investor'
    })
});

const registerData = await registerResponse.json();
const accessToken = registerData.tokens.access;

// Step 2: Choose verification method
const verificationResponse = await fetch('/api/registration-flow/choose_verification_method/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
        method: 'email' // or 'sms' with phone_number
    })
});

const verificationData = await verificationResponse.json();
// Show: "A verification code has been sent to suneha@example.com"

// Step 3: Verify code
const verifyResponse = await fetch('/api/registration-flow/verify_code/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
        code: '123456',
        method: 'email'
    })
});

const verifyData = await verifyResponse.json();
// Show: "Verification successful! Your account is now active."
```

## Error Responses

### 400 Bad Request
```json
{
    "error": "Field 'username' is required"
}
```

### 401 Unauthorized
```json
{
    "error": "Invalid or expired verification code"
}
```

### 404 Not Found
```json
{
    "error": "User not found"
}
```

## Code Format

- **Verification codes**: 6-digit numeric codes (e.g., "123456")
- **Code expiration**: 
  - Email: 15 minutes
  - SMS: 10 minutes
- **Frontend format**: `_ _ _ - _ _ _` (6 separate input fields)

## Features

✅ **Complete Registration Flow** - From signup to verification  
✅ **JWT Tokens** - Immediate access after registration  
✅ **Email Verification** - 6-digit codes via email  
✅ **Mobile Verification** - 6-digit codes via SMS  
✅ **Resend Functionality** - Resend codes if needed  
✅ **Error Handling** - Comprehensive error responses  
✅ **Frontend Ready** - Matches your UI design exactly  

## Notes

- All endpoints return JSON responses
- Authentication tokens are provided immediately after registration
- Verification codes are automatically generated and sent
- The flow matches your frontend design perfectly
- Email and SMS sending requires proper service configuration
