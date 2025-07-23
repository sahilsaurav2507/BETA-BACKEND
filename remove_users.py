#!/usr/bin/env python3
"""
User Removal Script
===================

This script safely removes specified users from the database.
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.dependencies import get_db
from app.models.user import User
from app.models.share import ShareEvent

def remove_user(db, email):
    """Remove a user and their associated data."""
    try:
        # Find the user
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User {email} not found")
            return False
        
        print(f"📋 Found user: {user.name} (ID: {user.id})")
        print(f"   Email: {user.email}")
        print(f"   Created: {user.created_at}")
        print(f"   Points: {user.total_points}")
        print(f"   Shares: {user.shares_count}")
        
        # Check for associated share events
        share_events = db.query(ShareEvent).filter(ShareEvent.user_id == user.id).all()
        if share_events:
            print(f"   📊 Found {len(share_events)} share events to delete")
            
            # Delete share events first (foreign key constraint)
            for share in share_events:
                db.delete(share)
            print(f"   ✅ Deleted {len(share_events)} share events")
        
        # Delete the user
        db.delete(user)
        db.commit()
        
        print(f"✅ Successfully removed user: {email}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error removing user {email}: {e}")
        return False

def main():
    """Remove the specified users."""
    print("🗑️  USER REMOVAL SCRIPT")
    print("=" * 50)
    
    # Users to remove
    users_to_remove = [
        "prabhjotjaswal08@gmail.com",
        "prabhjotjaswal09@gmail.com", 
        "prabhjotjaswal11@gmail.com"
    ]
    
    db = next(get_db())
    
    try:
        print(f"📋 Users to remove: {len(users_to_remove)}")
        print()
        
        removed_count = 0
        
        for email in users_to_remove:
            print(f"🔄 Processing: {email}")
            if remove_user(db, email):
                removed_count += 1
            print()
        
        print("=" * 50)
        print(f"📊 SUMMARY:")
        print(f"   Total users processed: {len(users_to_remove)}")
        print(f"   Successfully removed: {removed_count}")
        print(f"   Failed to remove: {len(users_to_remove) - removed_count}")
        
        if removed_count == len(users_to_remove):
            print("🎉 All users removed successfully!")
        elif removed_count > 0:
            print("⚠️  Some users were removed, but some failed.")
        else:
            print("❌ No users were removed.")
            
    except Exception as e:
        print(f"❌ Script error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
