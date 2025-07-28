from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# =====================================================
# ENUMS AND CONSTANTS
# =====================================================

class PlatformType(str, Enum):
    """Platform types for sharing."""
    facebook = "facebook"
    twitter = "twitter"
    linkedin = "linkedin"
    instagram = "instagram"
    whatsapp = "whatsapp"

# =====================================================
# INPUT MODELS (for creating/updating data)
# =====================================================

class ShareCreate(BaseModel):
    """Model for creating a share event."""
    platform: PlatformType

    @validator('platform')
    def validate_platform(cls, v):
        if v not in PlatformType:
            raise ValueError(f'Invalid platform. Must be one of: {list(PlatformType)}')
        return v

# =====================================================
# OUTPUT MODELS (for API responses)
# =====================================================

class ShareResponse(BaseModel):
    """Response model for share creation."""
    share_id: Optional[int] = None
    user_id: int
    platform: str
    points_earned: int
    total_points: int
    new_rank: Optional[int] = None
    timestamp: datetime
    message: str
    rank_change: Optional[int] = 0

class ShareHistoryItem(BaseModel):
    """Individual share item for history display."""
    share_id: int = Field(alias="id")
    platform: str
    points_earned: int
    timestamp: datetime = Field(alias="created_at")

    class Config:
        from_attributes = True
        populate_by_name = True

class ShareHistoryResponse(BaseModel):
    """Response model for share history with pagination."""
    shares: List[ShareHistoryItem]
    pagination: Dict[str, int]
    total_points: int = 0
    total_shares: int = 0

class ShareAnalyticsResponse(BaseModel):
    """Response model for share analytics."""
    total_shares: int
    total_points: int
    points_breakdown: Dict[str, Dict[str, int]]
    recent_activity: Optional[List[Dict[str, Any]]] = []
    platform_stats: Dict[str, Any] = {}
    performance_metrics: Dict[str, float] = {}

# =====================================================
# SPECIALIZED MODELS (for specific use cases)
# =====================================================

class ShareStats(BaseModel):
    """Model for share statistics."""
    platform: str
    share_count: int
    total_points: int
    avg_points_per_share: float
    last_share_date: Optional[datetime] = None
    first_share_date: Optional[datetime] = None

class PlatformAnalytics(BaseModel):
    """Analytics for a specific platform."""
    platform: str
    total_shares: int
    total_points: int
    unique_users: int
    avg_points_per_share: float
    growth_rate: float = 0.0
    last_activity: Optional[datetime] = None

class ShareTrend(BaseModel):
    """Model for share trends over time."""
    date: datetime
    shares_count: int
    points_earned: int
    unique_users: int

class UserShareSummary(BaseModel):
    """Summary of user's sharing activity."""
    user_id: int
    total_shares: int
    total_points: int
    platforms_used: List[str]
    most_active_platform: Optional[str] = None
    avg_points_per_share: float = 0.0
    sharing_streak: int = 0
    last_share_date: Optional[datetime] = None

# =====================================================
# BULK OPERATION MODELS
# =====================================================

class ShareBulkResponse(BaseModel):
    """Model for bulk share operations."""
    shares: List[ShareHistoryItem]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool

class ShareExport(BaseModel):
    """Model for share data export."""
    share_id: int = Field(alias="id")
    user_id: int
    user_name: str
    platform: str
    points_earned: int
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

# =====================================================
# DASHBOARD MODELS
# =====================================================

class ShareDashboard(BaseModel):
    """Model for share dashboard data."""
    total_shares_today: int = 0
    total_points_today: int = 0
    active_users_today: int = 0
    platform_breakdown: Dict[str, int] = {}
    trending_platforms: List[str] = []
    recent_shares: List[ShareHistoryItem] = []
    growth_metrics: Dict[str, float] = {}

class ShareLeaderboard(BaseModel):
    """Model for share-based leaderboard."""
    rank: int
    user_id: int
    user_name: str
    total_shares: int
    total_points: int
    favorite_platform: Optional[str] = None
    recent_activity: Optional[datetime] = None