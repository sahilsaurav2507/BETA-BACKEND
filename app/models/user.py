from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    total_points = Column(Integer, default=0, index=True)
    shares_count = Column(Integer, default=0)
    default_rank = Column(Integer, nullable=True, index=True)  # Registration order rank
    current_rank = Column(Integer, nullable=True, index=True)  # Dynamic rank based on points
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    feedback_responses = relationship("Feedback", back_populates="user", lazy="dynamic")

Index('idx_users_total_points', User.total_points)
Index('idx_users_email', User.email)
Index('idx_users_current_rank', User.current_rank)
Index('idx_users_default_rank', User.default_rank)