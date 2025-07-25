#!/usr/bin/env python3
"""
Email Queue Monitor
==================

Simple monitoring script for the email queue system.
Provides command-line interface to check queue status and manage emails.

Usage:
    python email_queue_monitor.py status
    python email_queue_monitor.py pending [--limit N]
    python email_queue_monitor.py failed [--limit N]
    python email_queue_monitor.py retry <email_id>
    python email_queue_monitor.py campaigns
    python email_queue_monitor.py add-campaign <email_type>
"""

import sys
import os
import argparse
from datetime import datetime
from typing import List

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.email_queue import EmailQueue, EmailType, EmailStatus
from app.services.email_queue_service import (
    get_queue_stats, get_failed_emails, retry_failed_email,
    get_next_schedule_info, get_schedule_info_by_type, add_campaign_emails_for_all_users,
    get_campaign_status, get_pending_emails, get_pending_emails_by_type
)


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
        
        return SessionLocal
        
    except Exception as e:
        print(f"❌ Failed to setup database: {e}")
        sys.exit(1)


def print_queue_status(session_factory):
    """Print overall queue status with type-specific information."""
    with session_factory() as db:
        stats = get_queue_stats(db)
        schedule_info_by_type = get_schedule_info_by_type(db)

        print("📊 Email Queue Status")
        print("=" * 50)
        print(f"Total emails:     {stats.total_emails}")
        print(f"Pending:          {stats.pending_count}")
        print(f"Processing:       {stats.processing_count}")
        print(f"Sent:             {stats.sent_count}")
        print(f"Failed:           {stats.failed_count}")
        print(f"Cancelled:        {stats.cancelled_count}")
        print()
        print(f"Global next scheduled: {stats.next_scheduled or 'None'}")
        print(f"Global last sent:      {stats.last_sent or 'None'}")

        print("\n📧 Queue Status by Email Type:")
        print("-" * 50)

        for email_type, schedule_info in schedule_info_by_type.items():
            print(f"{email_type.upper()}:")
            print(f"  Next scheduled: {schedule_info.next_scheduled_time}")
            print(f"  Queue position: {schedule_info.queue_position}")
            print(f"  Delay (minutes): {schedule_info.estimated_delay_minutes}")
            print()

        # Show pending emails by type
        pending_by_type = get_pending_emails_by_type(db, limit_per_type=10)
        if pending_by_type:
            print("📋 Pending Emails by Type:")
            print("-" * 50)
            for email_type, emails in pending_by_type.items():
                print(f"{email_type.value}: {len(emails)} pending")
            print()


def print_pending_emails(session_factory, limit: int = 10):
    """Print pending emails."""
    with session_factory() as db:
        pending_emails = get_pending_emails(db, limit=limit)
        
        print(f"📧 Pending Emails (showing {len(pending_emails)} of max {limit})")
        print("=" * 80)
        
        if not pending_emails:
            print("No pending emails found.")
            return
        
        for email in pending_emails:
            print(f"ID: {email.id}")
            print(f"  Email: {email.user_email}")
            print(f"  Name: {email.user_name}")
            print(f"  Type: {email.email_type.value}")
            print(f"  Scheduled: {email.scheduled_time}")
            print(f"  Created: {email.created_at}")
            print(f"  Retries: {email.retry_count}/{email.max_retries}")
            print("-" * 40)


def print_failed_emails(session_factory, limit: int = 10):
    """Print failed emails."""
    with session_factory() as db:
        failed_emails = get_failed_emails(db, limit=limit)
        
        print(f"❌ Failed Emails (showing {len(failed_emails)} of max {limit})")
        print("=" * 80)
        
        if not failed_emails:
            print("No failed emails found.")
            return
        
        for email in failed_emails:
            print(f"ID: {email.id}")
            print(f"  Email: {email.user_email}")
            print(f"  Name: {email.user_name}")
            print(f"  Type: {email.email_type.value}")
            print(f"  Scheduled: {email.scheduled_time}")
            print(f"  Retries: {email.retry_count}/{email.max_retries}")
            print(f"  Error: {email.error_message}")
            print("-" * 40)


def retry_email(session_factory, email_id: int):
    """Retry a failed email."""
    with session_factory() as db:
        success = retry_failed_email(db, email_id)
        
        if success:
            print(f"✅ Email {email_id} scheduled for retry")
        else:
            print(f"❌ Failed to retry email {email_id} (not found or cannot be retried)")


def print_campaign_status(session_factory):
    """Print campaign status."""
    with session_factory() as db:
        campaign_status = get_campaign_status(db)
        
        print("🚀 Campaign Status")
        print("=" * 60)
        
        for campaign_type, status in campaign_status.items():
            print(f"\n{campaign_type.upper()}:")
            print(f"  Scheduled: {status['scheduled_time']}")
            print(f"  Past due: {'Yes' if status['is_past_due'] else 'No'}")
            print(f"  Pending: {status['pending_count']}")
            print(f"  Sent: {status['sent_count']}")
            print(f"  Failed: {status['failed_count']}")
            print(f"  Total: {status['total_count']}")


def add_campaign_for_all(session_factory, email_type_str: str):
    """Add campaign email for all users."""
    try:
        email_type = EmailType(email_type_str)
    except ValueError:
        print(f"❌ Invalid email type: {email_type_str}")
        print(f"Valid types: {', '.join([t.value for t in EmailType])}")
        return
    
    with session_factory() as db:
        added_count = add_campaign_emails_for_all_users(db, email_type)
        print(f"✅ Added {email_type.value} campaign for {added_count} users")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Email Queue Monitor')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    subparsers.add_parser('status', help='Show queue status')
    
    # Pending command
    pending_parser = subparsers.add_parser('pending', help='Show pending emails')
    pending_parser.add_argument('--limit', type=int, default=10, help='Number of emails to show')
    
    # Failed command
    failed_parser = subparsers.add_parser('failed', help='Show failed emails')
    failed_parser.add_argument('--limit', type=int, default=10, help='Number of emails to show')
    
    # Retry command
    retry_parser = subparsers.add_parser('retry', help='Retry a failed email')
    retry_parser.add_argument('email_id', type=int, help='Email ID to retry')
    
    # Campaigns command
    subparsers.add_parser('campaigns', help='Show campaign status')
    
    # Add campaign command
    add_campaign_parser = subparsers.add_parser('add-campaign', help='Add campaign for all users')
    add_campaign_parser.add_argument('email_type', help='Email type (welcome, search_engine, portfolio_builder, platform_complete)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup database
    session_factory = setup_database()
    
    try:
        if args.command == 'status':
            print_queue_status(session_factory)
        elif args.command == 'pending':
            print_pending_emails(session_factory, args.limit)
        elif args.command == 'failed':
            print_failed_emails(session_factory, args.limit)
        elif args.command == 'retry':
            retry_email(session_factory, args.email_id)
        elif args.command == 'campaigns':
            print_campaign_status(session_factory)
        elif args.command == 'add-campaign':
            add_campaign_for_all(session_factory, args.email_type)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
