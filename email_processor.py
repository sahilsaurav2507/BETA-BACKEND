#!/usr/bin/env python3
"""
LawVriksh Email Queue Processor
==============================

Standalone script that processes the email queue with 5-minute intervals.
Replaces Redis/Celery with a pure database-driven approach.

Usage:
    python email_processor.py [--daemon] [--interval SECONDS] [--batch-size N]

Options:
    --daemon        Run as daemon (continuous processing)
    --interval      Check interval in seconds (default: 30)
    --batch-size    Number of emails to process per batch (default: 5)
    --dry-run       Don't actually send emails, just log what would be sent
    --verbose       Enable verbose logging
"""

import sys
import os
import time
import signal
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import pytz

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.email_queue import EmailQueue, EmailStatus, EmailType
from app.services.email_queue_service import (
    get_pending_emails, get_pending_emails_by_type, mark_email_processing, update_email_status
)
from app.services.email_service import send_email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('email_processor.log')
    ]
)
logger = logging.getLogger(__name__)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


def setup_database():
    """Setup database connection."""
    try:
        # Create database engine
        if settings.DATABASE_URL:
            engine = create_engine(settings.DATABASE_URL)
        else:
            database_url = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            engine = create_engine(database_url)
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        logger.info("Database connection established")
        return SessionLocal
        
    except Exception as e:
        logger.error(f"Failed to setup database: {e}")
        raise


def send_email_safely(email: EmailQueue, dry_run: bool = False) -> tuple[bool, Optional[str]]:
    """
    Send email with error handling.
    
    Args:
        email: Email queue entry
        dry_run: If True, don't actually send email
        
    Returns:
        tuple: (success, error_message)
    """
    try:
        if dry_run:
            logger.info(f"[DRY RUN] Would send {email.email_type.value} email to {email.user_email}")
            return True, None
        
        # Send the email
        send_email(email.user_email, email.subject, email.body)
        
        logger.info(f"Email sent successfully: {email.email_type.value} to {email.user_email}")
        return True, None
        
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        logger.error(f"Email send failed for {email.user_email}: {error_msg}")
        return False, error_msg


def process_email_batch_by_type(session_factory, batch_size: int = 100, dry_run: bool = False) -> dict:
    """
    Process ALL pending emails by type immediately - no more artificial delays.

    Welcome emails: Process immediately when due
    Campaign emails: Process ALL emails of same type when scheduled date arrives

    Args:
        session_factory: Database session factory
        batch_size: Maximum emails per type (increased for immediate processing)
        dry_run: If True, don't actually send emails

    Returns:
        dict: Number of emails processed per type
    """
    processed_counts = {}

    try:
        with session_factory() as db:
            # Get ALL pending emails by type for immediate processing
            pending_by_type = get_pending_emails_by_type(db, limit_per_type=batch_size)

            if not pending_by_type:
                return {}

            logger.info(f"Processing emails for {len(pending_by_type)} email types")

            # Process each email type independently
            for email_type, emails in pending_by_type.items():
                processed_count = 0

                logger.info(f"Processing {len(emails)} {email_type.value} emails")

                for email in emails:
                    try:
                        # Mark as processing to prevent duplicate sends
                        if not mark_email_processing(db, email.id):
                            logger.warning(f"Failed to mark email {email.id} as processing")
                            continue

                        # Send the email
                        success, error_message = send_email_safely(email, dry_run)

                        # Update status based on result
                        if success:
                            update_email_status(db, email.id, EmailStatus.sent)
                            processed_count += 1
                            logger.info(f"Sent {email_type.value} email to {email.user_email}")
                        else:
                            # Check if we should retry
                            if email.retry_count < email.max_retries:
                                # Reset to pending for retry (will be picked up in next cycle)
                                update_email_status(db, email.id, EmailStatus.pending, error_message)
                                logger.info(f"Email {email.id} will be retried (attempt {email.retry_count + 1}/{email.max_retries})")
                            else:
                                # Max retries reached, mark as failed
                                update_email_status(db, email.id, EmailStatus.failed, error_message)
                                logger.error(f"Email {email.id} failed permanently after {email.max_retries} retries")

                        # Check for shutdown
                        if shutdown_requested:
                            logger.info("Shutdown requested, stopping processing")
                            break

                    except Exception as e:
                        logger.error(f"Error processing email {email.id}: {e}")
                        try:
                            update_email_status(db, email.id, EmailStatus.failed, str(e))
                        except:
                            pass  # Don't fail if we can't update status

                processed_counts[email_type.value] = processed_count

                # Check for shutdown between types
                if shutdown_requested:
                    logger.info("Shutdown requested, stopping type processing")
                    break

            return processed_counts

    except Exception as e:
        logger.error(f"Error in process_email_batch_by_type: {e}")
        return processed_counts


def process_email_batch(session_factory, batch_size: int = 5, dry_run: bool = False) -> int:
    """
    Process emails using type-based processing - no more blocking between types.

    Args:
        session_factory: Database session factory
        batch_size: Number of emails to process per type
        dry_run: If True, don't actually send emails

    Returns:
        int: Total number of emails processed across all types
    """
    try:
        # Use the new type-based processing
        processed_by_type = process_email_batch_by_type(session_factory, batch_size, dry_run)

        total_processed = sum(processed_by_type.values())

        if total_processed > 0:
            logger.info(f"Processed {total_processed} emails across {len(processed_by_type)} types")
            for email_type, count in processed_by_type.items():
                logger.info(f"  {email_type}: {count} emails")

        return total_processed

    except Exception as e:
        logger.error(f"Error in process_email_batch: {e}")
        return 0


def run_daemon(session_factory, check_interval: int = 30, batch_size: int = 5, dry_run: bool = False):
    """
    Run email processor as daemon.
    
    Args:
        session_factory: Database session factory
        check_interval: Seconds between queue checks
        batch_size: Number of emails to process per batch
        dry_run: If True, don't actually send emails
    """
    logger.info(f"Starting email processor daemon (check_interval={check_interval}s, batch_size={batch_size})")
    
    if dry_run:
        logger.info("DRY RUN MODE: No emails will actually be sent")
    
    last_activity = datetime.now()
    
    while not shutdown_requested:
        try:
            start_time = datetime.now()
            processed = process_email_batch(session_factory, batch_size, dry_run)
            
            if processed > 0:
                last_activity = start_time
                logger.info(f"Processed {processed} emails in {(datetime.now() - start_time).total_seconds():.1f}s")
            else:
                # Log periodic status when idle
                if (datetime.now() - last_activity).total_seconds() > 300:  # 5 minutes
                    logger.info("Email processor is running, no pending emails")
                    last_activity = datetime.now()
            
            # Wait for next check
            for _ in range(check_interval):
                if shutdown_requested:
                    break
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in daemon loop: {e}")
            time.sleep(check_interval)
    
    logger.info("Email processor daemon stopped")


def run_single_batch(session_factory, batch_size: int = 5, dry_run: bool = False):
    """
    Run a single batch of email processing.
    
    Args:
        session_factory: Database session factory
        batch_size: Number of emails to process
        dry_run: If True, don't actually send emails
    """
    logger.info(f"Running single batch processing (batch_size={batch_size})")
    
    if dry_run:
        logger.info("DRY RUN MODE: No emails will actually be sent")
    
    start_time = datetime.now()
    processed = process_email_batch(session_factory, batch_size, dry_run)
    duration = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"Single batch completed: {processed} emails processed in {duration:.1f}s")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='LawVriksh Email Queue Processor')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
    parser.add_argument('--batch-size', type=int, default=5, help='Emails per batch')
    parser.add_argument('--dry-run', action='store_true', help='Don\'t actually send emails')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Setup database
        session_factory = setup_database()
        
        # Run processor
        if args.daemon:
            run_daemon(session_factory, args.interval, args.batch_size, args.dry_run)
        else:
            run_single_batch(session_factory, args.batch_size, args.dry_run)
            
    except Exception as e:
        logger.error(f"Email processor failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
