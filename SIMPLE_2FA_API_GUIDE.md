# Simple 2FA API Guide - Email & Mobile Verification

This guide covers the simplified authentication API with only Email and Mobile (SMS) verification, matching your frontend design.

## Base URL
```
http://localhost:8000/api/auth/
```

## Authentication Flow

### 1. Login
**POST** `/api/auth/login/`

Login with username and password. If 2FA is enabled, returns a flag requiring 2FA verification.

**Request Body:**
```json
{
    "username": "john_doe",
    "password": "password123"
}
```

**Response (No 2FA):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@gmail.com",
        "role": "syndicate_manager",
        "two_factor_enabled": false
    },
    "requires_2fa": false
}
```

**Response (With 2FA):**
```json
{
    "requires_2fa": true,
    "user_id": 1,
    "username": "john_doe",
    "two_factor_method": "email",
    "message": "Please verify your EMAIL code"
}
```

### 2. Verify 2FA Login
**POST** `/api/auth/verify_2fa_login/`

Verify 2FA code during login process.

**Request Body:**
```json
{
    "user_id": 1,
    "code": "123456",
    "two_factor_method": "email"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@gmail.com",
        "role": "syndicate_manager",
        "two_factor_enabled": true
    },
    "message": "Login successful"
}
```

## 2FA Setup Flow

### 3. Setup 2FA - Choose Method
**POST** `/api/auth/setup_2fa/`

Choose between Email or Mobile (SMS) for 2FA setup.

**Headers:**
```
Authorization: Bearer <access_token>
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
    "message": "Verification code sent to john@gmail.com",
    "email": "john@gmail.com",
    "method": "email",
    "next_step": "verify_setup"
}
```

**Response (SMS):**
```json
{
    "success": true,
    "message": "Verification code sent to +1234567890",
    "phone_number": "+1234567890",
    "method": "sms",
    "next_step": "verify_setup"
}
```

### 4. Verify Setup Code
**POST** `/api/auth/verify_setup/`

Enter the 6-digit verification code received via email or SMS.

**Headers:**
```
Authorization: Bearer <access_token>
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
    "message": "Two-factor authentication enabled successfully",
    "two_factor_enabled": true,
    "two_factor_method": "email"
}
```

### 5. Resend Code
**POST** `/api/auth/resend_code/`

Resend verification code if not received.

**Headers:**
```
Authorization: Bearer <access_token>
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
    "message": "New verification code sent to john@gmail.com"
}
```

## Management Endpoints

### 6. Get 2FA Status
**GET** `/api/auth/get_2fa_status/`

Get current 2FA status for the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "two_factor_enabled": true,
    "two_factor_method": "email",
    "phone_number": null,
    "email": "john@gmail.com"
}
```

### 7. Disable 2FA
**POST** `/api/auth/disable_2fa/`

Disable two-factor authentication (requires password confirmation).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "password": "your_password"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Two-factor authentication disabled successfully"
}
```

## Frontend Integration Examples

### Complete 2FA Setup Flow

1. **Choose Email Method:**
```javascript
const response = await fetch('/api/auth/setup_2fa/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        method: 'email'
    })
});

const data = await response.json();
// Shows: "A verification code has been sent to john@gmail.com"
```

2. **Enter Verification Code:**
```javascript
const response = await fetch('/api/auth/verify_setup/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        code: '123456',
        method: 'email'
    })
});

const data = await response.json();
// Shows: "Two-factor authentication enabled successfully"
```

3. **Resend Code if Needed:**
```javascript
const response = await fetch('/api/auth/resend_code/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        method: 'email'
    })
});

const data = await response.json();
// Shows: "New verification code sent to john@gmail.com"
```

### Login with 2FA Flow

1. **Initial Login:**
```javascript
const response = await fetch('/api/auth/login/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'john_doe',
        password: 'password123'
    })
});

const data = await response.json();
if (data.requires_2fa) {
    // Show 2FA verification screen
    // Display: "Please verify your EMAIL code"
}
```

2. **Verify 2FA Code:**
```javascript
const response = await fetch('/api/auth/verify_2fa_login/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        user_id: data.user_id,
        code: '123456',
        two_factor_method: data.two_factor_method
    })
});

const data = await response.json();
// Login successful, store tokens
```

## Error Responses

### 400 Bad Request
```json
{
    "error": "Username and password are required"
}
```

### 401 Unauthorized
```json
{
    "error": "Invalid credentials"
}
```

### 404 Not Found
```json
{
    "error": "User not found"
}
```

## Code Format

- **Email & SMS codes**: 6-digit numeric codes (e.g., "123456")
- **Code expiration**: 
  - Email: 15 minutes
  - SMS: 10 minutes
- **Code format for frontend**: `_ _ _ - _ _ _` (6 separate input fields)

## Security Features

1. **JWT Tokens**: Secure token-based authentication
2. **2FA Support**: Email and SMS verification only
3. **Code Expiration**: Time-limited verification codes
4. **Password Confirmation**: Required for disabling 2FA
5. **Rate Limiting**: Prevents brute force attacks (to be implemented)

## Notes

- All endpoints return JSON responses
- Authentication tokens should be included in the `Authorization` header
- Email and SMS sending requires proper service configuration
- The frontend should handle the 6-digit code input format as shown in your design
- Codes are automatically generated and sent when requested
