"""
Email Queue Service
==================

Database-driven email queue service that replaces Redis/Celery.
Implements sequential 5-minute email processing with proper error handling.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import logging
import pytz

from app.models.email_queue import EmailQueue, EmailType, EmailStatus
from app.schemas.email_queue import (
    EmailQueueCreate, EmailQueueUpdate, EmailQueueResponse,
    EmailQueueStats, EmailProcessingResult, NextScheduleTimeResponse
)
from app.services.email_campaign_service import EMAIL_TEMPLATES

logger = logging.getLogger(__name__)

# IST timezone for consistent scheduling
IST = pytz.timezone('Asia/Kolkata')


def get_next_scheduled_time(db: Session, email_type: Optional[EmailType] = None) -> datetime:
    """
    Calculate the next available scheduled time for immediate processing.
    No more 5-minute intervals - emails are scheduled for immediate processing.

    Args:
        db: Database session
        email_type: Specific email type (used for logging, but all emails scheduled immediately)

    Returns:
        datetime: Current time for immediate processing
    """
    try:
        current_time = datetime.now(IST)

        # All emails are now scheduled for immediate processing
        # The background processor will handle them in the next cycle (within 60 seconds)
        return current_time

    except Exception as e:
        logger.error(f"Error calculating next scheduled time for {email_type}: {e}")
        return datetime.now(IST)


def add_email_to_queue(
    db: Session, 
    email_data: EmailQueueCreate,
    auto_schedule: bool = True
) -> EmailQueue:
    """
    Add an email to the queue with automatic scheduling.
    
    Args:
        db: Database session
        email_data: Email queue creation data
        auto_schedule: Whether to auto-calculate scheduled_time
        
    Returns:
        EmailQueue: Created email queue entry
    """
    try:
        # Calculate scheduled time if not provided - use type-specific scheduling
        if auto_schedule and email_data.scheduled_time is None:
            scheduled_time = get_next_scheduled_time(db, email_data.email_type)
        else:
            scheduled_time = email_data.scheduled_time or datetime.now(IST)
        
        # Get email template if subject/body not provided
        subject = email_data.subject
        body = email_data.body
        
        if not subject or not body:
            template = EMAIL_TEMPLATES.get(email_data.email_type.value)
            if template:
                subject = subject or template["subject"]
                body = body or template["template"].format(name=email_data.user_name)
        
        # Create email queue entry
        email_queue = EmailQueue(
            user_email=email_data.user_email,
            user_name=email_data.user_name,
            email_type=email_data.email_type,
            subject=subject,
            body=body,
            scheduled_time=scheduled_time,
            max_retries=email_data.max_retries,
            status=EmailStatus.pending
        )
        
        db.add(email_queue)
        db.commit()
        db.refresh(email_queue)
        
        logger.info(
            f"Email queued: {email_data.email_type.value} for {email_data.user_email} "
            f"scheduled at {scheduled_time}"
        )
        
        return email_queue
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding email to queue: {e}")
        raise


def get_pending_emails(db: Session, limit: int = 100, email_type: Optional[EmailType] = None) -> List[EmailQueue]:
    """
    Get pending emails ready to be sent, optionally filtered by email type.
    Now processes ALL due emails immediately without artificial limits.

    Args:
        db: Database session
        limit: Maximum number of emails to retrieve (increased default for immediate processing)
        email_type: Optional email type filter

    Returns:
        List[EmailQueue]: List of pending emails ready for immediate processing
    """
    try:
        current_time = datetime.now(IST)

        # Get all pending emails first
        query = db.query(EmailQueue).filter(EmailQueue.status == EmailStatus.pending)

        # Add email type filter if specified
        if email_type is not None:
            query = query.filter(EmailQueue.email_type == email_type)

        all_pending = query.order_by(
            EmailQueue.created_at.asc(),
            EmailQueue.id.asc()
        ).limit(limit).all()

        # Filter by scheduled time, handling timezone issues
        ready_emails = []
        for email in all_pending:
            scheduled_time = email.scheduled_time

            # Handle timezone-naive scheduled times
            if scheduled_time.tzinfo is None:
                scheduled_time = IST.localize(scheduled_time)

            # Check if email is due
            if scheduled_time <= current_time:
                ready_emails.append(email)

        return ready_emails

    except Exception as e:
        logger.error(f"Error getting pending emails for type {email_type}: {e}")
        return []


def get_pending_emails_by_type(db: Session, limit_per_type: int = 100) -> dict:
    """
    Get pending emails for each email type separately for immediate processing.
    Processes ALL due emails without artificial limits.

    Args:
        db: Database session
        limit_per_type: Maximum number of emails per type (increased for immediate processing)

    Returns:
        dict: Dictionary with email_type as key and list of emails as value
    """
    try:
        result = {}
        current_time = datetime.now(IST)

        for email_type in EmailType:
            # Get all pending emails of this type that are due
            pending_emails = get_pending_emails(db, limit_per_type, email_type)

            if pending_emails:
                # Log how many emails are being processed for this type
                logger.info(f"Found {len(pending_emails)} {email_type.value} emails ready for immediate processing")
                result[email_type] = pending_emails

        return result

    except Exception as e:
        logger.error(f"Error getting pending emails by type: {e}")
        return {}


def update_email_status(
    db: Session,
    email_id: int,
    status: EmailStatus,
    error_message: Optional[str] = None
) -> bool:
    """
    Update email status in the queue.
    
    Args:
        db: Database session
        email_id: Email queue ID
        status: New status
        error_message: Error message if failed
        
    Returns:
        bool: True if updated successfully
    """
    try:
        email = db.query(EmailQueue).filter(EmailQueue.id == email_id).first()
        if not email:
            logger.error(f"Email with ID {email_id} not found")
            return False
        
        # Update status
        email.status = status
        email.error_message = error_message
        
        # Set sent_at if email was sent successfully
        if status == EmailStatus.sent:
            email.sent_at = datetime.now(IST)

        # Increment retry count if failed
        if status == EmailStatus.failed:
            email.retry_count += 1
        
        db.commit()
        
        logger.info(f"Email {email_id} status updated to {status.value}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating email status: {e}")
        return False


def mark_email_processing(db: Session, email_id: int) -> bool:
    """
    Mark email as processing to prevent duplicate sends.
    
    Args:
        db: Database session
        email_id: Email queue ID
        
    Returns:
        bool: True if marked successfully
    """
    return update_email_status(db, email_id, EmailStatus.processing)


def get_queue_stats(db: Session) -> EmailQueueStats:
    """
    Get email queue statistics.
    
    Args:
        db: Database session
        
    Returns:
        EmailQueueStats: Queue statistics
    """
    try:
        # Count emails by status
        stats_query = db.query(
            EmailQueue.status,
            func.count(EmailQueue.id).label('count')
        ).group_by(EmailQueue.status).all()
        
        stats_dict = {status.value: count for status, count in stats_query}
        
        # Get next scheduled and last sent
        next_scheduled = db.query(func.min(EmailQueue.scheduled_time)).filter(
            EmailQueue.status == EmailStatus.pending
        ).scalar()

        last_sent = db.query(func.max(EmailQueue.sent_at)).filter(
            EmailQueue.status == EmailStatus.sent
        ).scalar()
        
        total_emails = sum(stats_dict.values())
        
        return EmailQueueStats(
            total_emails=total_emails,
            pending_count=stats_dict.get('pending', 0),
            processing_count=stats_dict.get('processing', 0),
            sent_count=stats_dict.get('sent', 0),
            failed_count=stats_dict.get('failed', 0),
            cancelled_count=stats_dict.get('cancelled', 0),
            next_scheduled=next_scheduled,
            last_sent=last_sent
        )
        
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        return EmailQueueStats(
            total_emails=0, pending_count=0, processing_count=0,
            sent_count=0, failed_count=0, cancelled_count=0,
            next_scheduled=None, last_sent=None
        )


def get_failed_emails(db: Session, limit: int = 50) -> List[EmailQueue]:
    """
    Get failed emails that have reached max retries.
    
    Args:
        db: Database session
        limit: Maximum number of emails to retrieve
        
    Returns:
        List[EmailQueue]: List of failed emails
    """
    try:
        failed_emails = db.query(EmailQueue).filter(
            and_(
                EmailQueue.status == EmailStatus.failed,
                EmailQueue.retry_count >= EmailQueue.max_retries
            )
        ).order_by(desc(EmailQueue.created_at)).limit(limit).all()
        
        return failed_emails
        
    except Exception as e:
        logger.error(f"Error getting failed emails: {e}")
        return []


def retry_failed_email(db: Session, email_id: int) -> bool:
    """
    Retry a failed email by resetting its status and rescheduling.
    
    Args:
        db: Database session
        email_id: Email queue ID
        
    Returns:
        bool: True if retry was successful
    """
    try:
        email = db.query(EmailQueue).filter(EmailQueue.id == email_id).first()
        if not email:
            return False
        
        if email.status != EmailStatus.failed:
            logger.warning(f"Email {email_id} is not in failed status")
            return False

        # Reset status and reschedule
        email.status = EmailStatus.pending
        email.scheduled_time = get_next_scheduled_time(db)
        email.error_message = None
        
        db.commit()
        
        logger.info(f"Email {email_id} scheduled for retry at {email.scheduled_time}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error retrying failed email: {e}")
        return False


def get_next_schedule_info(db: Session, email_type: Optional[EmailType] = None) -> NextScheduleTimeResponse:
    """
    Get information about the next available schedule time for a specific email type.

    Args:
        db: Database session
        email_type: Email type to get schedule info for (if None, uses global)

    Returns:
        NextScheduleTimeResponse: Next schedule information
    """
    try:
        next_time = get_next_scheduled_time(db, email_type)

        # Count pending emails for this type
        if email_type is not None:
            queue_position = db.query(func.count(EmailQueue.id)).filter(
                and_(
                    EmailQueue.email_type == email_type,
                    EmailQueue.status.in_([EmailStatus.pending, EmailStatus.processing])
                )
            ).scalar() or 0
        else:
            queue_position = db.query(func.count(EmailQueue.id)).filter(
                EmailQueue.status.in_([EmailStatus.pending, EmailStatus.processing])
            ).scalar() or 0

        # Calculate estimated delay
        current_time = datetime.now(IST)
        delay_minutes = max(0, int((next_time - current_time).total_seconds() / 60))

        return NextScheduleTimeResponse(
            next_scheduled_time=next_time,
            queue_position=queue_position + 1,
            estimated_delay_minutes=delay_minutes
        )

    except Exception as e:
        logger.error(f"Error getting next schedule info for {email_type}: {e}")
        return NextScheduleTimeResponse(
            next_scheduled_time=datetime.now(IST),
            queue_position=1,
            estimated_delay_minutes=0
        )


def get_schedule_info_by_type(db: Session) -> dict:
    """
    Get schedule information for each email type.

    Args:
        db: Database session

    Returns:
        dict: Schedule information for each email type
    """
    try:
        result = {}

        for email_type in EmailType:
            result[email_type.value] = get_next_schedule_info(db, email_type)

        return result

    except Exception as e:
        logger.error(f"Error getting schedule info by type: {e}")
        return {}


def add_campaign_emails_for_user(db: Session, user_email: str, user_name: str) -> List[EmailQueue]:
    """
    Add all future campaign emails for a new user.

    Args:
        db: Database session
        user_email: User's email address
        user_name: User's name

    Returns:
        List[EmailQueue]: List of created campaign email entries
    """
    try:
        campaign_emails = []
        current_time = datetime.now(IST)

        # Campaign schedule from EMAIL_TEMPLATES
        campaign_schedules = {
            EmailType.search_engine: EMAIL_TEMPLATES["search_engine"]["schedule"],
            EmailType.portfolio_builder: EMAIL_TEMPLATES["portfolio_builder"]["schedule"],
            EmailType.platform_complete: EMAIL_TEMPLATES["platform_complete"]["schedule"]
        }

        for email_type, scheduled_time in campaign_schedules.items():
            # Only add campaigns that are in the future
            if scheduled_time != "instant" and scheduled_time > current_time:
                email_data = EmailQueueCreate(
                    user_email=user_email,
                    user_name=user_name,
                    email_type=email_type
                )

                # Use the specific scheduled time for campaigns (not auto-calculated)
                email_queue_entry = add_email_to_queue(db, email_data, auto_schedule=False)
                email_queue_entry.scheduled_time = scheduled_time
                db.commit()

                campaign_emails.append(email_queue_entry)

                logger.info(
                    f"Campaign email {email_type.value} queued for {user_email} "
                    f"at {scheduled_time}"
                )

        return campaign_emails

    except Exception as e:
        db.rollback()
        logger.error(f"Error adding campaign emails for user {user_email}: {e}")
        return []


def add_campaign_emails_for_all_users(db: Session, email_type: EmailType) -> int:
    """
    Add a specific campaign email for all existing users.

    Args:
        db: Database session
        email_type: Type of campaign email to add

    Returns:
        int: Number of emails added
    """
    try:
        from app.models.user import User

        # Get campaign schedule
        template = EMAIL_TEMPLATES.get(email_type.value)
        if not template or template["schedule"] == "instant":
            logger.warning(f"Invalid campaign type or schedule: {email_type.value}")
            return 0

        scheduled_time = template["schedule"]
        current_time = datetime.now(IST)

        # Only add if campaign is in the future
        if scheduled_time <= current_time:
            logger.warning(f"Campaign {email_type.value} is not in the future, skipping")
            return 0

        # Get all active users
        users = db.query(User).filter(User.is_active == True).all()

        added_count = 0
        for user in users:
            try:
                # Check if user already has this campaign email queued
                existing = db.query(EmailQueue).filter(
                    and_(
                        EmailQueue.user_email == user.email,
                        EmailQueue.email_type == email_type,
                        EmailQueue.status.in_([EmailStatus.pending, EmailStatus.processing])
                    )
                ).first()

                if existing:
                    logger.debug(f"Campaign {email_type.value} already queued for {user.email}")
                    continue

                # Add campaign email
                email_data = EmailQueueCreate(
                    user_email=user.email,
                    user_name=user.name,
                    email_type=email_type
                )

                email_queue_entry = add_email_to_queue(db, email_data, auto_schedule=False)
                email_queue_entry.scheduled_time = scheduled_time
                db.commit()

                added_count += 1

            except Exception as e:
                logger.error(f"Error adding campaign email for user {user.email}: {e}")
                continue

        logger.info(f"Added {added_count} campaign emails of type {email_type.value}")
        return added_count

    except Exception as e:
        logger.error(f"Error adding campaign emails for all users: {e}")
        return 0


def get_campaign_status(db: Session) -> dict:
    """
    Get status of all campaign emails.

    Args:
        db: Database session

    Returns:
        dict: Campaign status information
    """
    try:
        campaign_status = {}
        current_time = datetime.now(IST)

        for email_type in [EmailType.search_engine, EmailType.portfolio_builder, EmailType.platform_complete]:
            template = EMAIL_TEMPLATES.get(email_type.value)
            if not template:
                continue

            scheduled_time = template["schedule"]

            # Count emails by status for this campaign
            status_counts = db.query(
                EmailQueue.status,
                func.count(EmailQueue.id).label('count')
            ).filter(
                EmailQueue.email_type == email_type
            ).group_by(EmailQueue.status).all()

            status_dict = {status.value: count for status, count in status_counts}

            campaign_status[email_type.value] = {
                "scheduled_time": scheduled_time,
                "is_past_due": scheduled_time != "instant" and scheduled_time < current_time,
                "pending_count": status_dict.get('pending', 0),
                "sent_count": status_dict.get('sent', 0),
                "failed_count": status_dict.get('failed', 0),
                "total_count": sum(status_dict.values())
            }

        return campaign_status

    except Exception as e:
        logger.error(f"Error getting campaign status: {e}")
        return {}
