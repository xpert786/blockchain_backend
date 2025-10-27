import requests

def test_simple_cors():
    base_url = "http://192.168.0.146:8000"
    
    print("=== Testing Simple CORS ===")
    
    # Test preflight request
    try:
        response = requests.options(f"{base_url}/api/users/register/", 
                                  headers={
                                      'Origin': 'http://192.168.0.125:5173',
                                      'Access-Control-Request-Method': 'POST',
                                      'Access-Control-Request-Headers': 'Content-Type'
                                  })
        
        print(f"Status: {response.status_code}")
        print("All Headers:")
        for header, value in response.headers.items():
            print(f"  {header}: {value}")
        
        # Check for CORS headers
        cors_headers = [h for h in response.headers.keys() if 'access-control' in h.lower()]
        if cors_headers:
            print(f"\n✅ CORS Headers Found: {cors_headers}")
        else:
            print("\n❌ No CORS Headers Found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple_cors()
