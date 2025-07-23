from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.schemas.user import UserResponse, UserProfileUpdate
from app.services.user_service import get_user_by_id, update_user_profile
from app.core.security import verify_access_token, get_current_admin
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User
import csv
import io

router = APIRouter(prefix="/users", tags=["users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.get("/{user_id}/profile", response_model=UserResponse)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
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

@router.get("/view", response_model=list[UserResponse])
def view_all_users(admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [UserResponse(
        user_id=u.id,
        name=u.name,
        email=u.email,
        created_at=u.created_at,
        total_points=u.total_points,
        shares_count=u.shares_count,
        current_rank=None,
        is_admin=u.is_admin
    ) for u in users]

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