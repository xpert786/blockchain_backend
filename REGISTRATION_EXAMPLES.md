# User Registration API - Correct Examples

## ✅ Basic Registration (Minimal Fields)

```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!"
  }'
```

## ✅ Register Syndicate Manager

```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "syndicate_manager",
    "email": "manager@example.com",
    "first_name": "John",
    "last_name": "Manager",
    "role": "syndicate_manager",
    "password": "Pass123!",
    "password2": "Pass123!"
  }'
```

## ✅ Register Investor

```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "investor1",
    "email": "investor@example.com",
    "first_name": "Jane",
    "last_name": "Investor",
    "role": "investor",
    "password": "InvestorPass123!",
    "password2": "InvestorPass123!"
  }'
```

## ✅ Register Admin

```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin_user",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "role": "admin",
    "password": "AdminPass123!",
    "password2": "AdminPass123!"
  }'
```

---

## ❌ Common Mistakes

### Mistake 1: Including Response Fields
**WRONG:**
```json
{
  "user": {
    "id": 5,
    "username": "manager"
  },
  "tokens": { ... },
  "message": "..."
}
```

**RIGHT:**
```json
{
  "username": "manager",
  "email": "manager@example.com",
  "password": "Pass123!",
  "password2": "Pass123!"
}
```

### Mistake 2: Password Mismatch
**WRONG:**
```json
{
  "password": "Pass123!",
  "password2": "DifferentPass123!"
}
```

**Response:**
```json
{
  "password": ["Password fields didn't match."]
}
```

### Mistake 3: Weak Password
**WRONG:**
```json
{
  "password": "123",
  "password2": "123"
}
```

**Response:**
```json
{
  "password": [
    "This password is too short. It must contain at least 8 characters.",
    "This password is too common.",
    "This password is entirely numeric."
  ]
}
```

### Mistake 4: Missing Required Fields
**WRONG:**
```json
{
  "username": "testuser"
}
```

**Response:**
```json
{
  "email": ["This field is required."],
  "password": ["This field is required."],
  "password2": ["This field is required."]
}
```

---

## 📝 Field Specifications

### Username
- **Required:** Yes
- **Type:** String
- **Constraints:** Unique, alphanumeric + underscores
- **Example:** `"syndicate_manager"`, `"investor1"`, `"john_doe"`

### Email
- **Required:** Yes
- **Type:** String (valid email format)
- **Constraints:** Valid email address
- **Example:** `"manager@example.com"`

### Password
- **Required:** Yes
- **Type:** String
- **Constraints:** 
  - Minimum 8 characters
  - Not too common
  - Not entirely numeric
  - Not too similar to username
- **Good Examples:** `"SecurePass123!"`, `"MyStr0ng!Pass"`, `"Blockchain2024!"`
- **Bad Examples:** `"password"`, `"12345678"`, `"qwerty"`

### Password2
- **Required:** Yes
- **Type:** String
- **Constraints:** Must match `password` exactly

### First Name
- **Required:** No
- **Type:** String
- **Example:** `"John"`, `"Jane"`

### Last Name
- **Required:** No
- **Type:** String
- **Example:** `"Doe"`, `"Smith"`

### Role
- **Required:** No
- **Type:** String (enum)
- **Valid Values:**
  - `"admin"` - Full system access
  - `"syndicate_manager"` - Can create and manage syndicates
  - `"investor"` - Can view syndicates and submit KYC
- **Default:** None (if not provided)
- **Example:** `"syndicate_manager"`

---

## 🔄 Complete Flow Example

### Step 1: Register
```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "manager1",
    "email": "manager1@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "role": "syndicate_manager"
  }'
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "manager1",
    "email": "manager1@example.com",
    "first_name": "",
    "last_name": "",
    "role": "syndicate_manager",
    "is_active": true,
    "is_staff": false,
    "date_joined": "2024-12-13T10:30:00Z"
  },
  "tokens": {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "message": "User registered successfully"
}
```

### Step 2: Save the Token
```bash
# Save access token to variable (Bash)
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Or in PowerShell
$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Step 3: Use the Token
```bash
curl -X GET http://127.0.0.1:8000/api/users/me/ \
  -H "Authorization: Bearer $TOKEN"
```

### Step 4: Create a Syndicate
```bash
curl -X POST http://127.0.0.1:8000/api/syndicates/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Ventures",
    "description": "Technology investments",
    "accredited": "Yes",
    "sector": "Technology, AI",
    "firm_name": "Tech Ventures LLC"
  }'
```

---

## 🎯 Quick Copy-Paste Commands

### Windows PowerShell
```powershell
# Register
$body = '{"username":"manager1","email":"manager1@example.com","password":"Pass123!","password2":"Pass123!","role":"syndicate_manager"}' 
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/users/register/" -Method Post -Headers @{"Content-Type"="application/json"} -Body $body | ConvertTo-Json

# Login
$loginBody = '{"username":"manager1","password":"Pass123!"}'
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/users/login/" -Method Post -Headers @{"Content-Type"="application/json"} -Body $loginBody
$token = $response.tokens.access
Write-Host "Token: $token"
```

### Windows Command Prompt (cURL)
```bash
curl -X POST "http://127.0.0.1:8000/api/users/register/" -H "Content-Type: application/json" -d "{\"username\":\"manager1\",\"email\":\"manager1@example.com\",\"password\":\"Pass123!\",\"password2\":\"Pass123!\",\"role\":\"syndicate_manager\"}"

curl -X POST "http://127.0.0.1:8000/api/users/login/" -H "Content-Type: application/json" -d "{\"username\":\"manager1\",\"password\":\"Pass123!\"}"
```

### Bash/Linux/Mac (cURL)
```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"manager1","email":"manager1@example.com","password":"Pass123!","password2":"Pass123!","role":"syndicate_manager"}'

curl -X POST http://127.0.0.1:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"manager1","password":"Pass123!"}'
```

---

## 🔍 Debugging Tips

1. **Check server logs** in the terminal where Django is running
2. **Verify JSON syntax** - use a JSON validator
3. **Check Content-Type header** - must be `application/json`
4. **Ensure passwords match** - `password` must equal `password2`
5. **Use strong passwords** - at least 8 characters, not too common

---

## 📚 Related Documentation

- Full API docs: `API_DOCUMENTATION.md`
- Syndicate examples: `SYNDICATE_API_CURL_EXAMPLES.md`
- Setup guide: `SETUP_GUIDE.md`

