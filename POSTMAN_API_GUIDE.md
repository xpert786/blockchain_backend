# Syndicate Onboarding API - Postman Collection Guide

## Overview

This guide provides comprehensive instructions for using the Syndicate Onboarding API Postman collection. The collection includes all endpoints for syndicate management, user authentication, and advanced operations.

## Files Included

1. **`Syndicate_Onboarding_API.postman_collection.json`** - Main Postman collection
2. **`Syndicate_API_Environment.postman_environment.json`** - Environment variables
3. **`POSTMAN_API_GUIDE.md`** - This documentation

## Quick Setup

### 1. Import Collection and Environment

1. Open Postman
2. Click **Import** button
3. Import both files:
   - `Syndicate_Onboarding_API.postman_collection.json`
   - `Syndicate_API_Environment.postman_environment.json`
4. Select the **Syndicate API Environment** from the environment dropdown

### 2. Start Your Django Server

```bash
# Navigate to your project directory
cd E:\blockchain_admin

# Activate virtual environment
.\venv\Scripts\activate

# Start the server
python manage.py runserver
```

### 3. Verify Server is Running

The server should be running at `http://127.0.0.1:8000`

## Environment Variables

The environment includes the following variables:

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://127.0.0.1:8000` | API base URL |
| `access_token` | (auto-set) | JWT access token |
| `refresh_token` | (auto-set) | JWT refresh token |
| `user_id` | (auto-set) | Current user ID |
| `syndicate_id` | (auto-set) | Current syndicate ID |
| `test_username` | `test_manager` | Test username |
| `test_email` | `test@example.com` | Test email |
| `test_password` | `TestPass123!` | Test password |

## API Endpoints Overview

### Authentication
- **Register User** - Create new user account
- **Login User** - Authenticate and get tokens
- **Get Current User** - Get user profile
- **Refresh Token** - Get new access token
- **Logout User** - Invalidate tokens

### Syndicate Management
- **Create Syndicate (Minimal)** - Basic syndicate creation
- **Create Syndicate (Complete)** - Full syndicate with all fields
- **List All Syndicates** - Get paginated syndicate list
- **Get Syndicate by ID** - Get specific syndicate details
- **Update Syndicate (PATCH)** - Partial updates
- **Update Syndicate (PUT)** - Complete replacement
- **Delete Syndicate** - Remove syndicate

### Syndicate Actions
- **Get My Syndicates** - User's managed syndicates
- **Get Syndicate Details** - Detailed syndicate info
- **Get Recent Syndicates** - Last 30 days
- **Get Syndicates by Date** - Specific date filter
- **Get Syndicate Statistics** - Creation analytics
- **Get Oldest/Newest Syndicates** - Time-based queries

### User Management
- **List All Users** - Admin user management
- **Get User by ID** - User details
- **Get User's Syndicates** - User's syndicates
- **Update User** - Modify user info

### File Upload
- **Upload Syndicate Logo** - Image upload
- **Upload Logo with Fields** - Combined upload and update

### Test Scenarios
- **Complete Onboarding Flow** - End-to-end testing
- **Error Handling Tests** - Error scenario validation

## Step-by-Step Usage

### 1. Initial Setup

1. **Register a User**:
   - Go to `Authentication > Register User`
   - Click **Send**
   - Check the response - tokens are automatically saved to environment

2. **Verify Login**:
   - Go to `Authentication > Login User`
   - Click **Send**
   - Tokens are refreshed in environment

### 2. Create Your First Syndicate

1. **Create Basic Syndicate**:
   - Go to `Syndicate Management > Create Syndicate (Minimal)`
   - Click **Send**
   - Syndicate ID is automatically saved

2. **Update with Complete Details**:
   - Go to `Syndicate Management > Update Syndicate (PATCH)`
   - Modify the request body as needed
   - Click **Send**

### 3. Test Advanced Features

1. **View Your Syndicates**:
   - Go to `Syndicate Actions > Get My Syndicates`
   - Click **Send**

2. **Get Statistics**:
   - Go to `Syndicate Actions > Get Syndicate Statistics`
   - Click **Send**

### 4. Run Complete Test Flow

1. **Run Onboarding Flow**:
   - Go to `Test Scenarios > Complete Onboarding Flow`
   - Run each step in sequence:
     - 1. Register Syndicate Manager
     - 2. Create Basic Syndicate
     - 3. Update with Complete Details
     - 4. Verify Syndicate Details

## Request Examples

### Register User
```json
{
    "username": "syndicate_manager1",
    "email": "manager@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "John",
    "last_name": "Manager",
    "role": "syndicate_manager"
}
```

### Create Syndicate (Minimal)
```json
{
    "name": "Healthcare Innovation Fund",
    "description": "Investing in healthcare technology and biotech",
    "accredited": "Yes",
    "sector": "Healthcare, Biotech, Medical Devices",
    "geography": "North America",
    "firm_name": "Healthcare Innovations LLC"
}
```

### Create Syndicate (Complete)
```json
{
    "name": "Tech Ventures Syndicate",
    "description": "A syndicate focused on early-stage technology investments, specializing in AI, blockchain, and SaaS companies.",
    "accredited": "Yes",
    "sector": "Technology, AI, Blockchain, SaaS, Fintech",
    "geography": "North America, Europe",
    "lp_network": "Angel investors, VCs, Family offices",
    "enable_lp_network": "Yes",
    "firm_name": "Tech Ventures LLC",
    "team_member": "John Manager (Managing Partner), Sarah Smith (Investment Analyst), Mike Johnson (Legal Counsel)",
    "Risk_Regulatory_Attestation": "This syndicate complies with all SEC regulations and operates under Regulation D, Rule 506(c). All investors must be accredited.",
    "jurisdictional_requirements": "United States (all 50 states), Canada, United Kingdom, European Union",
    "additional_compliance_policies": "KYC/AML policies enforced, Annual audits conducted, GDPR compliant, Regular compliance training for team members"
}
```

### Update Syndicate (PATCH)
```json
{
    "description": "Updated description - Now focusing on late-stage tech companies",
    "sector": "Technology, AI, Enterprise SaaS",
    "geography": "Global"
}
```

## Response Examples

### Successful Registration (201)
```json
{
    "user": {
        "id": 1,
        "username": "syndicate_manager1",
        "email": "manager@example.com",
        "first_name": "John",
        "last_name": "Manager",
        "role": "syndicate_manager"
    },
    "tokens": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    },
    "message": "User registered successfully"
}
```

### Syndicate Created (201)
```json
{
    "id": 1,
    "name": "Tech Ventures Syndicate",
    "manager": 1,
    "manager_username": "syndicate_manager1",
    "description": "A syndicate focused on early-stage technology investments...",
    "accredited": "Yes",
    "sector": "Technology, AI, Blockchain, SaaS, Fintech",
    "geography": "North America, Europe",
    "firm_name": "Tech Ventures LLC",
    "time_of_register": "2024-01-15T10:30:00Z"
}
```

### Syndicate List (200)
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Tech Ventures Syndicate",
            "manager": 1,
            "manager_username": "syndicate_manager1",
            "description": "A syndicate focused on early-stage technology investments...",
            "accredited": "Yes",
            "sector": "Technology, AI, Blockchain, SaaS, Fintech",
            "geography": "North America, Europe",
            "firm_name": "Tech Ventures LLC"
        }
    ]
}
```

## Error Responses

### Authentication Error (401)
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### Validation Error (400)
```json
{
    "name": ["This field is required."]
}
```

### Not Found (404)
```json
{
    "detail": "Not found."
}
```

## Testing Features

### Automatic Token Management
- Tokens are automatically extracted and stored in environment variables
- No need to manually copy/paste tokens between requests

### Test Scripts
- Each request includes test scripts for validation
- Automatic response time checks
- JSON validation
- Success/failure logging

### Environment Variables
- All dynamic values are stored as environment variables
- Easy to switch between different environments (dev, staging, prod)

## Tips and Best Practices

### 1. Token Management
- Tokens are automatically managed by the collection
- Access tokens expire after 5 hours
- Use the "Refresh Token" request when needed

### 2. Testing Workflow
1. Start with authentication (register/login)
2. Create a basic syndicate
3. Update with complete details
4. Test various operations
5. Run error handling tests

### 3. File Uploads
- Use the file upload requests for logo uploads
- Supported formats: PNG, JPG, JPEG
- Maximum file size: 10MB

### 4. Pagination
- Use `page` and `page_size` parameters for large datasets
- Default page size is 20 items

### 5. Error Handling
- Always check response status codes
- Review error messages for validation issues
- Use the error handling test scenarios

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check if access token is valid
   - Use "Refresh Token" request
   - Re-login if refresh token is expired

2. **400 Bad Request**
   - Check request body format
   - Validate required fields
   - Check field value constraints

3. **404 Not Found**
   - Verify syndicate/user ID exists
   - Check URL path is correct

4. **500 Internal Server Error**
   - Check Django server logs
   - Verify database connection
   - Check for server-side errors

### Server Issues

1. **Server Not Running**
   ```bash
   python manage.py runserver
   ```

2. **Database Issues**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

3. **Permission Issues**
   - Ensure user has correct role
   - Check Django admin permissions

## Advanced Usage

### Custom Environment Variables

You can add custom variables to the environment:

1. Go to **Environments** tab
2. Select **Syndicate API Environment**
3. Add new variables as needed

### Collection Runner

Use the Collection Runner for automated testing:

1. Click **Runner** button
2. Select the collection
3. Choose environment
4. Configure iterations and delays
5. Run the collection

### Pre-request Scripts

Add custom pre-request scripts for:
- Dynamic data generation
- Custom authentication
- Request modifications

### Test Scripts

Add custom test scripts for:
- Response validation
- Data extraction
- Custom assertions

## Support

For issues or questions:

1. Check Django server logs
2. Review API documentation
3. Test with cURL commands
4. Check database state

## API Reference

For complete API documentation, see:
- `API_DOCUMENTATION.md`
- `API_SUMMARY.md`
- `SYNDICATE_API_CURL_EXAMPLES.md`

---

**Happy Testing! 🚀**

This Postman collection provides a complete testing environment for the Syndicate Onboarding API. Use it to test all features, validate responses, and ensure your API is working correctly.
