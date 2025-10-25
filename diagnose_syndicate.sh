#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYwMzU3MjU5LCJpYXQiOjE3NjAzMzkyNTksImp0aSI6IjBiMmQ4MDNjYmIxNzRlMzI5MDgwMjI0NTMwMTZjYmUwIiwidXNlcl9pZCI6IjUifQ.-G7G0IFpZBT0k-TcvY0pSTfxne5rMILKRojLrwc8aB0"
BASE_URL="http://127.0.0.1:8000/api"

echo "=========================================="
echo "Syndicate Diagnostic Script"
echo "=========================================="

echo -e "\n1. Checking current user info..."
curl -s -X GET "$BASE_URL/users/me/" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

echo -e "\n2. Listing all syndicates..."
curl -s -X GET "$BASE_URL/syndicates/" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

echo -e "\n3. Listing MY syndicates..."
curl -s -X GET "$BASE_URL/syndicates/my_syndicates/" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

echo -e "\n4. Checking if syndicate ID 7 exists..."
curl -s -X GET "$BASE_URL/syndicates/7/" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

echo -e "\n=========================================="
echo "Diagnostic Complete!"
echo "=========================================="

