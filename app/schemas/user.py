from pydantic import BaseModel, EmailStr, constr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# =====================================================
# INPUT MODELS (for creating/updating data)
# =====================================================

class UserCreate(BaseModel):
    """Model for user creation - only essential fields."""
    name: constr(min_length=1, max_length=100)
    email: EmailStr
    password: constr(min_length=6, max_length=128)

class UserLogin(BaseModel):
    """Model for user authentication - minimal data."""
    email: EmailStr
    password: str

class UserProfileUpdate(BaseModel):
    """Model for profile updates - optional fields only."""
    name: Optional[constr(min_length=1, max_length=100)] = None
    bio: Optional[constr(max_length=500)] = None

# =====================================================
# OUTPUT MODELS (for API responses)
# =====================================================

class UserPublic(BaseModel):
    """Public user data - safe for external exposure."""
    user_id: int = Field(alias="id")
    name: str
    total_points: int
    shares_count: int
    current_rank: Optional[int] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class UserPrivate(BaseModel):
    """Private user data - includes sensitive information."""
    user_id: int = Field(alias="id")
    name: str
    email: EmailStr
    created_at: datetime
    total_points: int
    shares_count: int
    default_rank: Optional[int] = None
    current_rank: Optional[int] = None
    is_admin: bool = False
    is_active: bool = True

    class Config:
        from_attributes = True
        populate_by_name = True

class UserResponse(UserPrivate):
    """Legacy response model - maintains backward compatibility."""
    pass

class UserInDB(BaseModel):
    """Internal model for database operations - includes all fields."""
    id: int
    name: str
    email: EmailStr
    password_hash: str
    total_points: int
    shares_count: int
    default_rank: Optional[int] = None
    current_rank: Optional[int] = None
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# =====================================================
# SPECIALIZED MODELS (for specific use cases)
# =====================================================

class UserLeaderboard(BaseModel):
    """Optimized model for leaderboard display."""
    rank: int
    user_id: int = Field(alias="id")
    name: str
    points: int = Field(alias="total_points")
    shares_count: int
    badge: Optional[str] = None
    rank_improvement: Optional[int] = 0

    class Config:
        from_attributes = True
        populate_by_name = True

class UserStats(BaseModel):
    """Model for user statistics and analytics."""
    user_id: int = Field(alias="id")
    name: str
    total_points: int
    shares_count: int
    platforms_used: int = 0
    avg_points_per_share: float = 0.0
    first_share_date: Optional[datetime] = None
    last_share_date: Optional[datetime] = None
    most_used_platform: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class UserProfile(BaseModel):
    """Complete user profile with related data."""
    user_id: int = Field(alias="id")
    name: str
    email: EmailStr
    created_at: datetime
    total_points: int
    shares_count: int
    current_rank: Optional[int] = None
    rank_improvement: Optional[int] = 0
    share_history: List[Dict[str, Any]] = []
    platform_breakdown: Dict[str, Dict[str, int]] = {}

    class Config:
        from_attributes = True
        populate_by_name = True

# =====================================================
# BULK OPERATION MODELS
# =====================================================

class UserBulkResponse(BaseModel):
    """Model for bulk user operations."""
    users: List[UserPublic]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool

class UserExport(BaseModel):
    """Model for user data export."""
    user_id: int = Field(alias="id")
    name: str
    email: EmailStr
    total_points: int
    shares_count: int
    created_at: datetime
    is_admin: bool

    class Config:
        from_attributes = True
        populate_by_name = True