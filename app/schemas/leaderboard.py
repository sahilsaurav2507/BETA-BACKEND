from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

# =====================================================
# ENUMS AND CONSTANTS
# =====================================================

class LeaderboardType(str, Enum):
    """Types of leaderboards available."""
    global_points = "global_points"
    weekly_points = "weekly_points"
    monthly_points = "monthly_points"
    shares_count = "shares_count"
    recent_activity = "recent_activity"

class TimePeriod(str, Enum):
    """Time periods for leaderboard filtering."""
    all_time = "all_time"
    today = "today"
    week = "week"
    month = "month"
    year = "year"

# =====================================================
# CORE LEADERBOARD MODELS
# =====================================================

class LeaderboardUser(BaseModel):
    """Individual user entry in leaderboard."""
    rank: int
    user_id: int
    name: str
    points: int
    shares_count: int
    badge: Optional[str] = None
    default_rank: Optional[int] = None
    rank_improvement: Optional[int] = 0
    last_activity: Optional[datetime] = None

    @validator('badge', pre=True, always=True)
    def set_badge(cls, v, values):
        if v is not None:
            return v
        rank = values.get('rank', 0)
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

class LeaderboardResponse(BaseModel):
    """Complete leaderboard response with metadata."""
    leaderboard: List[LeaderboardUser]
    pagination: Dict[str, int]
    metadata: Dict[str, Any]
    leaderboard_type: LeaderboardType = LeaderboardType.global_points
    time_period: TimePeriod = TimePeriod.all_time
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    total_users: int = 0

# =====================================================
# SPECIALIZED LEADERBOARD MODELS
# =====================================================

class AroundMeUser(BaseModel):
    """User entry for 'around me' leaderboard view."""
    rank: int
    name: str
    points: int
    is_current_user: bool = False
    rank_change: Optional[int] = 0
    badge: Optional[str] = None

class AroundMeResponse(BaseModel):
    """Response for 'around me' leaderboard view."""
    surrounding_users: List[AroundMeUser]
    your_stats: Dict[str, Union[int, float, str]]
    range_size: int = 5
    total_users_in_range: int = 0

class TopPerformer(BaseModel):
    """Model for top performers in specific time periods."""
    rank: int
    user_id: int
    name: str
    points_gained: int
    total_points: int
    growth_rate: str
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    shares_in_period: int = 0

class TopPerformersResponse(BaseModel):
    """Response for top performers query."""
    performers: List[TopPerformer]
    time_period: TimePeriod
    period_start: datetime
    period_end: datetime
    total_performers: int = 0

# =====================================================
# ANALYTICS AND INSIGHTS MODELS
# =====================================================

class LeaderboardInsights(BaseModel):
    """Analytics insights for leaderboard data."""
    total_active_users: int
    average_points: float
    median_points: float
    top_10_threshold: int
    competition_intensity: float  # Points needed to move up one rank
    growth_trends: Dict[str, float]
    platform_leaders: Dict[str, str]  # platform -> top user name

class RankingHistory(BaseModel):
    """Historical ranking data for a user."""
    user_id: int
    date: datetime
    rank: int
    points: int
    rank_change: int = 0
    percentile: float = 0.0

class LeaderboardStats(BaseModel):
    """Statistical information about the leaderboard."""
    total_users: int
    active_users_24h: int
    active_users_7d: int
    points_distribution: Dict[str, int]  # range -> count
    rank_volatility: float  # How much ranks change on average
    new_users_today: int
    climbing_users: int  # Users who improved rank
    falling_users: int   # Users who lost rank

# =====================================================
# DASHBOARD AND ADMIN MODELS
# =====================================================

class LeaderboardDashboard(BaseModel):
    """Complete dashboard view of leaderboard data."""
    current_leaderboard: List[LeaderboardUser]
    insights: LeaderboardInsights
    stats: LeaderboardStats
    top_performers_week: List[TopPerformer]
    recent_climbers: List[AroundMeUser]
    platform_breakdown: Dict[str, int]

class AdminLeaderboardView(BaseModel):
    """Admin view of leaderboard with additional data."""
    user_id: int
    name: str
    email: str
    current_rank: int
    previous_rank: Optional[int] = None
    points: int
    shares_count: int
    last_activity: Optional[datetime] = None
    account_status: str = "active"
    flags: List[str] = []  # Any admin flags or notes

# =====================================================
# EXPORT AND BULK MODELS
# =====================================================

class LeaderboardExport(BaseModel):
    """Model for leaderboard data export."""
    rank: int
    user_id: int
    name: str
    email: str
    points: int
    shares_count: int
    join_date: datetime
    last_activity: Optional[datetime] = None

    class Config:
        from_attributes = True

class TopPerformersResponse(BaseModel):
    period: str
    top_performers: List[TopPerformer]
    period_stats: Dict[str, Any]