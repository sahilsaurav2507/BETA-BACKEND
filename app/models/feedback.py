from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class BiggestHurdleEnum(enum.Enum):
    A = "A"  # Time commitment
    B = "B"  # Simplifying topics
    C = "C"  # Audience reach
    D = "D"  # Ethics/compliance
    E = "E"  # Other

class PrimaryMotivationEnum(enum.Enum):
    A = "A"  # Brand building
    B = "B"  # Client attraction
    C = "C"  # Revenue stream
    D = "D"  # Education/contribution

class TimeConsumingPartEnum(enum.Enum):
    A = "A"  # Research
    B = "B"  # Drafting
    C = "C"  # Editing
    D = "D"  # Formatting

class ProfessionalFearEnum(enum.Enum):
    A = "A"  # Losing clients
    B = "B"  # Becoming irrelevant
    C = "C"  # Being outdated
    D = "D"  # No fear

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)

    # User identification (optional - can be anonymous)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Contact information
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Multiple choice responses
    biggest_hurdle = Column(Enum(BiggestHurdleEnum), nullable=False, index=True)
    biggest_hurdle_other = Column(Text, nullable=True)
    primary_motivation = Column(Enum(PrimaryMotivationEnum), nullable=True, index=True)
    time_consuming_part = Column(Enum(TimeConsumingPartEnum), nullable=True, index=True)
    professional_fear = Column(Enum(ProfessionalFearEnum), nullable=False, index=True)

    # Short answer responses (2-4 sentences each)
    monetization_considerations = Column(Text, nullable=True)
    professional_legacy = Column(Text, nullable=True)
    platform_impact = Column(Text, nullable=False)
    
    # Metadata
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to user (optional)
    user = relationship("User", back_populates="feedback_responses")

# Add indexes for performance
Index('idx_feedback_user_id', Feedback.user_id)
Index('idx_feedback_submitted_at', Feedback.submitted_at)
Index('idx_feedback_biggest_hurdle', Feedback.biggest_hurdle)
Index('idx_feedback_primary_motivation', Feedback.primary_motivation)
Index('idx_feedback_professional_fear', Feedback.professional_fear)
Index('idx_feedback_time_consuming_part', Feedback.time_consuming_part)
