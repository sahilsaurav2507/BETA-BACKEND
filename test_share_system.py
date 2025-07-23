#!/usr/bin/env python3
"""
Test script to manually add shares and points to users to test the system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.share import ShareEvent, PlatformEnum
from datetime import datetime

def test_share_system():
    """Manually add shares and points to test users"""
    
    print("=== TESTING SHARE SYSTEM ===")
    print()
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get a test user
        user = db.query(User).filter(User.email == "cleantest@example.com").first()
        if not user:
            print("❌ Test user not found")
            return
        
        print(f"📊 Current user stats:")
        print(f"   User: {user.name} ({user.email})")
        print(f"   Points: {user.total_points}")
        print(f"   Shares: {user.shares_count}")
        print()
        
        # Check existing shares
        existing_shares = db.query(ShareEvent).filter(ShareEvent.user_id == user.id).all()
        print(f"📋 Existing shares: {len(existing_shares)}")
        for share in existing_shares:
            print(f"   - {share.platform.value}: {share.points_earned} points")
        print()
        
        # Add a test share if none exist
        if not existing_shares:
            print("➕ Adding test Facebook share...")
            
            # Create share event
            share = ShareEvent(
                user_id=user.id,
                platform=PlatformEnum.facebook,
                points_earned=3,
                created_at=datetime.utcnow()
            )
            
            # Update user stats
            user.total_points += 3
            user.shares_count += 1
            
            # Save to database
            db.add(share)
            db.commit()
            db.refresh(user)
            
            print(f"✅ Share added successfully!")
            print(f"   New points: {user.total_points}")
            print(f"   New shares count: {user.shares_count}")
        else:
            print("ℹ️  User already has shares")
        
        print()
        
        # Update user ranking
        print("🔄 Updating user ranking...")
        from app.services.ranking_service import update_user_rank
        new_rank = update_user_rank(db, user.id)
        db.refresh(user)
        
        print(f"✅ Ranking updated:")
        print(f"   Current rank: {user.current_rank}")
        print(f"   Default rank: {user.default_rank}")
        
        print()
        print("=== TEST COMPLETED ===")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_share_system()
