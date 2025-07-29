#!/usr/bin/env python3
"""
Test script to verify multilingual functionality with fallback responses
"""
import requests
import json
import os

def test_multilingual_fallback():
    """Test the multilingual analysis with fallback responses"""
    
    # Test data for Turkish
    test_data_tr = {
        "movies": "Inception",
        "music": "Radiohead",
        "brands": "Apple",
        "gender": "male",
        "language": "tr",  # Test Turkish
        "randomSeed": 123
    }
    
    print("🧪 Testing Turkish multilingual analysis (fallback)...")
    print(f"📤 Sending request with language: {test_data_tr['language']}")
    
    try:
        response = requests.post(
            "http://localhost:8000/analyze",
            json=test_data_tr,
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
            
            # Simple Turkish word check
            turkish_indicators = ['kültür', 'kişilik', 'yaratıcı', 'sosyal', 'dinamik', 'açık', 'keşifçi', 'meraklı']
            has_turkish = any(indicator in persona_name.lower() or indicator in description.lower() 
                            for indicator in turkish_indicators)
            
            if has_turkish:
                print("✅ Response appears to be in Turkish!")
                return True
            else:
                print("⚠️ Response may not be in Turkish - check manually")
                return False
                
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

def test_english_fallback():
    """Test English language analysis with fallback"""
    
    test_data_en = {
        "movies": "The Matrix",
        "music": "Queen",
        "brands": "Nike",
        "gender": "female",
        "language": "en",  # Test English
        "randomSeed": 456
    }
    
    print("\n🧪 Testing English analysis (fallback)...")
    print(f"📤 Sending request with language: {test_data_en['language']}")
    
    try:
        response = requests.post(
            "http://localhost:8000/analyze",
            json=test_data_en,
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
            english_indicators = ['cultural', 'personality', 'creative', 'social', 'dynamic', 'open', 'explorer', 'curious']
            has_english = any(indicator in persona_name.lower() or indicator in description.lower() 
                            for indicator in english_indicators)
            
            if has_english:
                print("✅ Response appears to be in English!")
                return True
            else:
                print("⚠️ Response may not be in English - check manually")
                return False
                
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

def test_all_languages():
    """Test all available languages in locales"""
    
    # Get all available languages from the LANGUAGE_MAPPING
    languages = ["en", "tr", "es", "fr", "de", "hi", "zh", "it"]
    
    print(f"\n🧪 Testing all {len(languages)} languages...")
    
    results = {}
    
    for lang in languages:
        test_data = {
            "movies": "Inception",
            "music": "Radiohead",
            "brands": "Apple",
            "gender": "male",
            "language": lang,
            "randomSeed": 123
        }
        
        print(f"\n📤 Testing language: {lang}")
        
        try:
            response = requests.post(
                "http://localhost:8000/analyze",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                parsed_result = json.loads(result.get("result", "{}"))
                
                persona_name = parsed_result.get('personaName', '')
                description = parsed_result.get('description', '')
                
                print(f"✅ {lang}: {persona_name}")
                print(f"   Description: {description[:50]}...")
                
                results[lang] = "SUCCESS"
            else:
                print(f"❌ {lang}: Failed with status {response.status_code}")
                results[lang] = "FAILED"
                
        except Exception as e:
            print(f"❌ {lang}: Error - {e}")
            results[lang] = "ERROR"
    
    return results

if __name__ == "__main__":
    print("🚀 Starting multilingual functionality tests...")
    
    # Test Turkish
    turkish_success = test_multilingual_fallback()
    
    # Test English
    english_success = test_english_fallback()
    
    # Test all languages
    all_languages_results = test_all_languages()
    
    print("\n📊 Test Results:")
    print(f"Turkish test: {'✅ PASSED' if turkish_success else '❌ FAILED'}")
    print(f"English test: {'✅ PASSED' if english_success else '❌ FAILED'}")
    
    print("\n🌍 All Languages Test Results:")
    for lang, result in all_languages_results.items():
        print(f"  {lang}: {result}")
    
    successful_langs = sum(1 for result in all_languages_results.values() if result == "SUCCESS")
    total_langs = len(all_languages_results)
    
    print(f"\n📈 Success Rate: {successful_langs}/{total_langs} languages working")
    
    if turkish_success and english_success and successful_langs >= 6:
        print("\n🎉 Multilingual functionality is working correctly!")
        print("✅ All major languages are supported")
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.") 