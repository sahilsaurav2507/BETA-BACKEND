import logging
from celery import Celery
from app.services.email_service import send_welcome_email, send_bulk_email
from app.core.config import settings

# Configure Celery with Redis (fallback to RabbitMQ if Redis not available)
try:
    # Try Redis first
    celery_app = Celery(
        "lawvriksh_tasks",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND
    )
    logging.info("Celery configured with Redis broker")
except Exception as e:
    # Fallback to RabbitMQ
    celery_app = Celery(
        "lawvriksh_tasks",
        broker=settings.RABBITMQ_URL,
        backend='rpc://'
    )
    logging.warning(f"Redis not available, using RabbitMQ fallback: {e}")

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

@celery_app.task(bind=True, max_retries=3)
def send_welcome_email_task(self, user_email: str, user_name: str):
    """Send a welcome email to a new user asynchronously."""
    try:
        send_welcome_email(user_email, user_name)
        return {"status": "success", "email": user_email}
    except Exception as exc:
        logging.error(f"Failed to send welcome email to {user_email}: {exc}")
        self.retry(countdown=60, exc=exc)

@celery_app.task
def update_user_points_task(user_id: int, platform: str):
    """Update user points after a share event."""
    from app.services.share_service import calculate_and_update_points
    return calculate_and_update_points(user_id, platform)

@celery_app.task
def send_bulk_email_task(emails: list, subject: str, body: str):
    """Send a bulk email to a list of users asynchronously."""
    try:
        send_bulk_email(emails, subject, body)
        return {"status": "success", "sent": len(emails)}
    except Exception as exc:
        logging.error(f"Failed to send bulk email to {len(emails)} users: {exc}")
        raise

@celery_app.task(bind=True, max_retries=3)
def send_campaign_email_task(self, campaign_type: str, user_email: str, user_name: str):
    """Send a campaign email to a specific user."""
    try:
        from app.services.email_campaign_service import send_scheduled_campaign_email
        result = send_scheduled_campaign_email(campaign_type, user_email, user_name)
        return {"status": "success" if result else "failed", "email": user_email, "campaign": campaign_type}
    except Exception as exc:
        logging.error(f"Failed to send campaign email '{campaign_type}' to {user_email}: {exc}")
        self.retry(countdown=60, exc=exc)

@celery_app.task
def send_bulk_campaign_task(campaign_type: str):
    """Send campaign email to all active users."""
    try:
        from app.services.email_campaign_service import send_bulk_campaign_email
        from app.core.dependencies import get_db

        db = next(get_db())
        try:
            success_count, failed_count = send_bulk_campaign_email(campaign_type, db)
            return {
                "campaign_type": campaign_type,
                "success_count": success_count,
                "failed_count": failed_count,
                "total_sent": success_count + failed_count,
                "status": "completed"
            }
        finally:
            db.close()
    except Exception as exc:
        logging.error(f"Failed to send bulk campaign '{campaign_type}': {exc}")
        raise

@celery_app.task(bind=True, max_retries=3)
def send_future_campaigns_to_new_user_task(self, user_email: str, user_name: str):
    """Send only future campaigns to a new user (no backdated emails)."""
    try:
        from app.services.email_campaign_service import send_future_campaigns_to_new_user
        result = send_future_campaigns_to_new_user(user_email, user_name)
        return {
            "status": "success" if result else "partial_failure",
            "user_email": user_email,
            "user_name": user_name
        }
    except Exception as exc:
        logging.error(f"Failed to send future campaigns to new user {user_email}: {exc}")
        self.retry(countdown=60, exc=exc)

@celery_app.task(bind=True, max_retries=3)
def send_delayed_welcome_email_task(self, user_email: str, user_name: str):
    """Send welcome email with a 5-minute delay to eliminate blocking delays."""
    try:
        from app.services.email_campaign_service import send_welcome_email_campaign

        # Send the welcome email
        send_welcome_email_campaign(user_email, user_name)

        logging.info(f"5-minute delayed welcome email sent successfully to {user_email} ({user_name})")
        return {"status": "success", "email": user_email, "name": user_name}
    except Exception as exc:
        logging.error(f"Failed to send delayed welcome email to {user_email}: {exc}")
        self.retry(countdown=60, exc=exc)

@celery_app.task(bind=True, max_retries=3)
def send_5_minute_welcome_email_task(self, user_email: str, user_name: str):
    """Send welcome email exactly 5 minutes after registration."""
    try:
        from app.services.email_campaign_service import send_welcome_email_campaign

        # Log the scheduled send time
        logging.info(f"Executing 5-minute welcome email for {user_email} ({user_name})")

        # Send the welcome email
        send_welcome_email_campaign(user_email, user_name)

        logging.info(f"5-minute scheduled welcome email sent successfully to {user_email} ({user_name})")
        return {"status": "success", "email": user_email, "name": user_name, "delay": "5_minutes"}
    except Exception as exc:
        logging.error(f"Failed to send 5-minute welcome email to {user_email}: {exc}")
        self.retry(countdown=60, exc=exc)

@celery_app.task
def process_due_campaigns_task():
    """Process all campaigns that are due to be sent (excludes past campaigns)."""
    try:
        from app.services.email_campaign_service import get_due_campaigns

        due_campaigns = get_due_campaigns()
        results = []

        for campaign_type in due_campaigns:
            result = send_bulk_campaign_task.delay(campaign_type)
            results.append({
                "campaign_type": campaign_type,
                "task_id": result.id,
                "status": "queued"
            })

        return {
            "due_campaigns": len(due_campaigns),
            "campaigns_queued": results,
            "processed_at": str(logging.datetime.now())
        }
    except Exception as exc:
        logging.error(f"Failed to process due campaigns: {exc}")
        raise