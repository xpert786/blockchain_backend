import requests
import json

def test_cors_fix():
    base_url = "http://192.168.0.146:8000"
    
    print("=== Testing CORS Preflight Fix ===")
    
    # Test 1: CORS Preflight Request
    try:
        response = requests.options(f"{base_url}/api/users/register/", 
                                  headers={
                                      'Origin': 'http://192.168.0.125:5173',
                                      'Access-Control-Request-Method': 'POST',
                                      'Access-Control-Request-Headers': 'Content-Type'
                                  })
        print(f"Preflight Status: {response.status_code}")
        print(f"CORS Headers:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        
        if response.status_code == 200:
            print("✅ Preflight request successful!")
        else:
            print("❌ Preflight request failed")
            
    except Exception as e:
        print(f"Preflight Error: {e}")
    
    print("\n=== Testing Registration Request ===")
    # Test 2: Actual Registration Request
    try:
        data = {
            "username": f"cors_test_user_{hash(str(time.time())) % 10000}",
            "email": f"cors_test_{hash(str(time.time())) % 10000}@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "first_name": "CORS",
            "last_name": "Test"
        }
        
        response = requests.post(f"{base_url}/api/users/register/", 
                               json=data,
                               headers={
                                   'Origin': 'http://192.168.0.125:5173',
                                   'Content-Type': 'application/json'
                               })
        
        print(f"Registration Status: {response.status_code}")
        print(f"Response Headers:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            response_data = response.json()
            print(f"User ID: {response_data.get('user_id')}")
        else:
            print(f"❌ Registration failed: {response.text}")
            
    except Exception as e:
        print(f"Registration Error: {e}")

if __name__ == "__main__":
    import time
    test_cors_fix()
