# Syndicate API - cURL Examples

## Prerequisites
First, you need to register and login to get a JWT token.

---

## Step 1: Register a User (Syndicate Manager)

```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"syndicate_manager1\",
    \"email\": \"manager@example.com\",
    \"password\": \"SecurePass123!\",
    \"password2\": \"SecurePass123!\",
    \"first_name\": \"John\",
    \"last_name\": \"Manager\",
    \"role\": \"syndicate_manager\"
  }"
```

**Response:**
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

**💡 Save the `access` token - you'll need it for all subsequent requests!**

---

## Step 2: Login (if already registered)

```bash
curl -X POST http://127.0.0.1:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"syndicate_manager1\",
    \"password\": \"SecurePass123!\"
  }"
```

---

## Syndicate API Endpoints

### 1. Create a Syndicate

```bash
curl -X POST http://127.0.0.1:8000/api/syndicates/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Tech Ventures Syndicate\",
    \"description\": \"A syndicate focused on early-stage technology investments, specializing in AI, blockchain, and SaaS companies.\",
    \"accredited\": \"Yes\",
    \"sector\": \"Technology, AI, Blockchain, SaaS, Fintech\",
    \"geography\": \"North America, Europe\",
    \"lp_network\": \"Angel investors, VCs, Family offices\",
    \"enable_lp_network\": \"Yes\",
    \"firm_name\": \"Tech Ventures LLC\",
    \"team_member\": \"John Manager (Managing Partner), Sarah Smith (Investment Analyst), Mike Johnson (Legal Counsel)\",
    \"Risk_Regulatory_Attestation\": \"This syndicate complies with all SEC regulations and operates under Regulation D, Rule 506(c). All investors must be accredited.\",
    \"jurisdictional_requirements\": \"United States (all 50 states), Canada, United Kingdom, European Union\",
    \"additional_compliance_policies\": \"KYC/AML policies enforced, Annual audits conducted, GDPR compliant, Regular compliance training for team members\"
  }"
```

**Response (201 Created):**
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
  "firm_name": "Tech Ventures LLC"
}
```

### 2. Create Syndicate (Minimal Fields)

```bash
curl -X POST http://127.0.0.1:8000/api/syndicates/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Healthcare Syndicate\",
    \"description\": \"Investing in healthcare and biotech\",
    \"accredited\": \"Yes\",
    \"sector\": \"Healthcare, Biotech\",
    \"firm_name\": \"Healthcare Investments LLC\"
  }"
```

### 3. List All Syndicates

```bash
curl -X GET http://127.0.0.1:8000/api/syndicates/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
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
      "manager_details": {
        "id": 1,
        "username": "syndicate_manager1",
        "email": "manager@example.com",
        "first_name": "John",
        "last_name": "Manager",
        "role": "syndicate_manager"
      },
      "description": "A syndicate focused on early-stage technology investments...",
      "accredited": "Yes",
      "sector": "Technology, AI, Blockchain, SaaS, Fintech",
      "geography": "North America, Europe",
      "firm_name": "Tech Ventures LLC"
    }
  ]
}
```

### 4. List Syndicates with Pagination

```bash
# Page 1, 5 items per page
curl -X GET "http://127.0.0.1:8000/api/syndicates/?page=1&page_size=5" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Page 2
curl -X GET "http://127.0.0.1:8000/api/syndicates/?page=2" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Get Syndicate by ID

```bash
curl -X GET http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "id": 1,
  "name": "Tech Ventures Syndicate",
  "manager": 1,
  "manager_username": "syndicate_manager1",
  "manager_details": {
    "id": 1,
    "username": "syndicate_manager1",
    "email": "manager@example.com",
    "first_name": "John",
    "last_name": "Manager"
  },
  "description": "A syndicate focused on early-stage technology investments...",
  "accredited": "Yes",
  "sector": "Technology, AI, Blockchain, SaaS, Fintech",
  "geography": "North America, Europe",
  "lp_network": "Angel investors, VCs, Family offices",
  "enable_lp_network": "Yes",
  "firm_name": "Tech Ventures LLC",
  "logo": null,
  "team_member": "John Manager (Managing Partner), Sarah Smith...",
  "Risk_Regulatory_Attestation": "This syndicate complies with all SEC regulations...",
  "jurisdictional_requirements": "United States (all 50 states)...",
  "additional_compliance_policies": "KYC/AML policies enforced..."
}
```

### 6. Update Syndicate (Full Update - PUT)

```bash
curl -X PUT http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Tech Ventures Syndicate (Updated)\",
    \"manager\": 1,
    \"description\": \"Updated description - Now focusing on late-stage tech companies\",
    \"accredited\": \"Yes\",
    \"sector\": \"Technology, AI, Enterprise SaaS\",
    \"geography\": \"Global\",
    \"firm_name\": \"Tech Ventures LLC\"
  }"
```

### 7. Update Syndicate (Partial Update - PATCH)

```bash
# Update only specific fields
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"Updated description only\",
    \"geography\": \"North America, Europe, Asia\"
  }"
```

### 8. Update Syndicate Sectors

```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"sector\": \"Technology, AI, Machine Learning, Blockchain, Fintech, Cybersecurity\"
  }"
```

### 9. Get My Syndicates (Current User's Syndicates)

```bash
curl -X GET http://127.0.0.1:8000/api/syndicates/my_syndicates/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Tech Ventures Syndicate",
    "manager": 1,
    "manager_username": "syndicate_manager1",
    "description": "A syndicate focused on early-stage technology investments...",
    "accredited": "Yes"
  }
]
```

### 10. Get Syndicate Details

```bash
curl -X GET http://127.0.0.1:8000/api/syndicates/1/details/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 11. Delete Syndicate

```bash
curl -X DELETE http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (204 No Content)**

---

## Upload Syndicate Logo (with File)

For file uploads, use multipart/form-data:

```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "logo=@/path/to/your/logo.png"
```

Or combine with other fields:

```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "logo=@/path/to/your/logo.png" \
  -F "name=Tech Ventures Syndicate" \
  -F "description=Updated with new logo"
```

---

## Advanced Examples

### 1. Create Multiple Syndicates (Script)

Save as `create_syndicates.sh`:

```bash
#!/bin/bash

TOKEN="YOUR_ACCESS_TOKEN_HERE"

# Create first syndicate
curl -X POST http://127.0.0.1:8000/api/syndicates/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Healthcare Innovation Fund",
    "description": "Investing in healthcare technology and biotech",
    "accredited": "Yes",
    "sector": "Healthcare, Biotech, Medical Devices",
    "geography": "North America",
    "firm_name": "Healthcare Innovations LLC"
  }'

# Create second syndicate
curl -X POST http://127.0.0.1:8000/api/syndicates/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Green Energy Syndicate",
    "description": "Sustainable energy investments",
    "accredited": "Yes",
    "sector": "Clean Energy, Solar, Wind, Battery Tech",
    "geography": "Global",
    "firm_name": "Green Energy Partners"
  }'

# Create third syndicate
curl -X POST http://127.0.0.1:8000/api/syndicates/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fintech Ventures",
    "description": "Next-generation financial services",
    "accredited": "Yes",
    "sector": "Fintech, Blockchain, DeFi, Payments",
    "geography": "North America, Europe, Asia",
    "firm_name": "Fintech Ventures LP"
  }'
```

Run with: `bash create_syndicates.sh`

### 2. Get User's Syndicates by User ID

```bash
# Get syndicates for user ID 1
curl -X GET http://127.0.0.1:8000/api/users/1/syndicates/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Create Syndicate with Manager Assignment

```bash
# Assign specific manager (must have permission)
curl -X POST http://127.0.0.1:8000/api/syndicates/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Real Estate Syndicate\",
    \"manager\": 2,
    \"description\": \"Commercial real estate investments\",
    \"accredited\": \"Yes\",
    \"sector\": \"Real Estate, Commercial Property\",
    \"firm_name\": \"Real Estate Partners LLC\"
  }"
```

---

## Refresh Token Example

When your access token expires (after 5 hours):

```bash
curl -X POST http://127.0.0.1:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh\": \"YOUR_REFRESH_TOKEN\"
  }"
```

**Response:**
```json
{
  "access": "NEW_ACCESS_TOKEN"
}
```

---

## Error Handling Examples

### 1. Missing Authorization (401)

```bash
curl -X GET http://127.0.0.1:8000/api/syndicates/
# Response: {"detail": "Authentication credentials were not provided."}
```

### 2. Invalid Token (401)

```bash
curl -X GET http://127.0.0.1:8000/api/syndicates/ \
  -H "Authorization: Bearer invalid_token"
# Response: {"detail": "Given token not valid for any token type"}
```

### 3. Syndicate Not Found (404)

```bash
curl -X GET http://127.0.0.1:8000/api/syndicates/999/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
# Response: {"detail": "Not found."}
```

### 4. Validation Error (400)

```bash
curl -X POST http://127.0.0.1:8000/api/syndicates/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"Missing required name field\"
  }"
# Response: {"name": ["This field is required."]}
```

---

## PowerShell Examples (Windows)

### Create Syndicate (PowerShell)

```powershell
$token = "YOUR_ACCESS_TOKEN"
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}
$body = @{
    name = "Tech Ventures Syndicate"
    description = "Technology investments"
    accredited = "Yes"
    sector = "Technology, AI"
    firm_name = "Tech Ventures LLC"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/syndicates/" `
    -Method Post `
    -Headers $headers `
    -Body $body
```

### List Syndicates (PowerShell)

```powershell
$token = "YOUR_ACCESS_TOKEN"
$headers = @{
    "Authorization" = "Bearer $token"
}

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/syndicates/" `
    -Method Get `
    -Headers $headers
```

---

## Testing Checklist

- [ ] Register a syndicate manager user
- [ ] Login and save access token
- [ ] Create a syndicate with minimal fields
- [ ] Create a syndicate with all fields
- [ ] List all syndicates
- [ ] Get specific syndicate by ID
- [ ] Get my syndicates
- [ ] Update syndicate (PATCH)
- [ ] Upload syndicate logo
- [ ] Delete syndicate
- [ ] Test with expired token
- [ ] Test without authentication

---

## Quick Test Script

Save as `test_syndicate_api.sh`:

```bash
#!/bin/bash

BASE_URL="http://127.0.0.1:8000/api"

echo "1. Registering user..."
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testmanager",
    "email": "test@example.com",
    "password": "TestPass123!",
    "password2": "TestPass123!",
    "first_name": "Test",
    "last_name": "Manager",
    "role": "syndicate_manager"
  }')

TOKEN=$(echo $REGISTER_RESPONSE | grep -o '"access":"[^"]*' | cut -d'"' -f4)
echo "Access Token: $TOKEN"

echo -e "\n2. Creating syndicate..."
curl -s -X POST $BASE_URL/syndicates/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Syndicate",
    "description": "Test syndicate created via API",
    "accredited": "Yes",
    "sector": "Technology",
    "firm_name": "Test Firm"
  }' | python -m json.tool

echo -e "\n3. Listing syndicates..."
curl -s -X GET $BASE_URL/syndicates/ \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

echo -e "\n4. Getting my syndicates..."
curl -s -X GET $BASE_URL/syndicates/my_syndicates/ \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

Run with: `bash test_syndicate_api.sh`

---

## Tips

1. **Save your token**: Store the access token in a variable for easier testing
   ```bash
   TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
   curl -H "Authorization: Bearer $TOKEN" ...
   ```

2. **Pretty print JSON**: Use `jq` or `python -m json.tool`
   ```bash
   curl ... | python -m json.tool
   curl ... | jq .
   ```

3. **Save response**: Save responses to files for inspection
   ```bash
   curl ... > response.json
   ```

4. **Verbose output**: Add `-v` flag to see full request/response
   ```bash
   curl -v -X GET ...
   ```

---

**Happy Testing! 🚀**

