"""
Email Queue Pydantic Schemas
============================

Schemas for email queue operations including validation and serialization.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from app.models.email_queue import EmailType, EmailStatus


class EmailQueueCreate(BaseModel):
    """Schema for creating a new email queue entry."""
    user_email: EmailStr
    user_name: str = Field(..., min_length=1, max_length=255)
    email_type: EmailType
    subject: Optional[str] = Field(None, max_length=500)
    body: Optional[str] = None
    scheduled_time: Optional[datetime] = None  # If None, will be auto-calculated
    max_retries: int = Field(default=3, ge=0, le=10)
    
    @validator('user_name')
    def validate_user_name(cls, v):
        if not v or not v.strip():
            raise ValueError('User name cannot be empty')
        return v.strip()


class EmailQueueUpdate(BaseModel):
    """Schema for updating email queue entry."""
    status: Optional[EmailStatus] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = Field(None, ge=0)
    scheduled_time: Optional[datetime] = None


class EmailQueueResponse(BaseModel):
    """Schema for email queue response."""
    id: int
    user_email: EmailStr
    user_name: str
    email_type: EmailType
    subject: Optional[str]
    body: Optional[str]
    scheduled_time: datetime
    status: EmailStatus
    retry_count: int
    max_retries: int
    error_message: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]
    updated_at: datetime
    
    # Computed properties
    is_pending: bool
    is_sent: bool
    is_failed: bool
    can_retry: bool
    is_max_retries_reached: bool
    
    class Config:
        from_attributes = True


class EmailQueueStats(BaseModel):
    """Schema for email queue statistics."""
    total_emails: int
    pending_count: int
    processing_count: int
    sent_count: int
    failed_count: int
    cancelled_count: int
    next_scheduled: Optional[datetime]
    last_sent: Optional[datetime]


class EmailQueueByType(BaseModel):
    """Schema for email queue statistics by type."""
    email_type: EmailType
    status: EmailStatus
    count: int
    oldest_email: Optional[datetime]
    newest_email: Optional[datetime]
    avg_processing_time_minutes: Optional[float]


class FailedEmailSummary(BaseModel):
    """Schema for failed email summary."""
    id: int
    user_email: EmailStr
    user_name: str
    email_type: EmailType
    subject: Optional[str]
    scheduled_time: datetime
    retry_count: int
    max_retries: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmailProcessingResult(BaseModel):
    """Schema for email processing results."""
    email_id: int
    success: bool
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    retry_count: int = 0


class BulkEmailQueueCreate(BaseModel):
    """Schema for creating multiple email queue entries."""
    emails: list[EmailQueueCreate]
    
    @validator('emails')
    def validate_emails_not_empty(cls, v):
        if not v:
            raise ValueError('Email list cannot be empty')
        if len(v) > 1000:  # Reasonable limit
            raise ValueError('Cannot queue more than 1000 emails at once')
        return v


class EmailQueueFilter(BaseModel):
    """Schema for filtering email queue entries."""
    status: Optional[EmailStatus] = None
    email_type: Optional[EmailType] = None
    user_email: Optional[EmailStr] = None
    scheduled_after: Optional[datetime] = None
    scheduled_before: Optional[datetime] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class NextScheduleTimeResponse(BaseModel):
    """Schema for next available schedule time."""
    next_scheduled_time: datetime
    queue_position: int
    estimated_delay_minutes: int
