#!/usr/bin/env python3
"""
Test script to verify the feedback list API is working
"""

import requests
import json
import sys

def test_feedback_list():
    """Test fetching feedback list"""
    
    # API endpoint
    url = "http://localhost:8000/feedback?page=1&page_size=20"
    
    print("🧪 Testing Feedback List API")
    print("=" * 50)
    
    try:
        # You'll need to add admin authentication headers here
        # For now, let's test without auth to see the error
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Feedback list API working!")
            data = response.json()
            print(f"📊 Found {len(data.get('feedback', []))} feedback records")
            
            # Show first record structure
            if data.get('feedback'):
                first_record = data['feedback'][0]
                print("\n📝 Sample record structure:")
                for key, value in first_record.items():
                    print(f"   {key}: {value}")
        else:
            print("❌ Feedback list API failed")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    return True

def test_feedback_stats():
    """Test fetching feedback stats"""
    
    # API endpoint
    url = "http://localhost:8000/feedback/stats"
    
    print("\n🧪 Testing Feedback Stats API")
    print("=" * 50)
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Feedback stats API working!")
        else:
            print("❌ Feedback stats API failed")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_feedback_list()
    test_feedback_stats()
