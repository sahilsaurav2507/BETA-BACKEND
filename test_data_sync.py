#!/usr/bin/env python3
"""
Data Synchronization Test Script
================================

This script tests the complete data flow from share action to UI display:
1. User shares on platform
2. Backend records share and updates points
3. Cache is invalidated
4. Admin dashboard shows updated stats
5. Leaderboard reflects new rankings
6. Share analytics display correct data

Usage:
    python test_data_sync.py
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_complete_data_sync():
    """Test complete data synchronization flow."""
    print("🔄 Testing Complete Data Synchronization Flow")
    print("=" * 50)
    
    # Step 1: Create a test user
    print("\n1️⃣ Creating test user...")
    test_user = {
        "name": f"Sync Test User {int(time.time())}",
        "email": f"synctest{int(time.time())}@example.com",
        "password": "testpassword123"
    }
    
    signup_response = requests.post(f"{BASE_URL}/auth/signup", json=test_user)
    if signup_response.status_code != 201:
        print(f"❌ Signup failed: {signup_response.text}")
        return False
    
    user_data = signup_response.json()
    print(f"✅ User created: {user_data['name']} (ID: {user_data['user_id']})")
    
    # Step 2: Login to get token
    print("\n2️⃣ Logging in...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": test_user["email"],
        "password": test_user["password"]
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Step 3: Get initial admin dashboard stats
    print("\n3️⃣ Getting initial admin dashboard stats...")
    admin_login = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@lawvriksh.com",
        "password": "admin123"
    })
    
    if admin_login.status_code != 200:
        print(f"❌ Admin login failed: {admin_login.text}")
        return False
    
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    initial_dashboard = requests.get(f"{BASE_URL}/admin/dashboard", headers=admin_headers)
    if initial_dashboard.status_code == 200:
        initial_stats = initial_dashboard.json()
        print(f"✅ Initial stats - Total shares today: {initial_stats['overview']['total_shares_today']}")
        print(f"   Points distributed today: {initial_stats['overview']['points_distributed_today']}")
    else:
        print(f"❌ Failed to get initial dashboard: {initial_dashboard.text}")
        return False
    
    # Step 4: Get initial leaderboard
    print("\n4️⃣ Getting initial leaderboard...")
    initial_leaderboard = requests.get(f"{BASE_URL}/leaderboard?page=1&limit=10")
    if initial_leaderboard.status_code == 200:
        leaderboard_data = initial_leaderboard.json()
        print(f"✅ Initial leaderboard has {len(leaderboard_data['leaderboard'])} users")
        
        # Find our user in leaderboard
        our_user = None
        for user in leaderboard_data['leaderboard']:
            if user['user_id'] == user_data['user_id']:
                our_user = user
                break
        
        if our_user:
            print(f"   Our user rank: {our_user['rank']}, points: {our_user['points']}, shares: {our_user['shares_count']}")
        else:
            print("   Our user not in top 10 yet")
    else:
        print(f"❌ Failed to get leaderboard: {initial_leaderboard.text}")
    
    # Step 5: Share on Facebook (3 points)
    print("\n5️⃣ Sharing on Facebook...")
    share_response = requests.post(f"{BASE_URL}/shares/facebook", headers=headers)
    
    if share_response.status_code != 201:
        print(f"❌ Share failed: {share_response.text}")
        return False
    
    share_data = share_response.json()
    print(f"✅ Share successful!")
    print(f"   Points earned: {share_data['points_earned']}")
    print(f"   Total points: {share_data['total_points']}")
    print(f"   New rank: {share_data.get('new_rank', 'N/A')}")
    
    # Step 6: Wait a moment for cache invalidation
    print("\n6️⃣ Waiting for cache invalidation...")
    time.sleep(2)
    
    # Step 7: Check updated admin dashboard
    print("\n7️⃣ Checking updated admin dashboard...")
    updated_dashboard = requests.get(f"{BASE_URL}/admin/dashboard", headers=admin_headers)
    if updated_dashboard.status_code == 200:
        updated_stats = updated_dashboard.json()
        shares_increase = updated_stats['overview']['total_shares_today'] - initial_stats['overview']['total_shares_today']
        points_increase = updated_stats['overview']['points_distributed_today'] - initial_stats['overview']['points_distributed_today']
        
        print(f"✅ Updated stats - Total shares today: {updated_stats['overview']['total_shares_today']} (+{shares_increase})")
        print(f"   Points distributed today: {updated_stats['overview']['points_distributed_today']} (+{points_increase})")
        
        # Check platform breakdown
        facebook_stats = updated_stats['platform_breakdown'].get('facebook', {})
        print(f"   Facebook shares: {facebook_stats.get('shares', 0)}")
        
        if shares_increase > 0 and points_increase > 0:
            print("✅ Admin dashboard updated correctly!")
        else:
            print("❌ Admin dashboard not updated properly")
    else:
        print(f"❌ Failed to get updated dashboard: {updated_dashboard.text}")
    
    # Step 8: Check updated leaderboard
    print("\n8️⃣ Checking updated leaderboard...")
    updated_leaderboard = requests.get(f"{BASE_URL}/leaderboard?page=1&limit=10&_t={int(time.time())}")
    if updated_leaderboard.status_code == 200:
        updated_leaderboard_data = updated_leaderboard.json()
        
        # Find our user in updated leaderboard
        updated_user = None
        for user in updated_leaderboard_data['leaderboard']:
            if user['user_id'] == user_data['user_id']:
                updated_user = user
                break
        
        if updated_user:
            print(f"✅ Our user in leaderboard:")
            print(f"   Rank: {updated_user['rank']}")
            print(f"   Points: {updated_user['points']}")
            print(f"   Shares: {updated_user['shares_count']}")
            
            if updated_user['points'] == share_data['total_points']:
                print("✅ Leaderboard points match share response!")
            else:
                print(f"❌ Points mismatch: leaderboard={updated_user['points']}, share={share_data['total_points']}")
        else:
            print("❌ Our user not found in updated leaderboard")
    else:
        print(f"❌ Failed to get updated leaderboard: {updated_leaderboard.text}")
    
    # Step 9: Check share analytics
    print("\n9️⃣ Checking share analytics...")
    analytics_response = requests.get(f"{BASE_URL}/shares/analytics/enhanced", headers=headers)
    if analytics_response.status_code == 200:
        analytics_data = analytics_response.json()
        print(f"✅ Share analytics loaded:")
        print(f"   Total shares: {analytics_data['summary']['total_shares']}")
        print(f"   Total points: {analytics_data['summary']['total_points']}")
        print(f"   Active platforms: {analytics_data['summary']['active_platforms']}")
        
        facebook_breakdown = analytics_data['platform_breakdown'].get('facebook', {})
        print(f"   Facebook shares: {facebook_breakdown.get('shares', 0)}")
        print(f"   Facebook points: {facebook_breakdown.get('points', 0)}")
        
        if analytics_data['summary']['total_shares'] > 0:
            print("✅ Share analytics working correctly!")
        else:
            print("❌ Share analytics not showing data")
    else:
        print(f"❌ Failed to get share analytics: {analytics_response.text}")
    
    print("\n🎉 Data synchronization test completed!")
    return True

if __name__ == "__main__":
    try:
        test_complete_data_sync()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
