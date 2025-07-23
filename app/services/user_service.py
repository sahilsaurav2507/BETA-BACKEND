from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import create_access_token
from passlib.context import CryptContext
from app.schemas.user import UserCreate, UserProfileUpdate
from fastapi import HTTPException, status
from datetime import datetime
from typing import List

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_email(db: Session, email: str):
    """Retrieve a user by email address."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    """Retrieve a user by user ID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_in: UserCreate, is_admin: bool = False):
    """Create a new user with dynamic ranking. Optionally set as admin."""
    if get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(user_in.password)
    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hashed_password,
        is_admin=is_admin,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Assign default rank for non-admin users
    if not is_admin:
        from app.services.ranking_service import assign_default_rank
        assign_default_rank(db, user.id)
        db.refresh(user)  # Refresh to get updated rank fields

    return user


def authenticate_user(db: Session, email: str, password: str):
    """Authenticate a user by email and password."""
    user = get_user_by_email(db, email)
    if not user or not pwd_context.verify(password, user.password_hash):
        return None
    return user


def update_user_profile(db: Session, user_id: int, profile_in: UserProfileUpdate):
    """Update a user's profile information."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if profile_in.name:
        user.name = profile_in.name
    if hasattr(profile_in, "bio") and profile_in.bio is not None:
        user.bio = profile_in.bio
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def create_jwt_for_user(user: User):
    """Create a JWT for the given user."""
    token = create_access_token({"user_id": user.id, "email": user.email, "is_admin": user.is_admin})
    return token


def promote_user_to_admin(db: Session, user_id: int):
    """Promote a user to admin status."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="User is already an admin")
    user.is_admin = True
    db.commit()
    db.refresh(user)
    return user


def get_bulk_email_recipients(db: Session, min_points: int = 0) -> List[User]:
    """Get all active users with at least min_points for bulk email."""
    return db.query(User).filter(User.total_points >= min_points, User.is_active == True).all() 