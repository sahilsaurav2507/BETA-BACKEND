#!/usr/bin/env python3
"""
Test script to verify the feedback API is working with the new schema
"""

import requests
import json
import sys

def test_feedback_submission():
    """Test submitting feedback with the new schema"""
    
    # API endpoint
    url = "http://localhost:8000/feedback/submit"
    
    # Test data with required fields only
    test_data_minimal = {
        "email": "test@example.com",
        "name": "Test User",
        "biggest_hurdle": "A",
        "professional_fear": "A",
        "platform_impact": "This platform would revolutionize my career by providing easy access to share insights and connect with peers."
    }
    
    # Test data with all fields
    test_data_complete = {
        "email": "complete@example.com",
        "name": "Complete Test User",
        "biggest_hurdle": "B",
        "biggest_hurdle_other": None,
        "primary_motivation": "A",
        "time_consuming_part": "C",
        "professional_fear": "B",
        "monetization_considerations": "I have concerns about ethical implications and time investment required for monetization.",
        "professional_legacy": "I want to be remembered as someone who made legal knowledge accessible to everyone in the community.",
        "platform_impact": "Such a platform would allow me to reach thousands of people and establish thought leadership in my field."
    }
    
    print("🧪 Testing Feedback API Submission")
    print("=" * 50)
    
    # Test 1: Minimal required fields
    print("\n📝 Test 1: Submitting with required fields only...")
    try:
        response = requests.post(url, json=test_data_minimal, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Test 1 PASSED: Required fields submission successful")
        else:
            print("❌ Test 1 FAILED: Required fields submission failed")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Test 1 ERROR: Connection failed - {e}")
        return False
    
    # Test 2: All fields
    print("\n📝 Test 2: Submitting with all fields...")
    try:
        response = requests.post(url, json=test_data_complete, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Test 2 PASSED: Complete fields submission successful")
        else:
            print("❌ Test 2 FAILED: Complete fields submission failed")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Test 2 ERROR: Connection failed - {e}")
        return False
    
    # Test 3: Missing required fields
    print("\n📝 Test 3: Testing validation with missing required fields...")
    invalid_data = {
        "email": "test@example.com",
        # Missing name, biggest_hurdle, professional_fear, platform_impact
    }
    
    try:
        response = requests.post(url, json=invalid_data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 422:
            print("✅ Test 3 PASSED: Validation correctly rejected missing fields")
        else:
            print("❌ Test 3 FAILED: Validation should have rejected missing fields")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Test 3 ERROR: Connection failed - {e}")
        return False
    
    # Test 4: Short text fields
    print("\n📝 Test 4: Testing validation with short text fields...")
    short_text_data = {
        "email": "test@example.com",
        "name": "Test User",
        "biggest_hurdle": "A",
        "professional_fear": "A",
        "platform_impact": "Short",  # Less than 10 characters
        "monetization_considerations": "Brief"  # Less than 10 characters
    }
    
    try:
        response = requests.post(url, json=short_text_data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 422:
            print("✅ Test 4 PASSED: Validation correctly rejected short text fields")
        else:
            print("❌ Test 4 FAILED: Validation should have rejected short text fields")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Test 4 ERROR: Connection failed - {e}")
        return False
    
    print("\n🎉 All tests completed!")
    return True

def check_server_status():
    """Check if the server is running"""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            return True
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server is not accessible: {e}")
        print("💡 Make sure the FastAPI server is running on port 8000")
        return False

if __name__ == "__main__":
    print("🔍 Checking server status...")
    if check_server_status():
        test_feedback_submission()
    else:
        print("\n🚨 Please start the backend server first:")
        print("   cd BetajoiningBackend")
        print("   uvicorn app.main:app --reload --port 8000")
        sys.exit(1)
