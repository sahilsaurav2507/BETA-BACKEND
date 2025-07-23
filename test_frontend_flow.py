#!/usr/bin/env python3
"""
Test script to simulate the exact frontend registration and authentication flow
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_frontend_registration_flow():
    """Test the exact flow that happens in the frontend"""
    
    print("=== FRONTEND FLOW SIMULATION ===")
    print()
    
    # Generate unique test user
    timestamp = int(time.time())
    test_user = {
        "name": "Frontend Test User",
        "email": f"frontend_test_{timestamp}@example.com",
        "password": f"temp-password-{timestamp}"
    }
    
    print(f"Test User: {test_user['name']} ({test_user['email']})")
    print()
    
    try:
        # Step 1: User Registration (like WaitlistPopup.tsx does)
        print("1. 🔄 User Registration...")
        
        signup_response = requests.post(f"{BASE_URL}/auth/signup", json=test_user)
        print(f"   Status: {signup_response.status_code}")
        
        if signup_response.status_code == 201:
            user_data = signup_response.json()
            print(f"   ✅ Registration successful!")
            print(f"   User ID: {user_data.get('user_id')}")
            print(f"   Name: {user_data.get('name')}")
            print(f"   Email: {user_data.get('email')}")
            print(f"   Total Points: {user_data.get('total_points', 0)}")
            print(f"   Current Rank: {user_data.get('current_rank')}")
            print(f"   Default Rank: {user_data.get('default_rank')}")
            
            # Step 2: Auto-login (like WaitlistPopup.tsx does)
            print("\n2. 🔄 Auto-login after registration...")
            
            login_data = {
                "email": test_user["email"],
                "password": test_user["password"]
            }
            
            login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            print(f"   Status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                print(f"   ✅ Login successful!")
                print(f"   Token Type: {token_data.get('token_type')}")
                print(f"   Expires In: {token_data.get('expires_in')} seconds")
                
                access_token = token_data["access_token"]
                headers = {"Authorization": f"Bearer {access_token}"}
                print(f"   Token Preview: {access_token[:20]}...")
                
                # Step 3: Get user profile (like AuthContext does)
                print("\n3. 🔄 Get user profile...")
                
                profile_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
                print(f"   Status: {profile_response.status_code}")
                
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    print(f"   ✅ Profile retrieved!")
                    print(f"   User ID: {profile_data.get('user_id')}")
                    print(f"   Name: {profile_data.get('name')}")
                    print(f"   Total Points: {profile_data.get('total_points', 0)}")
                    print(f"   Current Rank: {profile_data.get('current_rank')}")
                    
                    # Step 4: Get user stats (like ThankYou component does)
                    print("\n4. 🔄 Get user stats (around-me)...")
                    
                    stats_response = requests.get(f"{BASE_URL}/leaderboard/around-me?range=0", headers=headers)
                    print(f"   Status: {stats_response.status_code}")
                    
                    if stats_response.status_code == 200:
                        stats_data = stats_response.json()
                        print(f"   ✅ User stats retrieved!")
                        
                        your_stats = stats_data.get('your_stats', {})
                        print(f"   Your Stats:")
                        print(f"     - Rank: {your_stats.get('rank')}")
                        print(f"     - Points: {your_stats.get('points')}")
                        print(f"     - Points to Next Rank: {your_stats.get('points_to_next_rank')}")
                        print(f"     - Percentile: {your_stats.get('percentile')}")
                        
                        surrounding_users = stats_data.get('surrounding_users', [])
                        print(f"   Surrounding Users: {len(surrounding_users)} users")
                        
                        # Find current user in surrounding users
                        current_user_in_list = None
                        for user in surrounding_users:
                            if user.get('is_current_user'):
                                current_user_in_list = user
                                break
                        
                        if current_user_in_list:
                            print(f"   Current User in List:")
                            print(f"     - Rank: {current_user_in_list.get('rank')}")
                            print(f"     - Name: {current_user_in_list.get('name')}")
                            print(f"     - Points: {current_user_in_list.get('points')}")
                        
                        # Step 5: Get public leaderboard (like ThankYou component does)
                        print("\n5. 🔄 Get public leaderboard...")
                        
                        leaderboard_response = requests.get(f"{BASE_URL}/leaderboard?page=1&limit=10")
                        print(f"   Status: {leaderboard_response.status_code}")
                        
                        if leaderboard_response.status_code == 200:
                            leaderboard_data = leaderboard_response.json()
                            print(f"   ✅ Leaderboard retrieved!")
                            
                            leaderboard = leaderboard_data.get('leaderboard', [])
                            metadata = leaderboard_data.get('metadata', {})
                            
                            print(f"   Total Users: {metadata.get('total_users')}")
                            print(f"   Top 3 Users:")
                            for i, user in enumerate(leaderboard[:3]):
                                print(f"     {i+1}. {user.get('name')} - {user.get('points')} points")
                        
                        print("\n🎉 FRONTEND FLOW SIMULATION COMPLETE!")
                        print("✅ All steps completed successfully")
                        return True
                        
                    else:
                        print(f"   ❌ Failed to get user stats: {stats_response.text}")
                else:
                    print(f"   ❌ Failed to get profile: {profile_response.text}")
            else:
                print(f"   ❌ Login failed: {login_response.text}")
        else:
            print(f"   ❌ Registration failed: {signup_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return False

if __name__ == "__main__":
    test_frontend_registration_flow()
