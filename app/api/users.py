from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.schemas.user import (
    UserResponse, UserProfileUpdate, UserPublic, UserPrivate,
    UserProfile, UserStats, UserBulkResponse, UserExport
)
from app.services.user_service import get_user_by_id, update_user_profile
from app.services.optimized_query_service import optimized_query_service
from app.utils.pagination import get_pagination_params, PaginationParams
from app.core.security import verify_access_token, get_current_admin
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User
import csv
import io

router = APIRouter(prefix="/users", tags=["users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.get("/{user_id}/profile", response_model=UserProfile)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    """
    Get complete user profile with optimized data loading.

    Uses eager loading to prevent N+1 queries and includes
    share history and platform breakdown for comprehensive profile data.
    """
    # Use optimized query service to get user with all related data
    user = optimized_query_service.get_user_with_complete_profile(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user's rank efficiently
    rank_data = optimized_query_service.get_user_rank_optimized(db, user_id)
    current_rank = rank_data["rank"] if rank_data else None

    # Get share analytics efficiently
    share_analytics = optimized_query_service.get_share_analytics_optimized(db, user_id)

    # Build share history (last 10 shares)
    share_history_data = optimized_query_service.get_share_history_optimized(
        db, user_id, page=1, limit=10
    )

    return UserProfile(
        user_id=user.id,
        name=user.name,
        email=user.email,
        created_at=user.created_at,
        total_points=user.total_points,
        shares_count=user.shares_count,
        current_rank=current_rank,
        rank_improvement=user.default_rank - current_rank if user.default_rank and current_rank else 0,
        share_history=[share.dict() for share in share_history_data["shares"]],
        platform_breakdown=share_analytics.points_breakdown
    )

@router.put("/profile", response_model=UserResponse)
def update_profile(profile_in: UserProfileUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = update_user_profile(db, payload["user_id"], profile_in)
    return UserResponse(
        user_id=user.id,
        name=user.name,
        email=user.email,
        created_at=user.created_at,
        total_points=user.total_points,
        shares_count=user.shares_count,
        current_rank=None,
        is_admin=user.is_admin
    )

@router.get("/view", response_model=UserBulkResponse)
def view_all_users(
    pagination: PaginationParams = Depends(get_pagination_params),
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all users with optimized pagination and efficient data loading.

    Uses server-side pagination and optimized queries to handle large user datasets
    efficiently. Includes share statistics with eager loading to prevent N+1 queries.
    """
    # Use optimized query service with pagination
    users = optimized_query_service.get_users_with_share_stats(
        db,
        limit=pagination.limit,
        offset=pagination.offset,
        include_admin=True
    )

    # Get total count for pagination
    total_count = db.query(User).count()

    # Convert to public user format
    user_list = [
        UserPublic(
            user_id=u.id,
            name=u.name,
            total_points=u.total_points,
            shares_count=u.shares_count,
            current_rank=None  # Could be calculated if needed
        ) for u in users
    ]

    return UserBulkResponse(
        users=user_list,
        total_count=total_count,
        page=pagination.page,
        limit=pagination.limit,
        has_next=pagination.offset + pagination.limit < total_count,
        has_prev=pagination.page > 1
    )

@router.get("/export")
def export_users(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
    format: str = Query("csv", enum=["csv", "json"]),
    min_points: int = Query(0)
):
    users = db.query(User).filter(User.total_points >= min_points).all()
    if format == "json":
        data = [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "total_points": u.total_points,
                "shares_count": u.shares_count,
                "created_at": str(u.created_at),
                "is_admin": u.is_admin
            }
            for u in users
        ]
        from fastapi.responses import JSONResponse
        return JSONResponse(content=data)
    # Default: CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "name", "email", "total_points", "shares_count", "created_at", "is_admin"])
    for u in users:
        writer.writerow([u.id, u.name, u.email, u.total_points, u.shares_count, u.created_at, u.is_admin])
    output.seek(0)
    return Response(
        content=output.read(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"}
    ) 