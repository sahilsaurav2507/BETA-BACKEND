from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class ShareCreate(BaseModel):
    platform: str

class ShareResponse(BaseModel):
    share_id: Optional[int]
    user_id: int
    platform: str
    points_earned: int
    total_points: int
    new_rank: Optional[int]
    timestamp: datetime
    message: str

class ShareHistoryItem(BaseModel):
    share_id: int
    platform: str
    points_earned: int
    timestamp: datetime

class ShareHistoryResponse(BaseModel):
    shares: List[ShareHistoryItem]
    pagination: Dict[str, int]

class ShareAnalyticsResponse(BaseModel):
    total_shares: int
    points_breakdown: Dict[str, Dict[str, int]]
    recent_activity: Optional[List[Dict[str, str]]] 