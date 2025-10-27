# Quick API Test Commands

## Test 1: Register a User

Copy and paste this into PowerShell:

```powershell
$registerBody = @{
    username = "testuser"
    email = "test@example.com"
    password = "TestPass123!"
    password2 = "TestPass123!"
    first_name = "Test"
    last_name = "User"
    role = "investor"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/users/register/" -Method Post -Headers @{"Content-Type"="application/json"} -Body $registerBody | ConvertTo-Json
```

## Test 2: Login

```powershell
$loginBody = @{
    username = "testuser"
    password = "TestPass123!"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/users/login/" -Method Post -Headers @{"Content-Type"="application/json"} -Body $loginBody
$response | ConvertTo-Json
$token = $response.tokens.access
Write-Host "Token: $token"
```

## Test 3: Use Token

```powershell
$headers = @{
    "Authorization" = "Bearer $token"
}

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/users/me/" -Method Get -Headers $headers | ConvertTo-Json
```

## Or use cURL (simpler):

```bash
# Register
curl -X POST http://127.0.0.1:8000/api/users/register/ -H "Content-Type: application/json" -d "{\"username\":\"testuser\",\"email\":\"test@example.com\",\"password\":\"TestPass123!\",\"password2\":\"TestPass123!\",\"first_name\":\"Test\",\"last_name\":\"User\",\"role\":\"investor\"}"

# Login
curl -X POST http://127.0.0.1:8000/api/users/login/ -H "Content-Type: application/json" -d "{\"username\":\"testuser\",\"password\":\"TestPass123!\"}"
```

