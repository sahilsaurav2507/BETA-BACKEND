"""
Dynamic Ranking Service
======================

This service implements the dynamic ranking logic:
1. Default Rank: New users get rank based on registration order (5th user = rank 5)
2. Dynamic Ranking: When users share and earn points, rank improves based on total points
3. Real-time Updates: Ranks update immediately after sharing

Logic:
- New user with 0 points gets default rank (registration order)
- When user earns points, they get dynamic rank based on points
- Users with same points are ranked by registration order (earlier = better rank)
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, desc, asc
from app.models.user import User
from app.utils.cache import invalidate_leaderboard_cache
import logging

logger = logging.getLogger(__name__)

def assign_default_rank(db: Session, user_id: int) -> int:
    """
    Assign default rank to a new user based on registration order.
    
    Args:
        db: Database session
        user_id: ID of the user to assign rank to
        
    Returns:
        int: The assigned default rank
    """
    try:
        # Count total non-admin users (including the new user)
        total_users = db.query(User).filter(User.is_admin == False).count()
        
        # The new user gets rank equal to total users count
        default_rank = total_users
        
        # Update user's default rank
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.default_rank = default_rank
            user.current_rank = default_rank  # Initially same as default
            db.commit()
            
            logger.info(f"Assigned default rank {default_rank} to user {user_id}")
            return default_rank
        
        return total_users
        
    except Exception as e:
        logger.error(f"Error assigning default rank to user {user_id}: {e}")
        db.rollback()
        return 1

def calculate_dynamic_rank(db: Session, user_id: int) -> int:
    """
    Calculate dynamic rank based on points and registration order.
    
    Logic:
    - Users are ranked by total_points (descending)
    - Users with same points are ranked by created_at (ascending - earlier is better)
    - Users with 0 points keep their default rank
    
    Args:
        db: Database session
        user_id: ID of the user to calculate rank for
        
    Returns:
        int: The calculated dynamic rank
    """
    try:
        # Get the user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            return 1
        
        # If user has 0 points, return their default rank
        if user.total_points == 0:
            return user.default_rank or 1
        
        # Calculate rank based on points and registration order
        result = db.execute(text("""
            SELECT rank_val FROM (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        ORDER BY
                            total_points DESC,
                            created_at ASC
                    ) as rank_val
                FROM users
                WHERE is_admin = FALSE
            ) as ranked
            WHERE id = :user_id
        """), {"user_id": user_id}).first()
        
        dynamic_rank = result[0] if result else user.default_rank or 1
        
        logger.info(f"Calculated dynamic rank {dynamic_rank} for user {user_id} (points: {user.total_points})")
        return dynamic_rank
        
    except Exception as e:
        logger.error(f"Error calculating dynamic rank for user {user_id}: {e}")
        return 1

def update_user_rank(db: Session, user_id: int) -> int:
    """
    Update user's current rank after point changes.
    
    Args:
        db: Database session
        user_id: ID of the user to update rank for
        
    Returns:
        int: The updated current rank
    """
    try:
        # Calculate new dynamic rank
        new_rank = calculate_dynamic_rank(db, user_id)
        
        # Update user's current rank
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            old_rank = user.current_rank
            user.current_rank = new_rank
            db.commit()
            
            # Invalidate leaderboard cache
            invalidate_leaderboard_cache()
            
            logger.info(f"Updated user {user_id} rank: {old_rank} → {new_rank}")
            return new_rank
        
        return new_rank
        
    except Exception as e:
        logger.error(f"Error updating rank for user {user_id}: {e}")
        db.rollback()
        return 1

def update_all_ranks(db: Session):
    """
    Recalculate and update ranks for all users.
    This should be called after any major changes.
    """
    try:
        logger.info("Starting bulk rank update for all users")
        
        # Get all non-admin users ordered by points (desc) and created_at (asc)
        users = db.query(User).filter(
            User.is_admin == False
        ).order_by(
            desc(User.total_points),
            asc(User.created_at)
        ).all()
        
        # Update ranks
        for rank, user in enumerate(users, 1):
            # Users with 0 points keep their default rank
            if user.total_points == 0:
                user.current_rank = user.default_rank or rank
            else:
                user.current_rank = rank
        
        db.commit()
        invalidate_leaderboard_cache()
        
        logger.info(f"Updated ranks for {len(users)} users")
        
    except Exception as e:
        logger.error(f"Error in bulk rank update: {e}")
        db.rollback()

def get_user_rank_info(db: Session, user_id: int) -> dict:
    """
    Get comprehensive rank information for a user.
    
    Args:
        db: Database session
        user_id: ID of the user
        
    Returns:
        dict: User rank information
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Get total users for percentile calculation
        total_users = db.query(User).filter(User.is_admin == False).count()
        
        # Calculate percentile
        percentile = 0
        if total_users > 0 and user.current_rank:
            percentile = ((total_users - user.current_rank + 1) / total_users) * 100
        
        # Get next rank info (user with better rank)
        next_rank_target = (user.current_rank - 1) if user.current_rank and user.current_rank > 1 else None
        next_rank_user = None
        if next_rank_target:
            next_rank_user = db.query(User).filter(
                User.is_admin == False,
                User.current_rank == next_rank_target
            ).first()
        
        points_to_next_rank = 0
        if next_rank_user and user.current_rank and user.current_rank > 1:
            points_to_next_rank = max(0, next_rank_user.total_points - user.total_points + 1)
        
        return {
            "user_id": user.id,
            "name": user.name,
            "total_points": user.total_points,
            "default_rank": user.default_rank,
            "current_rank": user.current_rank,
            "rank_improvement": (user.default_rank - user.current_rank) if user.default_rank and user.current_rank else 0,
            "percentile": round(percentile, 1),
            "points_to_next_rank": points_to_next_rank,
            "total_users": total_users
        }
        
    except Exception as e:
        logger.error(f"Error getting rank info for user {user_id}: {e}")
        return {"error": str(e)}

def get_rank_changes_after_share(db: Session, user_id: int, points_earned: int) -> dict:
    """
    Calculate what rank changes would occur after earning points.
    
    Args:
        db: Database session
        user_id: ID of the user
        points_earned: Points that will be earned
        
    Returns:
        dict: Rank change information
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        old_rank = user.current_rank
        new_total_points = user.total_points + points_earned
        
        # Calculate what the new rank would be
        result = db.execute(text("""
            SELECT COUNT(*) + 1 as new_rank
            FROM users 
            WHERE is_admin = FALSE 
            AND (
                total_points > :new_points 
                OR (total_points = :new_points AND created_at < :user_created_at)
            )
        """), {
            "new_points": new_total_points,
            "user_created_at": user.created_at
        }).first()
        
        new_rank = result[0] if result else 1
        rank_improvement = (old_rank - new_rank) if old_rank else 0
        
        return {
            "old_rank": old_rank,
            "new_rank": new_rank,
            "rank_improvement": rank_improvement,
            "points_earned": points_earned,
            "new_total_points": new_total_points
        }
        
    except Exception as e:
        logger.error(f"Error calculating rank changes for user {user_id}: {e}")
        return {"error": str(e)}
