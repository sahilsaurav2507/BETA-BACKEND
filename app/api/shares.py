from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.schemas.share import ShareCreate, ShareResponse, ShareHistoryResponse, ShareHistoryItem, ShareAnalyticsResponse
from app.services.share_service import log_share_event
from app.services.optimized_query_service import optimized_query_service
from app.utils.pagination import get_pagination_params, PaginationParams
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
    pagination: PaginationParams = Depends(get_pagination_params),
    platform: PlatformEnum = Query(None, description="Filter by platform")
):
    """
    Get share history for the current user with optimized pagination.

    Uses server-side pagination with LIMIT/OFFSET for efficient large dataset handling.
    Optionally filtered by platform with eager loading to prevent N+1 queries.
    """
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Use optimized share history pagination
    from app.utils.pagination import share_history_pagination

    result = share_history_pagination.paginate_user_shares(
        db,
        user_id=payload["user_id"],
        page=pagination.page,
        limit=pagination.limit,
        platform=platform.value if platform else None
    )

    # Convert to response format
    shares = [
        ShareHistoryItem(
            share_id=item.id,
            platform=item.platform,
            points_earned=item.points_earned,
            timestamp=item.created_at
        ) for item in result["items"]
    ]

    # Calculate totals for additional metadata
    total_points = sum(share.points_earned for share in shares)

    return ShareHistoryResponse(
        shares=shares,
        pagination=result["pagination"].dict(),
        total_points=total_points,
        total_shares=result["pagination"].total
    )
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

        # Use optimized query service for comprehensive analytics

        # Use optimized query service for analytics
        analytics = optimized_query_service.get_share_analytics_optimized(
            db, payload["user_id"]
        )

        # Calculate additional performance metrics
        total_points = sum(
            platform_data["points"]
            for platform_data in analytics.points_breakdown.values()
        )

        performance_metrics = {
            "avg_points_per_share": (
                total_points / analytics.total_shares
                if analytics.total_shares > 0 else 0
            ),
            "most_valuable_platform": max(
                analytics.points_breakdown.items(),
                key=lambda x: x[1]["points"],
                default=("none", {"points": 0})
            )[0] if analytics.points_breakdown else "none",
            "platform_diversity": len([
                platform for platform, data in analytics.points_breakdown.items()
                if data["shares"] > 0
            ])
        }

        # Enhanced platform stats
        platform_stats = {}
        for platform, data in analytics.points_breakdown.items():
            if data["shares"] > 0:
                platform_stats[platform] = {
                    **data,
                    "avg_points": data["points"] / data["shares"] if data["shares"] > 0 else 0,
                    "percentage_of_total": (
                        data["shares"] / analytics.total_shares * 100
                        if analytics.total_shares > 0 else 0
                    )
                }

        return ShareAnalyticsResponse(
            total_shares=analytics.total_shares,
            total_points=total_points,
            points_breakdown=analytics.points_breakdown,
            recent_activity=analytics.recent_activity,
            platform_stats=platform_stats,
            performance_metrics=performance_metrics
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