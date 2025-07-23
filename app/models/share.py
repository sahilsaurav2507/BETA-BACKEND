from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class PlatformEnum(enum.Enum):
    facebook = "facebook"
    twitter = "twitter"
    linkedin = "linkedin"
    instagram = "instagram"

class ShareEvent(Base):
    __tablename__ = "share_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(Enum(PlatformEnum), index=True)
    points_earned = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

Index('idx_share_events_user_id', ShareEvent.user_id)
Index('idx_share_events_platform', ShareEvent.platform) 