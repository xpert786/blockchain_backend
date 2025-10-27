#!/bin/bash

echo "=========================================="
echo "Testing Blockchain Admin API - Login"
echo "=========================================="

BASE_URL="http://127.0.0.1:8000/api"

echo -e "\n1. Testing if server is running..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" $BASE_URL/users/

echo -e "\n2. Registering a new user..."
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser123",
    "email": "testuser123@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "investor"
  }')

echo "$REGISTER_RESPONSE" | python -m json.tool 2>/dev/null || echo "$REGISTER_RESPONSE"

echo -e "\n3. Logging in with the new user..."
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser123",
    "password": "SecurePass123!"
  }')

echo "$LOGIN_RESPONSE" | python -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"

# Extract token
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access":"[^"]*' | cut -d'"' -f4)

if [ ! -z "$TOKEN" ]; then
    echo -e "\n✅ Success! Access Token: $TOKEN"
    echo -e "\n4. Testing authenticated endpoint..."
    curl -s -X GET $BASE_URL/users/me/ \
      -H "Authorization: Bearer $TOKEN" | python -m json.tool 2>/dev/null
else
    echo -e "\n❌ Login failed!"
fi

echo -e "\n=========================================="


