from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class LeaderboardUser(BaseModel):
    rank: int
    user_id: int
    name: str
    points: int
    shares_count: int
    badge: Optional[str] = None

class LeaderboardResponse(BaseModel):
    leaderboard: List[LeaderboardUser]
    pagination: Dict[str, int]
    metadata: Dict[str, Optional[int]]

class AroundMeUser(BaseModel):
    rank: int
    name: str
    points: int
    is_current_user: Optional[bool] = False

class AroundMeResponse(BaseModel):
    surrounding_users: List[AroundMeUser]
    your_stats: Dict[str, float]

class TopPerformer(BaseModel):
    rank: int
    user_id: int
    name: str
    points_gained: int
    total_points: int
    growth_rate: str

class TopPerformersResponse(BaseModel):
    period: str
    top_performers: List[TopPerformer]
    period_stats: Dict[str, Any]