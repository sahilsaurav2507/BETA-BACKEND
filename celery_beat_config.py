"""
Celery Beat Configuration for LawVriksh Email Campaigns
======================================================

This configuration sets up automatic scheduling for LawVriksh email campaigns.

Campaign Schedule:
- Mail 1: Welcome (Instant - on signup)
- Mail 2: Search Engine Complete (July 26, 2025, 2:00 PM IST)
- Mail 3: Portfolio Builder Complete (July 30, 2025, 10:30 AM IST)  
- Mail 4: Platform Complete & Launch (August 3, 2025, 9:00 AM IST)

Usage:
    celery -A celery_beat_config beat --loglevel=info
"""

from celery import Celery
from celery.schedules import crontab
from datetime import datetime
import pytz
from app.core.config import settings

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Create Celery app
celery_app = Celery(
    "lawvriksh_campaigns",
    broker=settings.RABBITMQ_URL,
    backend=settings.RABBITMQ_URL
)

# Import tasks
from app.tasks.email_tasks import (
    send_bulk_campaign_task,
    process_due_campaigns_task
)

# Celery Beat Schedule
celery_app.conf.beat_schedule = {
    # Check for due campaigns every hour
    'check-due-campaigns': {
        'task': 'app.tasks.email_tasks.process_due_campaigns_task',
        'schedule': crontab(minute=0),  # Every hour at minute 0
        'options': {'queue': 'campaigns'}
    },
    
    # Specific campaign schedules (as backup to the hourly check)
    
    # Mail 2: Search Engine Complete - July 26, 2025, 2:00 PM IST
    'search-engine-campaign': {
        'task': 'app.tasks.email_tasks.send_bulk_campaign_task',
        'schedule': crontab(
            minute=0,
            hour=14,  # 2:00 PM
            day_of_month=26,
            month_of_year=7,
            year=2025
        ),
        'args': ('search_engine',),
        'options': {'queue': 'campaigns'}
    },
    
    # Mail 3: Portfolio Builder Complete - July 30, 2025, 10:30 AM IST
    'portfolio-builder-campaign': {
        'task': 'app.tasks.email_tasks.send_bulk_campaign_task',
        'schedule': crontab(
            minute=30,
            hour=10,  # 10:30 AM
            day_of_month=30,
            month_of_year=7,
            year=2025
        ),
        'args': ('portfolio_builder',),
        'options': {'queue': 'campaigns'}
    },
    
    # Mail 4: Platform Complete & Launch - August 3, 2025, 9:00 AM IST
    'platform-complete-campaign': {
        'task': 'app.tasks.email_tasks.send_bulk_campaign_task',
        'schedule': crontab(
            minute=0,
            hour=9,  # 9:00 AM
            day_of_month=3,
            month_of_year=8,
            year=2025
        ),
        'args': ('platform_complete',),
        'options': {'queue': 'campaigns'}
    },
    
    # Daily health check for campaign system
    'campaign-system-health-check': {
        'task': 'app.tasks.email_tasks.process_due_campaigns_task',
        'schedule': crontab(minute=0, hour=11),  # Daily at 11:00 AM IST
        'options': {'queue': 'campaigns'}
    }
}

# Celery configuration
celery_app.conf.update(
    timezone='Asia/Kolkata',
    enable_utc=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_routes={
        'app.tasks.email_tasks.*': {'queue': 'campaigns'},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

if __name__ == '__main__':
    celery_app.start()
