"""
Optimized Query Service for N+1 Query Prevention
===============================================

This service provides optimized database queries that prevent N+1 query problems
by using proper eager loading strategies with SQLAlchemy.

Performance Benefits:
- Eliminates N+1 query patterns
- Uses joinedload for many-to-one relationships
- Uses selectinload for one-to-many relationships
- Implements efficient batch loading
- Provides query result caching
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload, selectinload, contains_eager
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta

from app.models.user import User
from app.models.share import ShareEvent, PlatformEnum
from app.schemas.user import UserResponse
from app.schemas.share import ShareHistoryItem, ShareAnalyticsResponse

logger = logging.getLogger(__name__)

class OptimizedQueryService:
    """Service for optimized database queries that prevent N+1 problems."""
    
    @staticmethod
    def get_users_with_share_stats(
        db: Session, 
        limit: int = 50, 
        offset: int = 0,
        include_admin: bool = False
    ) -> List[User]:
        """
        Get users with their share statistics using optimized eager loading.
        Prevents N+1 queries by loading all related data in minimal queries.
        """
        query = db.query(User).options(
            selectinload(User.share_events)  # Eager load share events
        )
        
        if not include_admin:
            query = query.filter(User.is_admin == False)
            
        return query.order_by(
            User.total_points.desc(), 
            User.created_at.asc()
        ).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_user_with_complete_profile(db: Session, user_id: int) -> Optional[User]:
        """
        Get a single user with all related data using optimized eager loading.
        """
        return db.query(User).options(
            selectinload(User.share_events),
            selectinload(User.feedback_responses)
        ).filter(User.id == user_id).first()
    
    @staticmethod
    def get_share_history_optimized(
        db: Session,
        user_id: int,
        page: int = 1,
        limit: int = 20,
        platform: Optional[PlatformEnum] = None
    ) -> Dict[str, Any]:
        """
        Get share history with optimized query and eager loading.
        """
        query = db.query(ShareEvent).options(
            joinedload(ShareEvent.user)  # Eager load user data
        ).filter(ShareEvent.user_id == user_id)
        
        if platform:
            query = query.filter(ShareEvent.platform == platform)
        
        total = query.count()
        offset = (page - 1) * limit
        shares = query.order_by(
            ShareEvent.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "shares": [
                ShareHistoryItem(
                    share_id=share.id,
                    platform=share.platform.value,
                    points_earned=share.points_earned,
                    timestamp=share.created_at
                ) for share in shares
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    
    @staticmethod
    def get_share_analytics_optimized(db: Session, user_id: int) -> ShareAnalyticsResponse:
        """
        Get share analytics using optimized aggregation queries.
        Prevents N+1 by using database-level aggregations.
        """
        # Single query to get all platform statistics
        platform_stats = db.query(
            ShareEvent.platform,
            func.count(ShareEvent.id).label('share_count'),
            func.sum(ShareEvent.points_earned).label('total_points'),
            func.max(ShareEvent.created_at).label('last_share')
        ).filter(
            ShareEvent.user_id == user_id
        ).group_by(ShareEvent.platform).all()
        
        total_shares = sum(stat.share_count for stat in platform_stats)
        
        # Build points breakdown efficiently
        points_breakdown = {}
        recent_activity = []
        
        for platform in PlatformEnum:
            platform_stat = next(
                (stat for stat in platform_stats if stat.platform == platform), 
                None
            )
            
            if platform_stat:
                points_breakdown[platform.value] = {
                    "shares": platform_stat.share_count,
                    "points": platform_stat.total_points
                }
                
                if platform_stat.last_share:
                    recent_activity.append({
                        "platform": platform.value,
                        "last_share": platform_stat.last_share.isoformat(),
                        "points": platform_stat.total_points
                    })
            else:
                points_breakdown[platform.value] = {
                    "shares": 0,
                    "points": 0
                }
        
        # Sort recent activity by last share date
        recent_activity.sort(key=lambda x: x["last_share"], reverse=True)
        
        return ShareAnalyticsResponse(
            total_shares=total_shares,
            points_breakdown=points_breakdown,
            recent_activity=recent_activity[:5]  # Last 5 activities
        )
    
    @staticmethod
    def get_leaderboard_with_user_data(
        db: Session,
        page: int = 1,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get leaderboard data with optimized query using window functions.
        Prevents N+1 by calculating ranks in the database.
        """
        from sqlalchemy import text
        
        offset = (page - 1) * limit
        
        # Use raw SQL with window functions for optimal performance
        query = text("""
            SELECT 
                u.id as user_id,
                u.name,
                u.email,
                u.total_points,
                u.shares_count,
                u.default_rank,
                u.current_rank,
                ROW_NUMBER() OVER (
                    ORDER BY u.total_points DESC, u.created_at ASC
                ) as calculated_rank,
                CASE 
                    WHEN u.default_rank IS NOT NULL AND u.current_rank IS NOT NULL 
                    THEN u.default_rank - u.current_rank
                    WHEN u.default_rank IS NOT NULL 
                    THEN u.default_rank - ROW_NUMBER() OVER (
                        ORDER BY u.total_points DESC, u.created_at ASC
                    )
                    ELSE 0
                END as rank_improvement
            FROM users u
            WHERE u.is_admin = FALSE
            ORDER BY u.total_points DESC, u.created_at ASC
            LIMIT :limit OFFSET :offset
        """)
        
        result = db.execute(query, {"limit": limit, "offset": offset})
        
        return [
            {
                "rank": row.calculated_rank,
                "user_id": row.user_id,
                "name": row.name,
                "points": row.total_points,
                "shares_count": row.shares_count,
                "default_rank": row.default_rank,
                "rank_improvement": row.rank_improvement,
                "badge": OptimizedQueryService._get_badge_for_rank(row.calculated_rank)
            }
            for row in result.fetchall()
        ]
    
    @staticmethod
    def _get_badge_for_rank(rank: int) -> str:
        """Get badge based on rank position."""
        if rank == 1:
            return "🥇 Champion"
        elif rank == 2:
            return "🥈 Runner-up"
        elif rank == 3:
            return "🥉 Third Place"
        elif rank <= 10:
            return "🏆 Top 10"
        elif rank <= 50:
            return "⭐ Top 50"
        else:
            return "🎯 Participant"
    
    @staticmethod
    def get_user_rank_optimized(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user rank using optimized query with window functions.
        """
        from sqlalchemy import text
        
        query = text("""
            WITH ranked_users AS (
                SELECT 
                    u.id,
                    u.name,
                    u.total_points,
                    ROW_NUMBER() OVER (
                        ORDER BY u.total_points DESC, u.created_at ASC
                    ) as user_rank
                FROM users u
                WHERE u.is_admin = FALSE
            )
            SELECT * FROM ranked_users WHERE id = :user_id
        """)
        
        result = db.execute(query, {"user_id": user_id}).fetchone()
        
        if result:
            return {
                "user_id": result.id,
                "name": result.name,
                "total_points": result.total_points,
                "rank": result.user_rank
            }
        
        return None

# Global instance
optimized_query_service = OptimizedQueryService()
