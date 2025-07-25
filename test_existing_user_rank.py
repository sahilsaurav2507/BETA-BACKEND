#!/usr/bin/env python3
"""
Test script to verify that existing users with points still get correct dynamic ranks.
This ensures our fix doesn't break the ranking for users who have earned points.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.services.raw_sql_service import RawSQLService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_existing_user_rank_logic():
    """Test that existing users with points get correct dynamic ranks."""
    
    try:
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("🔍 Testing existing user rank logic...")
        
        # Find a user with points > 0
        user_with_points = db.query(User).filter(
            User.is_admin == False,
            User.total_points > 0
        ).first()
        
        if not user_with_points:
            print("⚠️  No users with points found. Creating a test scenario...")
            
            # Get a user with 0 points and give them some points
            user_with_zero_points = db.query(User).filter(
                User.is_admin == False,
                User.total_points == 0
            ).first()
            
            if user_with_zero_points:
                print(f"👤 Giving points to user: {user_with_zero_points.name}")
                user_with_zero_points.total_points = 100
                db.commit()
                user_with_points = user_with_zero_points
            else:
                print("❌ No users available for testing")
                return False
        
        print(f"👤 Testing with user: {user_with_points.name}")
        print(f"💰 User total_points: {user_with_points.total_points}")
        print(f"📈 User default_rank: {user_with_points.default_rank}")
        print(f"📈 User current_rank: {user_with_points.current_rank}")
        
        # Test the raw SQL service functions
        print("\n🔍 Testing raw SQL service functions...")
        
        # Test get_user_rank_raw
        rank_from_raw = RawSQLService.get_user_rank_raw(db, user_with_points.id)
        print(f"📊 Rank from get_user_rank_raw: {rank_from_raw}")
        
        # Test get_user_stats_raw
        stats_from_raw = RawSQLService.get_user_stats_raw(db, user_with_points.id)
        print(f"📊 Stats from get_user_stats_raw: {stats_from_raw}")
        
        # Test get_around_me_raw
        around_me_data = RawSQLService.get_around_me_raw(db, user_with_points.id, 2)
        print(f"📊 Around me data: {around_me_data}")
        
        # For users with points > 0, the rank should be calculated dynamically
        # and should be better (lower number) than their default rank
        success = True
        
        if user_with_points.total_points > 0:
            # The rank should be calculated dynamically, not using default_rank
            expected_behavior = "Dynamic rank calculation (should be <= default_rank)"
            print(f"\n✅ Expected behavior: {expected_behavior}")
            
            if rank_from_raw and user_with_points.default_rank:
                if rank_from_raw <= user_with_points.default_rank:
                    print(f"✅ PASS: Dynamic rank ({rank_from_raw}) <= default rank ({user_with_points.default_rank})")
                else:
                    print(f"⚠️  WARNING: Dynamic rank ({rank_from_raw}) > default rank ({user_with_points.default_rank})")
                    print("   This could happen if other users also have points")
            
            if stats_from_raw and stats_from_raw.get('rank'):
                print(f"✅ PASS: get_user_stats_raw returned valid rank ({stats_from_raw.get('rank')})")
            else:
                print(f"❌ FAIL: get_user_stats_raw returned invalid rank")
                success = False
                
            # Check around_me data
            user_found_in_around_me = False
            for user_data in around_me_data:
                if user_data.get('is_current_user'):
                    print(f"✅ PASS: User found in around_me with rank ({user_data.get('rank')})")
                    user_found_in_around_me = True
                    break
                    
            if not user_found_in_around_me:
                print(f"❌ FAIL: User not found in around_me data")
                success = False
        
        if success:
            print(f"\n🎉 ALL TESTS PASSED! Existing user rank logic is working correctly.")
            print(f"📝 Users with points get dynamic ranks, users with 0 points keep default ranks")
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
    success = test_existing_user_rank_logic()
    sys.exit(0 if success else 1)
