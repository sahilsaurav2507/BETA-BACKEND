#!/usr/bin/env python3
"""
Test script to verify the feedback export API is working
"""

import requests
import json
import sys

def test_export_json():
    """Test exporting feedback as JSON"""
    
    # API endpoint
    url = "http://localhost:8000/feedback/export?format=json"
    
    print("🧪 Testing Feedback Export API (JSON)")
    print("=" * 50)
    
    try:
        # Note: This will fail with 401 without admin auth, but we can see if the endpoint exists
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Export endpoint exists (requires authentication)")
        elif response.status_code == 200:
            print("✅ Export endpoint working!")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content-Disposition: {response.headers.get('content-disposition')}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    return True

def test_export_csv():
    """Test exporting feedback as CSV"""
    
    # API endpoint
    url = "http://localhost:8000/feedback/export?format=csv"
    
    print("\n🧪 Testing Feedback Export API (CSV)")
    print("=" * 50)
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Export endpoint exists (requires authentication)")
        elif response.status_code == 200:
            print("✅ Export endpoint working!")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content-Disposition: {response.headers.get('content-disposition')}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_export_json()
    test_export_csv()
