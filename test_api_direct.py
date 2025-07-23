#!/usr/bin/env python3
"""
Direct API test to verify the backend is working correctly
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_registration_and_stats():
    """Test user registration and stats retrieval"""
    
    print("=== DIRECT API TEST ===")
    print()
    
    # Test 1: Register a new user
    print("1. Testing user registration...")
    
    registration_data = {
        "name": "Test User API",
        "email": f"testuser{int(__import__('time').time())}@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=registration_data)
        print(f"Registration Status: {response.status_code}")
        
        if response.status_code == 201:
            user_data = response.json()
            print(f"Registration Response: {json.dumps(user_data, indent=2)}")
            
            # Test 2: Login with the new user
            print("\n2. Testing user login...")
            
            login_data = {
                "email": registration_data["email"],
                "password": registration_data["password"]
            }
            
            login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            print(f"Login Status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                print(f"Login Response: {json.dumps(token_data, indent=2)}")
                
                access_token = token_data["access_token"]
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # Test 3: Get user profile
                print("\n3. Testing user profile...")
                
                profile_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
                print(f"Profile Status: {profile_response.status_code}")
                
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    print(f"Profile Response: {json.dumps(profile_data, indent=2)}")
                
                # Test 4: Get leaderboard around me
                print("\n4. Testing leaderboard around-me...")
                
                around_me_response = requests.get(f"{BASE_URL}/leaderboard/around-me?range=5", headers=headers)
                print(f"Around Me Status: {around_me_response.status_code}")
                
                if around_me_response.status_code == 200:
                    around_me_data = around_me_response.json()
                    print(f"Around Me Response: {json.dumps(around_me_data, indent=2)}")
                else:
                    print(f"Around Me Error: {around_me_response.text}")
                
                # Test 5: Get public leaderboard
                print("\n5. Testing public leaderboard...")
                
                leaderboard_response = requests.get(f"{BASE_URL}/leaderboard?page=1&limit=10")
                print(f"Leaderboard Status: {leaderboard_response.status_code}")
                
                if leaderboard_response.status_code == 200:
                    leaderboard_data = leaderboard_response.json()
                    print(f"Leaderboard Response: {json.dumps(leaderboard_data, indent=2)}")
                
            else:
                print(f"Login Error: {login_response.text}")
        else:
            print(f"Registration Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_registration_and_stats()
