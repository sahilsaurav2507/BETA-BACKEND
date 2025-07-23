import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.schemas.admin import AdminDashboardResponse, AdminUsersResponse, AdminUser
from app.models.user import User
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from app.services.user_service import authenticate_user, create_jwt_for_user, get_user_by_id, promote_user_to_admin, get_bulk_email_recipients
from app.core.security import get_current_admin
from app.schemas.user import UserLogin
from app.tasks.email_tasks import send_bulk_email_task
from pydantic import BaseModel
from app.utils.monitoring import inc_bulk_email_sent, inc_admin_promotion

router = APIRouter(prefix="/admin", tags=["admin"])

class BulkEmailRequest(BaseModel):
    subject: str
    body: str
    min_points: int = 0

class PromoteRequest(BaseModel):
    user_id: int

@router.post("/login")
def admin_login(user_in: UserLogin, db: Session = Depends(get_db)):
    """Admin login. Returns JWT if credentials are valid and user is admin."""
    user = authenticate_user(db, user_in.email, user_in.password)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin credentials required")
    token = create_jwt_for_user(user)
    return {"access_token": token, "token_type": "bearer", "expires_in": 3600}

@router.get("/dashboard", response_model=AdminDashboardResponse)
def dashboard(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    """Get admin dashboard overview with user and platform stats."""
    from app.models.share import ShareEvent
    from sqlalchemy import func

    # Basic user stats
    total_users = db.query(User).count()
    active_users_24h = db.query(User).filter(User.updated_at > datetime.utcnow() - timedelta(hours=24)).count()

    # Share stats for today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total_shares_today = db.query(ShareEvent).filter(ShareEvent.created_at >= today_start).count()
    points_distributed_today = db.query(func.sum(ShareEvent.points_earned)).filter(ShareEvent.created_at >= today_start).scalar() or 0

    # Platform breakdown (all time)
    platform_stats = db.query(
        ShareEvent.platform,
        func.count(ShareEvent.id).label('shares'),
        func.sum(ShareEvent.points_earned).label('points')
    ).group_by(ShareEvent.platform).all()

    total_all_shares = sum(stat.shares for stat in platform_stats) or 1  # Avoid division by zero
    platform_breakdown = {}

    for stat in platform_stats:
        platform_name = stat.platform.value if hasattr(stat.platform, 'value') else str(stat.platform)
        platform_breakdown[platform_name] = {
            "shares": stat.shares,
            "percentage": round((stat.shares / total_all_shares) * 100, 1)
        }

    # Ensure all platforms are represented
    for platform in ["facebook", "twitter", "linkedin", "instagram"]:
        if platform not in platform_breakdown:
            platform_breakdown[platform] = {"shares": 0, "percentage": 0}

    # Growth metrics (simplified for now)
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_7d = db.query(User).filter(User.created_at >= week_ago).count()

    growth_metrics = {
        "new_users_7d": new_users_7d,
        "user_retention_rate": 0,  # TODO: Implement retention calculation
        "average_session_duration": 0  # TODO: Implement session tracking
    }

    return AdminDashboardResponse(
        overview={
            "total_users": total_users,
            "active_users_24h": active_users_24h,
            "total_shares_today": total_shares_today,
            "points_distributed_today": points_distributed_today
        },
        platform_breakdown=platform_breakdown,
        growth_metrics=growth_metrics
    )

@router.get("/analytics")
def admin_analytics(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    """
    Get comprehensive analytics for admin panel.
    Returns system-wide share analytics across all users.
    """
    try:
        from app.models.share import ShareEvent, PlatformEnum
        from sqlalchemy import func
        from datetime import datetime, timedelta

        # Get all share events
        all_shares = db.query(ShareEvent).all()
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

        # Timeline data (last 30 days) - system-wide
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

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Admin analytics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate admin analytics"
        )

@router.get("/share-history")
def admin_share_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    platform: str = Query(None),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """
    Get system-wide share history for admin panel.
    Returns all share events across all users with pagination.
    """
    try:
        from app.models.share import ShareEvent, PlatformEnum
        from sqlalchemy import desc

        # Build query for all share events
        query = db.query(ShareEvent).join(User)

        # Filter by platform if specified
        if platform and platform != 'all':
            try:
                platform_enum = PlatformEnum(platform)
                query = query.filter(ShareEvent.platform == platform_enum)
            except ValueError:
                pass  # Invalid platform, ignore filter

        # Get total count for pagination
        total_shares = query.count()

        # Apply pagination and ordering
        offset = (page - 1) * limit
        share_events = query.order_by(desc(ShareEvent.created_at)).offset(offset).limit(limit).all()

        # Format response
        shares = []
        for event in share_events:
            platform_value = event.platform.value if hasattr(event.platform, 'value') else str(event.platform)
            shares.append({
                "id": event.id,
                "platform": platform_value,
                "points_earned": event.points_earned,
                "timestamp": event.created_at.isoformat(),
                "user_name": event.user.name,
                "user_email": event.user.email
            })

        # Calculate pagination info
        total_pages = (total_shares + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1

        return {
            "shares": shares,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_shares,
                "items_per_page": limit,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Admin share history failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get share history"
        )

@router.get("/platform-stats")
def admin_platform_stats(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    """
    Get detailed platform statistics for admin panel.
    Returns comprehensive stats for each platform.
    """
    try:
        from app.models.share import ShareEvent, PlatformEnum
        from sqlalchemy import func
        from datetime import datetime, timedelta

        # Get all share events
        all_shares = db.query(ShareEvent).all()
        total_shares = len(all_shares)
        total_points = sum(s.points_earned for s in all_shares)

        # Calculate stats for each platform
        platform_stats = {}

        for platform in PlatformEnum:
            platform_shares = [s for s in all_shares if s.platform == platform]
            shares_count = len(platform_shares)
            points_sum = sum(s.points_earned for s in platform_shares)

            if shares_count > 0:
                # Calculate additional metrics
                first_share = min(platform_shares, key=lambda x: x.created_at)
                last_share = max(platform_shares, key=lambda x: x.created_at)

                # Get unique users for this platform
                unique_users = len(set(s.user_id for s in platform_shares))

                # Calculate recent activity (last 7 days)
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_shares = [s for s in platform_shares if s.created_at >= week_ago]

                # Calculate daily average
                days_active = (datetime.utcnow() - first_share.created_at).days + 1
                daily_average = round(shares_count / days_active, 2) if days_active > 0 else 0

                platform_stats[platform.value] = {
                    "shares": shares_count,
                    "points": points_sum,
                    "percentage": round((shares_count / total_shares * 100), 1) if total_shares > 0 else 0,
                    "unique_users": unique_users,
                    "first_share_date": first_share.created_at.isoformat(),
                    "last_share_date": last_share.created_at.isoformat(),
                    "recent_shares_7d": len(recent_shares),
                    "daily_average": daily_average,
                    "points_per_share": round(points_sum / shares_count, 2) if shares_count > 0 else 0
                }
            else:
                platform_stats[platform.value] = {
                    "shares": 0,
                    "points": 0,
                    "percentage": 0,
                    "unique_users": 0,
                    "recent_shares_7d": 0,
                    "daily_average": 0,
                    "points_per_share": 0
                }

        return {
            "platform_stats": platform_stats,
            "summary": {
                "total_shares": total_shares,
                "total_points": total_points,
                "total_platforms": len([p for p in platform_stats.values() if p["shares"] > 0])
            }
        }

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Admin platform stats failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get platform statistics"
        )

@router.get("/users", response_model=AdminUsersResponse)
def admin_users(db: Session = Depends(get_db), admin=Depends(get_current_admin), page: int = 1, limit: int = 50, search: str = "", sort: str = "points"):
    """List users for admin panel with pagination, search, and sorting."""
    q = db.query(User)
    if search:
        q = q.filter(User.name.ilike(f"%{search}%"))
    if sort == "points":
        q = q.order_by(User.total_points.desc())
    total = q.count()
    users = q.offset((page-1)*limit).limit(limit).all()
    items = [AdminUser(user_id=u.id, name=u.name, email=u.email, points=u.total_points, rank=None, shares_count=u.shares_count, status="active" if u.is_active else "inactive", last_activity=u.updated_at, created_at=u.created_at) for u in users]
    return AdminUsersResponse(users=items, pagination={"page": page, "limit": limit, "total": total, "pages": (total+limit-1)//limit})

@router.post("/send-bulk-email")
def send_bulk_email(req: BulkEmailRequest, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    """Send a bulk email to all or filtered users (min_points)."""
    users = get_bulk_email_recipients(db, req.min_points)
    emails = [u.email for u in users]
    if not emails:
        raise HTTPException(status_code=404, detail="No users found for criteria")
    send_bulk_email_task.delay(emails, req.subject, req.body)
    inc_bulk_email_sent()
    logging.info(f"Admin {admin['user_id']} sent bulk email to {len(emails)} users.")
    return {"message": f"Bulk email sent to {len(emails)} users (task queued)"}

@router.post("/promote")
def promote_user(req: PromoteRequest, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    """Promote a user to admin status."""
    user = promote_user_to_admin(db, req.user_id)
    inc_admin_promotion()
    logging.info(f"Admin {admin['user_id']} promoted user {user.email} to admin.")
    return {"message": f"User {user.email} promoted to admin."} 