from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class PlatformEnum(enum.Enum):
    facebook = "facebook"
    twitter = "twitter"
    linkedin = "linkedin"
    instagram = "instagram"
    whatsapp = "whatsapp"  # Added to match SQL schema

class ShareEvent(Base):
    __tablename__ = "share_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(Enum(PlatformEnum), index=True)
    points_earned = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Optimized relationship to prevent N+1 queries
    user = relationship(
        "User",
        back_populates="share_events",
        lazy="joined"  # Use joined loading for many-to-one relationships
    )

# Performance-optimized indexes
Index('idx_share_events_user_id', ShareEvent.user_id)
Index('idx_share_events_platform', ShareEvent.platform)
Index('idx_share_events_user_platform', ShareEvent.user_id, ShareEvent.platform)
Index('idx_share_events_user_created', ShareEvent.user_id, ShareEvent.created_at.desc())
Index('idx_share_events_covering', ShareEvent.user_id, ShareEvent.platform, ShareEvent.points_earned, ShareEvent.created_at.desc())