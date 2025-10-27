import requests
import json

def test_server_status():
    base_url = "http://192.168.0.146:8000"
    
    print("=== Testing Server Status ===")
    
    # Test 1: Server is running
    try:
        response = requests.get(f"{base_url}/api/users/")
        print(f"✅ Server is running (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False
    
    # Test 2: Registration endpoint
    try:
        data = {
            "username": f"postman_test_{hash(str(123)) % 10000}",
            "email": f"postman_test_{hash(str(123)) % 10000}@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "first_name": "Postman",
            "last_name": "Test"
        }
        
        response = requests.post(f"{base_url}/api/users/register/", json=data)
        print(f"✅ Registration endpoint working (Status: {response.status_code})")
        
        if response.status_code == 201:
            response_data = response.json()
            print(f"   User ID: {response_data.get('user_id')}")
            print(f"   Access Token: {response_data.get('tokens', {}).get('access', 'N/A')[:50]}...")
            return response_data.get('tokens', {}).get('access')
        
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        return None
    
    # Test 3: CORS preflight
    try:
        response = requests.options(f"{base_url}/api/users/register/", 
                                  headers={
                                      'Origin': 'http://192.168.0.125:5173',
                                      'Access-Control-Request-Method': 'POST'
                                  })
        print(f"✅ CORS preflight working (Status: {response.status_code})")
        
        # Check for CORS headers
        cors_headers = [h for h in response.headers.keys() if 'access-control' in h.lower()]
        if cors_headers:
            print(f"   CORS Headers: {cors_headers}")
        else:
            print("   ⚠️  No CORS headers found")
            
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
    
    return None

if __name__ == "__main__":
    access_token = test_server_status()
    
    if access_token:
        print(f"\n🎉 Server is ready for Postman testing!")
        print(f"📋 Use this access token in Postman: {access_token[:50]}...")
        print(f"\n📖 Follow the POSTMAN_TESTING_GUIDE.md for step-by-step testing")
    else:
        print(f"\n❌ Server needs to be started or configured")
        print(f"🚀 Run: python manage.py runserver 192.168.0.146:8000")
