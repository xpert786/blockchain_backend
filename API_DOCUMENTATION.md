# Blockchain Admin API Documentation

## Overview
This document provides comprehensive documentation for the Blockchain Admin REST APIs including User Management, Syndicate Management, and KYC (Know Your Customer) functionalities.

## Authentication
All APIs use **JWT (JSON Web Token)** authentication. Include the access token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

## Base URL
```
http://localhost:8000/api/
```

---

## Authentication Endpoints

### 1. User Registration
**POST** `/api/users/register/`

Register a new user account.

**Request Body:**
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123!",
    "password2": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe",
    "role": "investor"
}
```

**Roles:** `admin`, `syndicate_manager`, `investor`

**Response (201):**
```json
{
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "investor",
        "is_active": true,
        "is_staff": false,
        "date_joined": "2024-01-15T10:30:00Z"
    },
    "tokens": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    },
    "message": "User registered successfully"
}
```

### 2. User Login
**POST** `/api/users/login/`

Login with credentials to receive JWT tokens.

**Request Body:**
```json
{
    "username": "john_doe",
    "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "role": "investor"
    },
    "tokens": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    },
    "message": "Login successful"
}
```

### 3. Token Refresh
**POST** `/api/token/refresh/`

Get a new access token using refresh token.

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 4. Token Verify
**POST** `/api/token/verify/`

Verify if a token is valid.

**Request Body:**
```json
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 5. User Logout
**POST** `/api/users/logout/`

Logout by blacklisting the refresh token.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200):**
```json
{
    "message": "Logout successful"
}
```

---

## User Management Endpoints

### 6. Get Current User
**GET** `/api/users/me/`

Get details of the currently authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "investor",
    "is_active": true,
    "date_joined": "2024-01-15T10:30:00Z"
}
```

### 7. List All Users
**GET** `/api/users/`

Get list of all users (paginated).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (optional): Page number
- `page_size` (optional): Number of items per page

**Response (200):**
```json
{
    "count": 25,
    "next": "http://localhost:8000/api/users/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "role": "investor"
        }
    ]
}
```

### 8. Get User by ID
**GET** `/api/users/{id}/`

Get specific user details.

**Response (200):**
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "investor"
}
```

### 9. Update User
**PUT/PATCH** `/api/users/{id}/`

Update user information.

**Request Body:**
```json
{
    "first_name": "John Updated",
    "last_name": "Doe",
    "email": "john.new@example.com"
}
```

### 10. Delete User
**DELETE** `/api/users/{id}/`

Delete a user account.

**Response (204):** No Content

### 11. Get User's Syndicates
**GET** `/api/users/{id}/syndicates/`

Get all syndicates managed by a specific user.

---

## Syndicate Management Endpoints

### 12. List All Syndicates
**GET** `/api/syndicates/`

Get list of all syndicates (filtered based on user role).

**Response (200):**
```json
{
    "count": 10,
    "results": [
        {
            "id": 1,
            "name": "Tech Ventures Syndicate",
            "manager": 1,
            "manager_username": "john_doe",
            "description": "Focused on tech startups",
            "accredited": "Yes",
            "sector": "Technology",
            "geography": "North America",
            "firm_name": "Tech Ventures LLC"
        }
    ]
}
```

### 13. Create Syndicate
**POST** `/api/syndicates/`

Create a new syndicate.

**Request Body:**
```json
{
    "name": "Tech Ventures Syndicate",
    "manager": 1,
    "description": "Focused on tech startups",
    "accredited": "Yes",
    "sector": "Technology, AI, Blockchain",
    "geography": "North America",
    "lp_network": "Angel investors, VCs",
    "enable_lp_network": "Yes",
    "firm_name": "Tech Ventures LLC",
    "team_member": "John Doe, Jane Smith",
    "Risk_Regulatory_Attestation": "Compliant with SEC regulations",
    "jurisdictional_requirements": "US, Canada",
    "additional_compliance_policies": "KYC/AML policies in place"
}
```

**Response (201):**
```json
{
    "id": 1,
    "name": "Tech Ventures Syndicate",
    "manager": 1,
    "manager_username": "john_doe",
    "description": "Focused on tech startups",
    "accredited": "Yes"
}
```

### 14. Get Syndicate by ID
**GET** `/api/syndicates/{id}/`

Get specific syndicate details.

### 15. Update Syndicate
**PUT/PATCH** `/api/syndicates/{id}/`

Update syndicate information.

### 16. Delete Syndicate
**DELETE** `/api/syndicates/{id}/`

Delete a syndicate.

### 17. Get My Syndicates
**GET** `/api/syndicates/my_syndicates/`

Get all syndicates managed by the current user.

### 18. Get Syndicate Details
**GET** `/api/syndicates/{id}/details/`

Get detailed information about a syndicate.

---

## KYC Management Endpoints

### 19. List All KYC Records
**GET** `/api/kyc/`

Get list of KYC records (filtered based on user role).
- Admins see all KYC records
- Regular users see only their own KYC records

**Response (200):**
```json
{
    "count": 5,
    "results": [
        {
            "id": 1,
            "user": 1,
            "user_details": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe"
            },
            "status": "Pending",
            "submitted_at": "2024-01-15T10:30:00Z",
            "address_1": "123 Main St",
            "city": "New York",
            "country": "USA"
        }
    ]
}
```

### 20. Create KYC Record
**POST** `/api/kyc/`

Submit a new KYC application.

**Request Body:**
```json
{
    "user": 1,
    "certificate_of_incorporation": "Certificate text or URL",
    "company_bank_statement": "Bank statement URL",
    "address_1": "123 Main Street",
    "address_2": "Suite 100",
    "city": "New York",
    "zip_code": "10001",
    "country": "USA",
    "owner_identity_doc": "ID document URL",
    "owner_proof_of_address": "Proof URL",
    "sie_eligibilty": "Eligible",
    "notary": "Notary details",
    "Unlocksley_To_Sign_a_Deed_Of_adherence": true,
    "Investee_Company_Contact_Number": "+1234567890",
    "Investee_Company_Email": "company@example.com",
    "I_Agree_To_Investee_Terms": true
}
```

**Response (201):**
```json
{
    "id": 1,
    "user": 1,
    "status": "Pending",
    "submitted_at": "2024-01-15T10:30:00Z",
    "message": "KYC application submitted successfully"
}
```

### 21. Get KYC by ID
**GET** `/api/kyc/{id}/`

Get specific KYC record details.

### 22. Update KYC Record
**PUT/PATCH** `/api/kyc/{id}/`

Update KYC information (users can only update their own).

### 23. Delete KYC Record
**DELETE** `/api/kyc/{id}/`

Delete a KYC record.

### 24. Get My KYC Records
**GET** `/api/kyc/my_kyc/`

Get all KYC records for the current user.

**Response (200):**
```json
[
    {
        "id": 1,
        "status": "Approved",
        "submitted_at": "2024-01-15T10:30:00Z"
    }
]
```

### 25. Update KYC Status (Admin Only)
**PATCH** `/api/kyc/{id}/update_status/`

Update the status of a KYC application (Admin only).

**Request Body:**
```json
{
    "status": "Approved"
}
```

**Valid statuses:** `Pending`, `Approved`, `Rejected`

**Response (200):**
```json
{
    "message": "KYC status updated successfully",
    "data": {
        "id": 1,
        "status": "Approved",
        "user": 1
    }
}
```

### 26. Get Pending KYC Records (Admin Only)
**GET** `/api/kyc/pending/`

Get all KYC records with pending status.

### 27. Get Approved KYC Records (Admin Only)
**GET** `/api/kyc/approved/`

Get all approved KYC records.

### 28. Get Rejected KYC Records (Admin Only)
**GET** `/api/kyc/rejected/`

Get all rejected KYC records.

### 29. Get User KYC Status
**GET** `/api/kyc/{id}/user_kyc_status/`

Get KYC status for a specific user.

**Response (200):**
```json
{
    "user_id": 1,
    "username": "john_doe",
    "status": "Approved",
    "submitted_at": "2024-01-15T10:30:00Z"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
    "error": "Invalid request data",
    "details": {
        "field_name": ["Error message"]
    }
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "error": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
    "error": "Internal server error"
}
```

---

## JWT Token Configuration

- **Access Token Lifetime:** 5 hours
- **Refresh Token Lifetime:** 7 days
- **Token Type:** Bearer
- **Algorithm:** HS256

---

## Permissions Summary

| Endpoint | Admin | Syndicate Manager | Investor |
|----------|-------|-------------------|----------|
| User Management | Full Access | View Only | View Only |
| Syndicate List | All Syndicates | Own Syndicates | All (Read) |
| Syndicate Create | ✓ | ✓ | ✗ |
| KYC List | All Records | Own Records | Own Records |
| KYC Status Update | ✓ | ✗ | ✗ |
| KYC Create | ✓ | ✓ | ✓ |

---

## Testing with Postman/cURL

### Example: Login
```bash
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePassword123!"
  }'
```

### Example: Get User Info (with token)
```bash
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### Example: Create Syndicate
```bash
curl -X POST http://localhost:8000/api/syndicates/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Syndicate",
    "description": "Investment syndicate",
    "accredited": "Yes"
  }'
```

---

## Notes

1. All timestamps are in UTC ISO 8601 format
2. Pagination is applied to list endpoints (10 items per page by default)
3. File uploads (like logos) should use multipart/form-data
4. Keep your access tokens secure and refresh them before expiration
5. Use HTTPS in production environments
6. The refresh token should be stored securely (e.g., httpOnly cookies)

---

## Support

For issues or questions, please contact the development team or refer to the Django REST Framework and SimpleJWT documentation.

