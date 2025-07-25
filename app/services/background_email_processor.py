"""
Background Email Processor Service
==================================

This service runs continuously in the background to process emails from the queue.
It integrates with FastAPI's lifespan events to start/stop automatically.

Features:
- Runs every 60 seconds to check for pending emails
- Processes ALL due emails immediately (no artificial delays)
- Welcome emails: Sent within 1-2 minutes of registration
- Campaign emails: ALL users with same date processed together
- Automatic startup/shutdown with FastAPI
- Graceful error handling and logging
- Production-ready background task
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
import pytz

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.email_queue_service import get_pending_emails_by_type
from app.models.email_queue import EmailType

# Configure logging
logger = logging.getLogger(__name__)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Global variables for background task management
background_task: Optional[asyncio.Task] = None
should_stop = False


def setup_database():
    """Setup database connection for background processing."""
    try:
        if settings.DATABASE_URL:
            engine = create_engine(settings.DATABASE_URL)
        else:
            database_url = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            engine = create_engine(database_url)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal
        
    except Exception as e:
        logger.error(f"Failed to setup database for background email processor: {e}")
        return None


async def process_pending_emails():
    """Process pending emails that are due for sending."""
    try:
        session_factory = setup_database()
        if not session_factory:
            logger.error("Database setup failed, skipping email processing")
            return 0
        
        # Import here to avoid circular imports
        from email_processor import process_email_batch_by_type
        
        # Process ALL due emails immediately (no artificial limits)
        processed_counts = process_email_batch_by_type(
            session_factory,
            batch_size=100,  # Process up to 100 emails per type per cycle
            dry_run=False
        )
        
        total_processed = sum(processed_counts.values())
        
        if total_processed > 0:
            logger.info(f"Background processor: Processed {total_processed} emails")
            for email_type, count in processed_counts.items():
                if count > 0:
                    logger.info(f"  {email_type}: {count} emails")
        
        return total_processed
        
    except Exception as e:
        logger.error(f"Error in background email processing: {e}")
        return 0


async def check_queue_status():
    """Check queue status and log summary."""
    try:
        session_factory = setup_database()
        if not session_factory:
            return
        
        with session_factory() as db:
            pending_by_type = get_pending_emails_by_type(db, limit_per_type=1)
            
            if pending_by_type:
                current_time = datetime.now(IST)
                ready_count = 0
                
                for email_type, emails in pending_by_type.items():
                    for email in emails:
                        scheduled_time = email.scheduled_time
                        if scheduled_time.tzinfo is None:
                            scheduled_time = IST.localize(scheduled_time)
                        
                        if scheduled_time <= current_time:
                            ready_count += 1
                
                if ready_count > 0:
                    logger.info(f"Background processor: {ready_count} emails ready for processing")
                
    except Exception as e:
        logger.error(f"Error checking queue status: {e}")


async def background_email_processor():
    """Main background email processor loop."""
    global should_stop
    
    logger.info("🚀 Background email processor started")
    logger.info("📧 Will check for pending emails every 60 seconds")
    
    iteration = 0
    
    while not should_stop:
        try:
            iteration += 1
            
            # Process pending emails
            processed_count = await process_pending_emails()
            
            # Log status every 10 iterations (10 minutes) if no emails processed
            if iteration % 10 == 0 and processed_count == 0:
                await check_queue_status()
                logger.info("Background email processor: Running normally (no emails due)")
            
            # Wait for 60 seconds before next check
            for _ in range(60):  # 60 seconds = 60 iterations of 1 second
                if should_stop:
                    break
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("Background email processor cancelled")
            break
        except Exception as e:
            logger.error(f"Unexpected error in background email processor: {e}")
            # Wait a bit before retrying to avoid rapid error loops
            await asyncio.sleep(30)
    
    logger.info("🛑 Background email processor stopped")


async def start_background_email_processor():
    """Start the background email processor."""
    global background_task, should_stop
    
    if background_task is not None:
        logger.warning("Background email processor already running")
        return
    
    should_stop = False
    background_task = asyncio.create_task(background_email_processor())
    logger.info("✅ Background email processor task created")


async def stop_background_email_processor():
    """Stop the background email processor."""
    global background_task, should_stop
    
    if background_task is None:
        logger.info("Background email processor not running")
        return
    
    logger.info("🛑 Stopping background email processor...")
    should_stop = True
    
    # Cancel the task
    background_task.cancel()
    
    try:
        # Wait for the task to complete
        await asyncio.wait_for(background_task, timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("Background email processor did not stop within timeout")
    except asyncio.CancelledError:
        logger.info("Background email processor cancelled successfully")
    
    background_task = None
    logger.info("✅ Background email processor stopped")


def is_background_processor_running() -> bool:
    """Check if the background email processor is running."""
    global background_task
    return background_task is not None and not background_task.done()


async def get_background_processor_status() -> dict:
    """Get status information about the background processor."""
    global background_task
    
    if background_task is None:
        return {
            "running": False,
            "status": "Not started",
            "uptime": None
        }
    
    if background_task.done():
        return {
            "running": False,
            "status": "Stopped",
            "uptime": None
        }
    
    return {
        "running": True,
        "status": "Running",
        "uptime": "Active"
    }
