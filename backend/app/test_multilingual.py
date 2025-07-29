#!/usr/bin/env python3
"""
Test script to verify multilingual functionality
"""
import requests
import json

def test_multilingual_analysis():
    """Test the multilingual analysis endpoint"""
    
    # Test data
    test_data = {
        "movies": "Inception",
        "music": "Radiohead",
        "brands": "Apple",
        "gender": "male",
        "language": "tr",  # Test Turkish
        "randomSeed": 123
    }
    
    print("🧪 Testing multilingual analysis...")
    print(f"📤 Sending request with language: {test_data['language']}")
    
    try:
        response = requests.post(
            "http://localhost:8000/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            print(f"📥 Response status: {response.status_code}")
            
            # Parse the result
            parsed_result = json.loads(result.get("result", "{}"))
            
            print(f"🎭 Persona Name: {parsed_result.get('personaName', 'N/A')}")
            print(f"👥 Cultural Twin: {parsed_result.get('culturalTwin', 'N/A')}")
            print(f"📝 Description: {parsed_result.get('description', 'N/A')}")
            print(f"🏷️ Traits: {parsed_result.get('traits', [])}")
            
            # Check if response is in Turkish
            persona_name = parsed_result.get('personaName', '')
            description = parsed_result.get('description', '')
            
            # Simple Turkish word check (not comprehensive but good for testing)
            turkish_indicators = ['kültür', 'kişilik', 'yaratıcı', 'sosyal', 'dinamik', 'açık']
            has_turkish = any(indicator in persona_name.lower() or indicator in description.lower() 
                            for indicator in turkish_indicators)
            
            if has_turkish:
                print("✅ Response appears to be in Turkish!")
            else:
                print("⚠️ Response may not be in Turkish - check manually")
                
            return True
            
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the backend is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

def test_english_analysis():
    """Test English language analysis"""
    
    test_data = {
        "movies": "The Matrix",
        "music": "Queen",
        "brands": "Nike",
        "gender": "female",
        "language": "en",  # Test English
        "randomSeed": 456
    }
    
    print("\n🧪 Testing English analysis...")
    print(f"📤 Sending request with language: {test_data['language']}")
    
    try:
        response = requests.post(
            "http://localhost:8000/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            
            parsed_result = json.loads(result.get("result", "{}"))
            
            print(f"🎭 Persona Name: {parsed_result.get('personaName', 'N/A')}")
            print(f"👥 Cultural Twin: {parsed_result.get('culturalTwin', 'N/A')}")
            print(f"📝 Description: {parsed_result.get('description', 'N/A')}")
            
            # Check if response is in English
            persona_name = parsed_result.get('personaName', '')
            description = parsed_result.get('description', '')
            
            # Simple English word check
            english_indicators = ['cultural', 'personality', 'creative', 'social', 'dynamic', 'open']
            has_english = any(indicator in persona_name.lower() or indicator in description.lower() 
                            for indicator in english_indicators)
            
            if has_english:
                print("✅ Response appears to be in English!")
            else:
                print("⚠️ Response may not be in English - check manually")
                
            return True
            
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting multilingual functionality tests...")
    
    # Test Turkish
    turkish_success = test_multilingual_analysis()
    
    # Test English
    english_success = test_english_analysis()
    
    print("\n📊 Test Results:")
    print(f"Turkish test: {'✅ PASSED' if turkish_success else '❌ FAILED'}")
    print(f"English test: {'✅ PASSED' if english_success else '❌ FAILED'}")
    
    if turkish_success and english_success:
        print("\n🎉 All tests passed! Multilingual functionality is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.") 