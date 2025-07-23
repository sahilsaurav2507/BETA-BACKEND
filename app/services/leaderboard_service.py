import logging
from sqlalchemy.orm import Session
from app.models.user import User
from app.utils.cache import get_leaderboard_cache, set_leaderboard_cache
from app.utils.bst_leaderboard import bst_leaderboard, LeaderboardUser
from app.services.raw_sql_service import raw_sql_service
from typing import List
from datetime import datetime, timedelta

def sync_bst_with_database(db: Session, force_refresh: bool = False):
    """Synchronize BST leaderboard with database for optimal performance."""
    try:
        # Always sync for now to ensure data consistency
        # time_threshold = datetime.utcnow() - timedelta(minutes=5)
        # if not force_refresh and bst_leaderboard.last_updated > time_threshold:
        #     logging.debug("BST leaderboard is up to date, skipping sync")
        #     return

        logging.info("Synchronizing BST leaderboard with database...")

        # Get all non-admin users from database
        users = db.query(User).filter(
            User.is_admin == False
        ).order_by(
            User.total_points.desc(),
            User.created_at.asc()
        ).all()

        if not users:
            logging.warning("No users found in database for BST sync")
            return

        # Clear and rebuild BST
        bst_leaderboard.__init__()  # Reset BST

        # Insert all users into BST
        for user in users:
            bst_user = LeaderboardUser(
                user_id=user.id,
                name=user.name,
                points=user.total_points,
                shares_count=user.shares_count,
                created_at=user.created_at,
                default_rank=user.default_rank,
                current_rank=user.current_rank
            )
            bst_leaderboard.insert_user(bst_user)

        logging.info(f"BST leaderboard synchronized with {len(users)} users")

    except Exception as e:
        logging.error(f"Error synchronizing BST leaderboard: {e}")
        # Don't raise the exception to allow fallback to work

def get_leaderboard(db: Session, page: int = 1, limit: int = 50):
    """Get leaderboard using raw SQL for reliable performance."""
    try:
        # First try cache
        cached = get_leaderboard_cache(page, limit)
        if cached:
            logging.info(f"Leaderboard cache hit for page {page}, limit {limit}")
            return cached
        logging.info(f"Leaderboard cache miss for page {page}, limit {limit}")
    except Exception as e:
        logging.error(f"Leaderboard cache error: {e}")
        cached = None

    # Use raw SQL directly for reliable results (BST optimization temporarily disabled)
    logging.info(f"Using raw SQL for leaderboard page {page}")
    leaderboard = raw_sql_service.get_leaderboard_raw(db, page, limit)

    try:
        set_leaderboard_cache(leaderboard, page, limit)
    except Exception as e:
        logging.error(f"Leaderboard cache set error: {e}")

    return leaderboard

def get_user_rank(db: Session, user_id: int):
    """Get the current rank of a user using BST optimization."""
    try:
        # Try BST first for faster lookup
        sync_bst_with_database(db)
        bst_rank = bst_leaderboard.get_user_rank(user_id)
        if bst_rank:
            logging.debug(f"BST rank lookup for user {user_id}: {bst_rank}")
            return bst_rank

        # Fallback to raw SQL for 3-5x performance improvement
        return raw_sql_service.get_user_rank_raw(db, user_id)
    except Exception as e:
        logging.error(f"Error getting user rank for user_id {user_id}: {e}")
        return None

def update_user_in_bst(db: Session, user_id: int):
    """Update a specific user in the BST after point changes."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user and not user.is_admin:
            bst_user = LeaderboardUser(
                user_id=user.id,
                name=user.name,
                points=user.total_points,
                shares_count=user.shares_count,
                created_at=user.created_at,
                default_rank=user.default_rank,
                current_rank=user.current_rank
            )
            bst_leaderboard.insert_user(bst_user)
            logging.debug(f"Updated user {user_id} in BST leaderboard")
    except Exception as e:
        logging.error(f"Error updating user {user_id} in BST: {e}")