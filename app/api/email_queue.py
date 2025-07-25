"""
Email Queue Management API
=========================

API endpoints for monitoring and managing the database-driven email queue.
Provides admin interface for queue status, failed emails, and manual operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.dependencies import get_db
from app.core.security import verify_access_token
from app.models.user import User
from app.models.email_queue import EmailQueue, EmailType, EmailStatus
from app.schemas.email_queue import (
    EmailQueueResponse, EmailQueueStats, FailedEmailSummary,
    NextScheduleTimeResponse, EmailQueueFilter
)
from app.services.email_queue_service import (
    get_queue_stats, get_failed_emails, retry_failed_email,
    get_next_schedule_info, add_campaign_emails_for_all_users,
    get_campaign_status, get_pending_emails
)

router = APIRouter(prefix="/email-queue", tags=["email-queue"])
logger = logging.getLogger(__name__)


def get_current_admin_user(token: str = Depends(verify_access_token), db: Session = Depends(get_db)):
    """Verify that the current user is an admin."""
    user = db.query(User).filter(User.email == token["email"]).first()
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


@router.get("/stats", response_model=EmailQueueStats)
def get_email_queue_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get email queue statistics.
    
    Returns overall queue statistics including counts by status.
    """
    try:
        stats = get_queue_stats(db)
        logger.info(f"Queue stats requested by admin {current_user.email}")
        return stats
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get queue statistics"
        )


@router.get("/pending", response_model=List[EmailQueueResponse])
def get_pending_emails_endpoint(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get pending emails in the queue.
    
    Returns list of emails waiting to be sent.
    """
    try:
        pending_emails = get_pending_emails(db, limit=limit)
        
        # Convert to response format
        response_emails = []
        for email in pending_emails:
            response_emails.append(EmailQueueResponse(
                id=email.id,
                user_email=email.user_email,
                user_name=email.user_name,
                email_type=email.email_type,
                subject=email.subject,
                body=email.body,
                scheduled_time=email.scheduled_time,
                status=email.status,
                retry_count=email.retry_count,
                max_retries=email.max_retries,
                error_message=email.error_message,
                created_at=email.created_at,
                sent_at=email.sent_at,
                updated_at=email.updated_at,
                is_pending=email.is_pending,
                is_sent=email.is_sent,
                is_failed=email.is_failed,
                can_retry=email.can_retry,
                is_max_retries_reached=email.is_max_retries_reached
            ))
        
        logger.info(f"Pending emails requested by admin {current_user.email} (count: {len(response_emails)})")
        return response_emails
        
    except Exception as e:
        logger.error(f"Error getting pending emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pending emails"
        )


@router.get("/failed", response_model=List[FailedEmailSummary])
def get_failed_emails_endpoint(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get failed emails that have reached max retries.
    
    Returns list of emails that failed permanently.
    """
    try:
        failed_emails = get_failed_emails(db, limit=limit)
        
        # Convert to response format
        response_emails = []
        for email in failed_emails:
            response_emails.append(FailedEmailSummary(
                id=email.id,
                user_email=email.user_email,
                user_name=email.user_name,
                email_type=email.email_type,
                subject=email.subject,
                scheduled_time=email.scheduled_time,
                retry_count=email.retry_count,
                max_retries=email.max_retries,
                error_message=email.error_message,
                created_at=email.created_at,
                updated_at=email.updated_at
            ))
        
        logger.info(f"Failed emails requested by admin {current_user.email} (count: {len(response_emails)})")
        return response_emails
        
    except Exception as e:
        logger.error(f"Error getting failed emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get failed emails"
        )


@router.post("/retry/{email_id}")
def retry_failed_email_endpoint(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Retry a failed email.
    
    Resets the email status to pending and reschedules it.
    """
    try:
        success = retry_failed_email(db, email_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found or cannot be retried"
            )
        
        logger.info(f"Email {email_id} retry initiated by admin {current_user.email}")
        return {"message": f"Email {email_id} scheduled for retry", "success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying email {email_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry email"
        )


@router.get("/next-schedule", response_model=NextScheduleTimeResponse)
def get_next_schedule_time(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get information about the next available schedule time.
    
    Returns when the next email will be scheduled and queue position.
    """
    try:
        schedule_info = get_next_schedule_info(db)
        logger.info(f"Next schedule info requested by admin {current_user.email}")
        return schedule_info
        
    except Exception as e:
        logger.error(f"Error getting next schedule info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get schedule information"
        )


@router.get("/campaigns/status")
def get_campaign_status_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get status of all campaign emails.
    
    Returns information about each campaign's progress.
    """
    try:
        campaign_status = get_campaign_status(db)
        logger.info(f"Campaign status requested by admin {current_user.email}")
        return campaign_status
        
    except Exception as e:
        logger.error(f"Error getting campaign status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get campaign status"
        )


@router.post("/campaigns/add/{email_type}")
def add_campaign_for_all_users(
    email_type: EmailType,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Add a campaign email for all existing users.
    
    Useful for adding campaign emails to users who registered before the campaign was set up.
    """
    try:
        added_count = add_campaign_emails_for_all_users(db, email_type)
        
        logger.info(
            f"Campaign {email_type.value} added for all users by admin {current_user.email} "
            f"(added: {added_count})"
        )
        
        return {
            "message": f"Campaign {email_type.value} added for {added_count} users",
            "email_type": email_type.value,
            "added_count": added_count
        }
        
    except Exception as e:
        logger.error(f"Error adding campaign {email_type.value} for all users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add campaign emails"
        )


@router.get("/background-processor/status")
async def get_background_processor_status(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get status of the background email processor.

    Returns information about the background processor running state.
    """
    try:
        from app.services.background_email_processor import get_background_processor_status

        status = await get_background_processor_status()

        logger.info(f"Background processor status requested by admin {current_user.email}")
        return {
            "background_processor": status,
            "message": "Background processor status retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Error getting background processor status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get background processor status"
        )


@router.get("/health")
def email_queue_health_check():
    """
    Simple health check for the email queue system.

    Returns basic system status.
    """
    return {
        "status": "healthy",
        "system": "email_queue",
        "message": "Email queue API is operational"
    }
