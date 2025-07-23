#!/usr/bin/env python3
"""
Debug script to check user stats and ranking system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.models.user import User
from app.services.ranking_service import get_user_rank_info
from app.services.leaderboard_service import get_user_rank
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_user_stats():
    """Debug user stats and ranking"""
    try:
        # Get database session
        db = next(get_db())
        
        print("=== USER STATS DEBUG ===")
        print()
        
        # Get all non-admin users
        users = db.query(User).filter(User.is_admin == False).order_by(User.created_at.desc()).limit(10).all()
        
        print(f"Found {len(users)} recent non-admin users:")
        print()
        
        for user in users:
            print(f"User ID: {user.id}")
            print(f"Name: {user.name}")
            print(f"Email: {user.email}")
            print(f"Total Points: {user.total_points}")
            print(f"Shares Count: {user.shares_count}")
            print(f"Default Rank: {user.default_rank}")
            print(f"Current Rank: {user.current_rank}")
            print(f"Created At: {user.created_at}")
            
            # Get rank from service
            service_rank = get_user_rank(db, user.id)
            print(f"Service Rank: {service_rank}")
            
            # Get detailed rank info
            rank_info = get_user_rank_info(db, user.id)
            print(f"Rank Info: {rank_info}")
            
            print("-" * 50)
            print()
        
        # Get total user count
        total_users = db.query(User).filter(User.is_admin == False).count()
        print(f"Total non-admin users: {total_users}")
        
        # Get users with missing ranks
        users_no_default_rank = db.query(User).filter(
            User.is_admin == False,
            User.default_rank.is_(None)
        ).count()
        
        users_no_current_rank = db.query(User).filter(
            User.is_admin == False,
            User.current_rank.is_(None)
        ).count()
        
        print(f"Users without default rank: {users_no_default_rank}")
        print(f"Users without current rank: {users_no_current_rank}")
        
    except Exception as e:
        logger.error(f"Error in debug_user_stats: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_user_stats()
