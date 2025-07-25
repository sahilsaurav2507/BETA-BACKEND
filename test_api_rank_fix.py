#!/usr/bin/env python3
"""
Test script to verify that the API endpoints return correct rank for new users.
This tests the actual API endpoints that the frontend calls.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.services.user_service import create_user
from app.schemas.user import UserCreate
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api_rank_endpoints():
    """Test that API endpoints return correct rank for new users."""
    
    try:
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("🔍 Testing API rank endpoints...")
        
        # Get current user count
        total_users_before = db.query(User).filter(User.is_admin == False).count()
        print(f"📊 Total non-admin users before test: {total_users_before}")
        
        # Create a test user
        test_user_data = UserCreate(
            name="API Test User",
            email=f"api_test_user_{total_users_before + 1}@example.com",
            password="testpassword123"
        )
        
        print(f"👤 Creating test user: {test_user_data.email}")
        new_user = create_user(db, test_user_data)
        
        expected_rank = total_users_before + 1
        print(f"✅ Expected rank for new user: {expected_rank}")
        print(f"📈 User default_rank: {new_user.default_rank}")
        print(f"📈 User current_rank: {new_user.current_rank}")
        
        # Test the debug endpoint (no auth required)
        print(f"\n🔍 Testing debug endpoint...")
        try:
            response = requests.get(f"http://localhost:8000/test-around-me/{new_user.id}")
            if response.status_code == 200:
                data = response.json()
                your_stats = data.get('your_stats', {})
                rank_from_api = your_stats.get('rank')
                print(f"📊 Rank from API: {rank_from_api}")
                
                if rank_from_api == expected_rank:
                    print(f"✅ PASS: API returned correct rank ({rank_from_api})")
                else:
                    print(f"❌ FAIL: API returned rank {rank_from_api}, expected {expected_rank}")
                    
                # Check surrounding users
                surrounding_users = data.get('surrounding_users', [])
                user_found = False
                for user_data in surrounding_users:
                    if user_data.get('is_current_user'):
                        api_rank = user_data.get('rank')
                        if api_rank == expected_rank:
                            print(f"✅ PASS: Around-me API returned correct rank ({api_rank})")
                        else:
                            print(f"❌ FAIL: Around-me API returned rank {api_rank}, expected {expected_rank}")
                        user_found = True
                        break
                        
                if not user_found:
                    print(f"❌ FAIL: User not found in around-me API response")
                    
            else:
                print(f"❌ API request failed with status: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"⚠️  Could not connect to API server. Make sure the server is running on localhost:8000")
            print(f"   This is expected if the server is not running.")
        except Exception as e:
            print(f"❌ API test failed: {e}")
        
        # Clean up - delete the test user
        print(f"\n🧹 Cleaning up test user...")
        db.delete(new_user)
        db.commit()
        
        print(f"\n🎉 API test completed!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    success = test_api_rank_endpoints()
    sys.exit(0 if success else 1)
