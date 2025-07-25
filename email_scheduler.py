#!/usr/bin/env python3
"""
Email Campaign Scheduler
========================

Simple scheduler that runs email campaigns at scheduled times.
Run this script every hour via cron job or task scheduler.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.dependencies import get_db
from app.models.user import User
from app.services.email_campaign_service import EMAIL_TEMPLATES, send_scheduled_campaign_email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def should_send_campaign(campaign_type: str) -> bool:
    """Check if a campaign should be sent now."""
    template = EMAIL_TEMPLATES.get(campaign_type)
    if not template:
        return False
    
    schedule_time = template.get("schedule")
    if schedule_time == "instant":
        return False  # Instant emails are handled during signup
    
    current_time = datetime.now(schedule_time.tzinfo)
    
    # Send if current time is past the scheduled time
    # and within the last hour (to avoid sending multiple times)
    time_diff = (current_time - schedule_time).total_seconds()
    return 0 <= time_diff <= 3600  # Within the last hour

def send_scheduled_campaigns():
    """Send all scheduled campaigns that are due."""
    logger.info("🕐 Checking for scheduled email campaigns...")
    
    db = next(get_db())
    
    try:
        # Get all active non-admin users
        users = db.query(User).filter(
            User.is_active == True,
            User.is_admin == False
        ).all()
        
        logger.info(f"📧 Found {len(users)} active users")
        
        campaigns_sent = 0
        
        # Check each campaign type
        for campaign_type in EMAIL_TEMPLATES.keys():
            if campaign_type == "welcome":
                continue  # Skip welcome emails (handled during signup)
            
            if should_send_campaign(campaign_type):
                logger.info(f"📤 Sending '{campaign_type}' campaign...")
                
                success_count = 0
                failed_count = 0
                
                for user in users:
                    try:
                        if send_scheduled_campaign_email(campaign_type, user.email, user.name):
                            success_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send {campaign_type} to {user.email}: {e}")
                        failed_count += 1
                
                logger.info(f"✅ Campaign '{campaign_type}' completed: {success_count} sent, {failed_count} failed")
                campaigns_sent += 1
        
        if campaigns_sent == 0:
            logger.info("ℹ️  No campaigns scheduled for this time")
        
    except Exception as e:
        logger.error(f"❌ Error in scheduled campaigns: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    send_scheduled_campaigns()
