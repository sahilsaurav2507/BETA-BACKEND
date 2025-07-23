from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.schemas.share import ShareCreate, ShareResponse, ShareHistoryResponse, ShareHistoryItem, ShareAnalyticsResponse
from app.services.share_service import log_share_event
from app.core.security import verify_access_token
from fastapi.security import OAuth2PasswordBearer
from app.models.share import ShareEvent, PlatformEnum
from typing import List
from datetime import datetime
from app.utils.monitoring import inc_share_event

router = APIRouter(prefix="/shares", tags=["shares"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/{platform}", response_model=ShareResponse, status_code=201)
def share(
    platform: PlatformEnum = Path(..., description="Platform to share on (facebook, twitter, linkedin, instagram, whatsapp)"),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Record a share event on the specified platform.

    Points are awarded only for the first share per platform per user.
    Subsequent shares on the same platform will not earn additional points.

    Args:
        platform: Social media platform (facebook, twitter, linkedin, instagram, whatsapp)
        token: JWT access token
        db: Database session

    Returns:
        ShareResponse: Share event details and points earned

    Raises:
        HTTPException: If token is invalid or share logging fails
    """
    try:
        # Verify access token
        payload = verify_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Log share event
        share, user, points = log_share_event(db, payload["user_id"], platform)

        # Update metrics
        inc_share_event()

        # Handle case where no points were awarded (duplicate share)
        if points == 0:
            return ShareResponse(
                share_id=None,
                user_id=user.id,
                platform=platform.value,
                points_earned=0,
                total_points=user.total_points,
                new_rank=None,
                timestamp=datetime.utcnow(),
                message="You have already shared on this platform. No additional points awarded."
            )

        # Get updated rank information
        from app.services.ranking_service import get_user_rank_info
        rank_info = get_user_rank_info(db, user.id)

        # Return successful share response with rank information
        return ShareResponse(
            share_id=share.id,
            user_id=user.id,
            platform=platform.value,
            points_earned=points,
            total_points=user.total_points,
            new_rank=user.current_rank,
            timestamp=share.created_at,
            message=f"Share recorded successfully! You earned {points} points. Current rank: {user.current_rank}"
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors
        import logging
        logging.getLogger(__name__).error(f"Share logging failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record share event"
        )

@router.get("/history", response_model=ShareHistoryResponse)
def share_history(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 20,
    platform: PlatformEnum = Query(None, description="Filter by platform")
):
    """Get share history for the current user, optionally filtered by platform."""
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    q = db.query(ShareEvent).filter(ShareEvent.user_id == payload["user_id"])
    if platform:
        q = q.filter(ShareEvent.platform == platform)
    total = q.count()
    shares = q.order_by(ShareEvent.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    items = [ShareHistoryItem(share_id=s.id, platform=s.platform.value, points_earned=s.points_earned, timestamp=s.created_at) for s in shares]
    return ShareHistoryResponse(
        shares=items,
        pagination={"page": page, "limit": limit, "total": total, "pages": (total+limit-1)//limit}
    )

@router.get("/analytics", response_model=ShareAnalyticsResponse)
def share_analytics(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get analytics for the current user's shares across all platforms.

    Args:
        token: JWT access token
        db: Database session

    Returns:
        ShareAnalyticsResponse: User's sharing analytics and statistics

    Raises:
        HTTPException: If token is invalid or analytics calculation fails
    """
    try:
        # Verify access token
        payload = verify_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Get user's share events
        q = db.query(ShareEvent).filter(ShareEvent.user_id == payload["user_id"])
        total_shares = q.count()

        # Calculate points breakdown by platform
        points_breakdown = {}
        for platform in PlatformEnum:
            p_q = q.filter(ShareEvent.platform == platform.value)  # Use platform.value for comparison
            shares = p_q.all()
            points_breakdown[platform.value] = {
                "shares": len(shares),
                "points": sum(s.points_earned for s in shares)
            }

        # Get recent activity
        recent = q.order_by(ShareEvent.created_at.desc()).limit(5).all()
        recent_activity = []
        for s in recent:
            # Handle both enum and string platform values
            platform_value = s.platform.value if hasattr(s.platform, 'value') else str(s.platform)
            recent_activity.append({
                "platform": platform_value,
                "points": str(s.points_earned),  # Convert to string as expected by schema
                "timestamp": s.created_at.isoformat()
            })

        return ShareAnalyticsResponse(
            total_shares=total_shares,
            points_breakdown=points_breakdown,
            recent_activity=recent_activity
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors
        import logging
        logging.getLogger(__name__).error(f"Share analytics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate share analytics"
        )

@router.get("/analytics/enhanced")
def share_analytics_enhanced(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get enhanced analytics for the current user's shares with detailed breakdown.
    This endpoint matches the frontend ShareAnalyticsEnhanced interface.
    """
    try:
        from sqlalchemy import func, desc
        from datetime import datetime, timedelta

        # Verify access token
        payload = verify_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        user_id = payload["user_id"]

        # Get all user's share events
        all_shares = db.query(ShareEvent).filter(ShareEvent.user_id == user_id).all()
        total_shares = len(all_shares)
        total_points = sum(s.points_earned for s in all_shares)

        # Platform breakdown with enhanced data
        platform_breakdown = {}
        active_platforms = 0

        for platform in PlatformEnum:
            platform_shares = [s for s in all_shares if s.platform == platform]
            shares_count = len(platform_shares)
            points_sum = sum(s.points_earned for s in platform_shares)

            if shares_count > 0:
                active_platforms += 1
                first_share = min(platform_shares, key=lambda x: x.created_at)
                last_share = max(platform_shares, key=lambda x: x.created_at)

                platform_breakdown[platform.value] = {
                    "shares": shares_count,
                    "points": points_sum,
                    "percentage": round((shares_count / total_shares * 100), 1) if total_shares > 0 else 0,
                    "first_share_date": first_share.created_at.isoformat(),
                    "last_share_date": last_share.created_at.isoformat()
                }
            else:
                platform_breakdown[platform.value] = {
                    "shares": 0,
                    "points": 0,
                    "percentage": 0
                }

        # Timeline data (last 30 days)
        timeline = []
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            day_shares = [s for s in all_shares if day_start <= s.created_at < day_end]
            day_shares_count = len(day_shares)
            day_points = sum(s.points_earned for s in day_shares)

            timeline.append({
                "date": day_start.isoformat(),
                "shares": day_shares_count,
                "points": day_points
            })

        # Reverse to get chronological order
        timeline.reverse()

        # Summary
        average_points_per_share = round(total_points / total_shares, 2) if total_shares > 0 else 0

        summary = {
            "total_shares": total_shares,
            "total_points": total_points,
            "active_platforms": active_platforms,
            "average_points_per_share": average_points_per_share
        }

        return {
            "platform_breakdown": platform_breakdown,
            "timeline": timeline,
            "summary": summary
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Enhanced share analytics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate enhanced share analytics"
        )