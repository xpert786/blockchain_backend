# 🚀 Blockchain API Testing Instructions

## 📋 Prerequisites
1. **Django Server Running**: Make sure your Django server is running on `http://localhost:8000`
2. **Postman Installed**: Download and install Postman from https://www.postman.com/downloads/
3. **Database Migrated**: Ensure all migrations are applied (`python manage.py migrate`)

## 🔧 Setup Instructions

### 1. Import Postman Collection
1. Open Postman
2. Click "Import" button
3. Select the `Blockchain_API_Postman_Collection.json` file
4. The collection will be imported with all endpoints organized in folders

### 2. Set Environment Variables
1. In Postman, click on the "Environments" tab
2. Create a new environment called "Blockchain API"
3. Add these variables:
   - `base_url`: `http://localhost:8000/blockchain-backend`
   - `access_token`: (leave empty, will be filled automatically)
   - `refresh_token`: (leave empty, will be filled automatically)

### 3. Select Environment
1. In the top-right corner of Postman, select "Blockchain API" environment
2. This will ensure all requests use the correct base URL

## 🧪 Testing Workflow

### Step 1: Test Server Status
1. Go to "🔍 Debug & Status" folder
2. Run "Server Status" request
3. Should return 200 OK with server information

### Step 2: Complete Registration Flow
1. Go to "🔐 Registration Flow (Main)" folder
2. Follow these steps in order:

#### 2.1 User Registration
- Run "1. User Registration"
- **Request Body**: Update with your test data
- **Expected**: 201 Created with access_token
- **Action**: Copy the `access` token from response and paste it into the `access_token` environment variable

#### 2.2 Choose Verification Method
- Run "2. Choose Verification Method - Email" (or SMS)
- **Expected**: 200 OK with verification message

#### 2.3 Verify OTP Code
- **Note**: You'll need to check your email/SMS for the actual OTP code
- Update the `code` field in the request body with the real OTP
- Run "3. Verify OTP Code"
- **Expected**: 200 OK with verification success

#### 2.4 Get Terms of Service
- Run "4. Get Terms of Service"
- **Expected**: 200 OK with list of 5 terms

#### 2.5 Accept Terms
- Run "5. Accept Terms of Service"
- **Expected**: 200 OK with acceptance confirmation

#### 2.6 Complete Registration
- Run "6. Complete Registration"
- **Expected**: 200 OK with completion message

### Step 3: Test Other Endpoints
1. **User Management**: Test user listing and details
2. **Sector/Geography**: Test data retrieval
3. **Authentication**: Test JWT token refresh
4. **2FA**: Test two-factor authentication setup
5. **Debug**: Test all debug endpoints

## 🔍 Expected Responses

### Successful Registration Response
```json
{
    "success": true,
    "message": "User registered successfully",
    "user_id": 1,
    "email": "john.doe@example.com",
    "phone_number": "+1234567890",
    "full_name": "John Doe",
    "tokens": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    },
    "next_step": "choose_verification_method"
}
```

### Error Responses
- **400 Bad Request**: Missing required fields, validation errors
- **401 Unauthorized**: Invalid/expired tokens, wrong OTP codes
- **404 Not Found**: Invalid endpoints or resource IDs
- **500 Internal Server Error**: Server-side issues

## 🚨 Common Issues & Solutions

### Issue 1: "Connection Refused"
- **Solution**: Make sure Django server is running (`python manage.py runserver`)

### Issue 2: "Invalid Token" or "Authentication Required"
- **Solution**: Make sure you've set the `access_token` environment variable after registration

### Issue 3: "OTP Code Invalid"
- **Solution**: Check your email/SMS for the actual 6-digit code and update the request body

### Issue 4: "Field Required" Errors
- **Solution**: Make sure all required fields are included in request body

### Issue 5: "User Already Exists"
- **Solution**: Use a different email/phone number for testing

## 📊 Testing Checklist

- [ ] Server is running and accessible
- [ ] Environment variables are set
- [ ] Registration flow completes successfully
- [ ] JWT tokens are generated and working
- [ ] All CRUD operations work for users, sectors, geographies
- [ ] 2FA setup and verification works
- [ ] Email/SMS test endpoints work
- [ ] Debug endpoints return proper status

## 🔄 Automated Testing

You can also use Postman's Collection Runner to run all tests automatically:
1. Click on the collection name
2. Click "Run" button
3. Select the environment
4. Click "Run Blockchain API - Complete Collection"

## 📝 Notes

- **Username**: Auto-generated from email (e.g., `john.doe@example.com` → `john.doe`)
- **Phone Numbers**: Must be unique across all users
- **Roles**: `"syndicate"` or `"investor"`
- **OTP Codes**: 6-digit numbers, expire after 15 minutes (email) or 10 minutes (SMS)
- **JWT Tokens**: Access tokens expire, use refresh tokens to get new ones

## 🆘 Support

If you encounter any issues:
1. Check the Django server logs
2. Verify all environment variables are set
3. Ensure the database is properly migrated
4. Check that all required fields are included in requests
