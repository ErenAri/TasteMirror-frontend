#!/usr/bin/env python3
"""
Simple test to check if server is responding
"""
import requests
import json

def test_server_connection():
    """Test if server is responding"""
    
    print("🧪 Testing server connection...")
    
    try:
        # Test basic connection
        response = requests.get("http://localhost:8000/docs", timeout=10)
        print(f"✅ Server is responding! Status: {response.status_code}")
        
        # Test analyze endpoint with minimal data
        test_data = {
            "movies": "Inception",
            "music": "Radiohead", 
            "brands": "Apple",
            "gender": "male",
            "language": "en",
            "randomSeed": 123
        }
        
        print("🧪 Testing analyze endpoint...")
        response = requests.post(
            "http://localhost:8000/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Analyze endpoint working!")
            print(f"📥 Response status: {response.status_code}")
            
            # Check if result contains expected fields
            if "result" in result:
                parsed_result = json.loads(result.get("result", "{}"))
                print(f"🎭 Persona Name: {parsed_result.get('personaName', 'N/A')}")
                print(f"👥 Cultural Twin: {parsed_result.get('culturalTwin', 'N/A')}")
                print(f"📝 Description: {parsed_result.get('description', 'N/A')[:100]}...")
                return True
            else:
                print("❌ Response missing 'result' field")
                return False
        else:
            print(f"❌ Analyze endpoint failed with status: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the backend is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting simple server test...")
    success = test_server_connection()
    
    if success:
        print("\n🎉 Server test passed! Multilingual functionality should work.")
    else:
        print("\n⚠️ Server test failed. Please check the server.") 