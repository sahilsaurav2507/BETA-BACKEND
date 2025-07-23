from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: constr(min_length=1, max_length=100)
    email: EmailStr
    password: constr(min_length=6, max_length=128)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    created_at: datetime
    total_points: int
    shares_count: int
    default_rank: Optional[int] = None
    current_rank: Optional[int] = None
    is_admin: Optional[bool] = False

    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    name: Optional[str]
    bio: Optional[str] 