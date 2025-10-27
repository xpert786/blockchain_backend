# Authentication API Guide

This guide covers the comprehensive authentication API endpoints with Two-Factor Authentication (2FA) support.

## Base URL
```
http://localhost:8000/api/auth/
```

## Authentication Endpoints

### 1. Login
**POST** `/api/auth/login/`

Login with username and password. If 2FA is enabled, returns a flag requiring 2FA verification.

**Request Body:**
```json
{
    "username": "your_username",
    "password": "your_password"
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
        "email": "john@example.com",
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
    "two_factor_method": "sms",
    "message": "Please verify your SMS code"
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
    "two_factor_method": "sms"
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
        "email": "john@example.com",
        "role": "syndicate_manager",
        "two_factor_enabled": true
    },
    "message": "Login successful"
}
```

### 3. Enable 2FA
**POST** `/api/auth/enable_2fa/`

Enable two-factor authentication for the current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (SMS):**
```json
{
    "method": "sms",
    "phone_number": "+1234567890"
}
```

**Request Body (TOTP):**
```json
{
    "method": "totp"
}
```

**Request Body (Email):**
```json
{
    "method": "email"
}
```

**Response (SMS/Email):**
```json
{
    "message": "Verification code sent to +1234567890",
    "phone_number": "+1234567890",
    "next_step": "verify_2fa_setup"
}
```

**Response (TOTP):**
```json
{
    "message": "Scan the QR code with your authenticator app",
    "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "secret": "JBSWY3DPEHPK3PXP",
    "next_step": "verify_totp_setup"
}
```

### 4. Verify 2FA Setup
**POST** `/api/auth/verify_2fa_setup/`

Verify the 2FA setup code to complete the process.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "code": "123456",
    "method": "sms"
}
```

**Response:**
```json
{
    "message": "Two-factor authentication enabled successfully",
    "backup_codes": [
        "A1B2C3D4",
        "E5F6G7H8",
        "I9J0K1L2",
        "M3N4O5P6",
        "Q7R8S9T0",
        "U1V2W3X4",
        "Y5Z6A7B8",
        "C9D0E1F2",
        "G3H4I5J6",
        "K7L8M9N0"
    ],
    "warning": "Save these backup codes in a secure location"
}
```

### 5. Disable 2FA
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
    "message": "Two-factor authentication disabled successfully"
}
```

### 6. Resend 2FA Code
**POST** `/api/auth/resend_2fa_code/`

Resend 2FA verification code.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "method": "sms"
}
```

**Response:**
```json
{
    "message": "New verification code sent to +1234567890"
}
```

### 7. Get 2FA Status
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
    "two_factor_method": "sms",
    "phone_number": "+1234567890",
    "email": "john@example.com",
    "backup_codes_count": 10
}
```

### 8. Regenerate Backup Codes
**POST** `/api/auth/regenerate_backup_codes/`

Regenerate backup codes for 2FA (requires password confirmation).

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
    "message": "Backup codes regenerated successfully",
    "backup_codes": [
        "A1B2C3D4",
        "E5F6G7H8",
        "I9J0K1L2",
        "M3N4O5P6",
        "Q7R8S9T0",
        "U1V2W3X4",
        "Y5Z6A7B8",
        "C9D0E1F2",
        "G3H4I5J6",
        "K7L8M9N0"
    ],
    "warning": "Save these backup codes in a secure location"
}
```

## 2FA Methods

### SMS 2FA
- Sends 6-digit verification codes via SMS
- Codes expire in 10 minutes
- Requires valid phone number

### TOTP (Time-based One-Time Password)
- Uses authenticator apps like Google Authenticator, Authy, etc.
- Generates QR code for easy setup
- 30-second time windows
- More secure than SMS

### Email 2FA
- Sends 6-digit verification codes via email
- Codes expire in 15 minutes
- Uses user's registered email address

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

## Security Features

1. **JWT Tokens**: Secure token-based authentication
2. **2FA Support**: Multiple methods (SMS, TOTP, Email)
3. **Backup Codes**: Recovery mechanism for lost devices
4. **Password Confirmation**: Required for sensitive operations
5. **Code Expiration**: Time-limited verification codes
6. **Rate Limiting**: Prevents brute force attacks (to be implemented)

## Usage Examples

### Complete Login Flow with 2FA

1. **Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john_doe", "password": "password123"}'
```

2. **Verify 2FA (if required):**
```bash
curl -X POST http://localhost:8000/api/auth/verify_2fa_login/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "code": "123456", "two_factor_method": "sms"}'
```

### Enable TOTP 2FA

1. **Enable TOTP:**
```bash
curl -X POST http://localhost:8000/api/auth/enable_2fa/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"method": "totp"}'
```

2. **Verify Setup:**
```bash
curl -X POST http://localhost:8000/api/auth/verify_2fa_setup/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"code": "123456", "method": "totp"}'
```

## Notes

- All endpoints return JSON responses
- Authentication tokens should be included in the `Authorization` header
- Backup codes should be stored securely by users
- SMS and Email sending requires proper service configuration
- TOTP setup requires scanning QR code with authenticator app
