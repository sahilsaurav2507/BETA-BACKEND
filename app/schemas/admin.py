from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional
from datetime import datetime

class AdminUser(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    points: int
    rank: Optional[int]
    shares_count: int
    status: str
    last_activity: Optional[datetime]
    created_at: datetime

class AdminUsersResponse(BaseModel):
    users: List[AdminUser]
    pagination: Dict[str, int]

class AdminDashboardResponse(BaseModel):
    overview: Dict[str, int]
    platform_breakdown: Dict[str, Dict[str, float]]
    growth_metrics: Dict[str, float] 