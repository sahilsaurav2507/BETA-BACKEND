#!/usr/bin/env python3
"""
Test script for the delete all users functionality
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "prabhjotjaswal08@gmail.com"
ADMIN_PASSWORD = "aaAA123/"

def test_delete_all_users():
    """Test the delete all users endpoint"""
    
    print("🧪 Testing Delete All Users Functionality")
    print("=" * 50)
    
    # Step 1: Login as admin
    print("1. Logging in as admin...")
    login_response = requests.post(f"{BASE_URL}/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return False
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Step 2: Check current users
    print("\n2. Checking current users...")
    users_response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    
    if users_response.status_code != 200:
        print(f"❌ Failed to get users: {users_response.status_code}")
        return False
    
    users_data = users_response.json()
    total_users = users_data["pagination"]["total"]
    print(f"✅ Current total users: {total_users}")
    
    if total_users == 0:
        print("ℹ️  No users to delete")
        return True
    
    # Step 3: Test delete all users
    print("\n3. Testing delete all users...")
    delete_response = requests.post(f"{BASE_URL}/admin/delete-all-users", headers=headers)
    
    if delete_response.status_code != 200:
        print(f"❌ Delete failed: {delete_response.status_code}")
        print(delete_response.text)
        return False
    
    delete_data = delete_response.json()
    print("✅ Delete successful!")
    print(f"📄 Message: {delete_data['message']}")
    print(f"📁 Export file: {delete_data['export_file']}")
    
    # Step 4: Verify users are deleted
    print("\n4. Verifying deletion...")
    users_response_after = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    
    if users_response_after.status_code != 200:
        print(f"❌ Failed to get users after deletion: {users_response_after.status_code}")
        return False
    
    users_data_after = users_response_after.json()
    total_users_after = users_data_after["pagination"]["total"]
    print(f"✅ Users remaining after deletion: {total_users_after}")
    
    # Step 5: Save export data to file for inspection
    if "export_data" in delete_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_export_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(delete_data["export_data"], f, indent=2, ensure_ascii=False)
        
        print(f"📁 Export data saved to: {filename}")
        
        # Show summary of exported data
        export_data = delete_data["export_data"]
        print(f"📊 Export summary:")
        print(f"   - Users exported: {export_data['total_users_exported']}")
        print(f"   - Export timestamp: {export_data['export_timestamp']}")
        print(f"   - Exported by: {export_data['exported_by_admin']}")
        if 'note' in export_data:
            print(f"   - Note: {export_data['note']}")
    
    print("\n🎉 Test completed successfully!")
    return True

if __name__ == "__main__":
    try:
        success = test_delete_all_users()
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
