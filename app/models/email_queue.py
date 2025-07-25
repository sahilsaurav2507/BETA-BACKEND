"""
Email Queue Model for Database-Driven Email Scheduling
=====================================================

This model replaces Redis/Celery with a pure database approach for email scheduling.
Implements sequential 5-minute email queue processing.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Index
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class EmailType(str, enum.Enum):
    """Email types supported by the queue system."""
    welcome = "welcome"
    search_engine = "search_engine"
    portfolio_builder = "portfolio_builder"
    platform_complete = "platform_complete"


class EmailStatus(str, enum.Enum):
    """Email processing status."""
    pending = "pending"
    processing = "processing"
    sent = "sent"
    failed = "failed"
    cancelled = "cancelled"


class EmailQueue(Base):
    """
    Email Queue Model
    
    Stores emails to be sent with scheduled timing to ensure 5-minute intervals
    between email sends regardless of registration volume.
    """
    __tablename__ = "email_queue"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Email details
    user_email = Column(String(255), nullable=False, index=True)
    user_name = Column(String(255), nullable=False)
    email_type = Column(
        Enum(EmailType), 
        nullable=False, 
        index=True
    )
    
    # Email content (optional - can be generated from templates)
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=True)
    
    # Scheduling and status
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(
        Enum(EmailStatus),
        nullable=False,
        default=EmailStatus.pending,
        index=True
    )
    
    # Retry and error handling
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    def __repr__(self):
        return f"<EmailQueue(id={self.id}, email={self.user_email}, type={self.email_type}, status={self.status})>"
    
    @property
    def is_pending(self) -> bool:
        """Check if email is pending."""
        return self.status == EmailStatus.pending

    @property
    def is_sent(self) -> bool:
        """Check if email was sent successfully."""
        return self.status == EmailStatus.sent

    @property
    def is_failed(self) -> bool:
        """Check if email failed to send."""
        return self.status == EmailStatus.failed

    @property
    def can_retry(self) -> bool:
        """Check if email can be retried."""
        return self.status == EmailStatus.failed and self.retry_count < self.max_retries
    
    @property
    def is_max_retries_reached(self) -> bool:
        """Check if maximum retries have been reached."""
        return self.retry_count >= self.max_retries


# Indexes for optimal query performance
Index('idx_email_queue_status_scheduled', EmailQueue.status, EmailQueue.scheduled_time)
Index('idx_email_queue_user_email', EmailQueue.user_email)
Index('idx_email_queue_email_type', EmailQueue.email_type)
Index('idx_email_queue_created_at', EmailQueue.created_at)
