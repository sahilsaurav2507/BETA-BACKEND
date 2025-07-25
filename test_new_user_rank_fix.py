#!/usr/bin/env python3
"""
Test script to verify that new users with 0 points show their default rank instead of N/A.
This tests the fix for the ranking system where newly registered users should show 
rank = (1 + total users) instead of "N/A".
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.services.raw_sql_service import RawSQLService
from app.services.ranking_service import assign_default_rank
from app.services.user_service import create_user
from app.schemas.user import UserCreate
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_new_user_rank_logic():
    """Test that new users with 0 points get their default rank, not N/A."""
    
    try:
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("🔍 Testing new user rank logic...")
        
        # Get current user count
        total_users_before = db.query(User).filter(User.is_admin == False).count()
        print(f"📊 Total non-admin users before test: {total_users_before}")
        
        # Create a test user
        test_user_data = UserCreate(
            name="Test User Rank Fix",
            email=f"test_rank_fix_{total_users_before + 1}@example.com",
            password="testpassword123"
        )
        
        print(f"👤 Creating test user: {test_user_data.email}")
        new_user = create_user(db, test_user_data)
        
        print(f"✅ User created with ID: {new_user.id}")
        print(f"📈 User default_rank: {new_user.default_rank}")
        print(f"📈 User current_rank: {new_user.current_rank}")
        print(f"💰 User total_points: {new_user.total_points}")
        
        # Test the raw SQL service functions
        print("\n🔍 Testing raw SQL service functions...")
        
        # Test get_user_rank_raw
        rank_from_raw = RawSQLService.get_user_rank_raw(db, new_user.id)
        print(f"📊 Rank from get_user_rank_raw: {rank_from_raw}")
        
        # Test get_user_stats_raw
        stats_from_raw = RawSQLService.get_user_stats_raw(db, new_user.id)
        print(f"📊 Stats from get_user_stats_raw: {stats_from_raw}")
        
        # Test get_around_me_raw
        around_me_data = RawSQLService.get_around_me_raw(db, new_user.id, 2)
        print(f"📊 Around me data: {around_me_data}")
        
        # Verify the logic
        expected_rank = total_users_before + 1
        print(f"\n✅ Expected rank for new user: {expected_rank}")
        
        # Check if all functions return the expected rank
        success = True
        
        if new_user.default_rank != expected_rank:
            print(f"❌ FAIL: default_rank is {new_user.default_rank}, expected {expected_rank}")
            success = False
        else:
            print(f"✅ PASS: default_rank is correct ({new_user.default_rank})")
            
        if new_user.current_rank != expected_rank:
            print(f"❌ FAIL: current_rank is {new_user.current_rank}, expected {expected_rank}")
            success = False
        else:
            print(f"✅ PASS: current_rank is correct ({new_user.current_rank})")
            
        if rank_from_raw != expected_rank:
            print(f"❌ FAIL: get_user_rank_raw returned {rank_from_raw}, expected {expected_rank}")
            success = False
        else:
            print(f"✅ PASS: get_user_rank_raw is correct ({rank_from_raw})")
            
        if stats_from_raw and stats_from_raw.get('rank') != expected_rank:
            print(f"❌ FAIL: get_user_stats_raw returned rank {stats_from_raw.get('rank')}, expected {expected_rank}")
            success = False
        elif stats_from_raw:
            print(f"✅ PASS: get_user_stats_raw is correct ({stats_from_raw.get('rank')})")
        else:
            print(f"❌ FAIL: get_user_stats_raw returned None")
            success = False
            
        # Check around_me data
        user_found_in_around_me = False
        for user_data in around_me_data:
            if user_data.get('is_current_user'):
                if user_data.get('rank') != expected_rank:
                    print(f"❌ FAIL: get_around_me_raw returned rank {user_data.get('rank')}, expected {expected_rank}")
                    success = False
                else:
                    print(f"✅ PASS: get_around_me_raw is correct ({user_data.get('rank')})")
                user_found_in_around_me = True
                break
                
        if not user_found_in_around_me:
            print(f"❌ FAIL: User not found in around_me data")
            success = False
        
        # Clean up - delete the test user
        print(f"\n🧹 Cleaning up test user...")
        db.delete(new_user)
        db.commit()
        
        if success:
            print(f"\n🎉 ALL TESTS PASSED! New user rank logic is working correctly.")
            print(f"📝 New users with 0 points will show rank {expected_rank} instead of 'N/A'")
        else:
            print(f"\n❌ SOME TESTS FAILED! Please check the implementation.")
            
        return success
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    success = test_new_user_rank_logic()
    sys.exit(0 if success else 1)
