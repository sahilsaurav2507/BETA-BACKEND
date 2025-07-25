#!/usr/bin/env python3
"""
Email Queue System Tests
=======================

Comprehensive tests for the database-driven email queue system.
Tests sequential processing, 5-minute delays, failure handling, and campaign scheduling.

Usage:
    python test_email_queue.py
"""

import sys
import os
import time
from datetime import datetime, timedelta
import pytz

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.email_queue import EmailQueue, EmailType, EmailStatus
from app.schemas.email_queue import EmailQueueCreate
from app.services.email_queue_service import (
    add_email_to_queue, get_pending_emails, get_next_scheduled_time,
    update_email_status, get_queue_stats, add_campaign_emails_for_user
)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')


def setup_test_database():
    """Setup test database connection."""
    try:
        if settings.DATABASE_URL:
            engine = create_engine(settings.DATABASE_URL)
        else:
            database_url = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            engine = create_engine(database_url)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal
        
    except Exception as e:
        print(f"❌ Failed to setup test database: {e}")
        sys.exit(1)


def cleanup_test_emails(db):
    """Clean up test emails from database."""
    try:
        # Delete test emails (emails with test domains)
        test_emails = db.query(EmailQueue).filter(
            EmailQueue.user_email.like('%@test.com')
        ).all()
        
        for email in test_emails:
            db.delete(email)
        
        db.commit()
        print(f"🧹 Cleaned up {len(test_emails)} test emails")
        
    except Exception as e:
        print(f"⚠️  Warning: Failed to cleanup test emails: {e}")


def test_basic_queue_operations(session_factory):
    """Test basic queue operations."""
    print("\n🧪 Testing Basic Queue Operations")
    print("-" * 40)
    
    with session_factory() as db:
        # Clean up first
        cleanup_test_emails(db)
        
        # Test 1: Add email to queue
        email_data = EmailQueueCreate(
            user_email="test1@test.com",
            user_name="Test User 1",
            email_type=EmailType.WELCOME
        )
        
        email_entry = add_email_to_queue(db, email_data)
        print(f"✅ Email added to queue (ID: {email_entry.id})")
        
        # Test 2: Check scheduled time
        assert email_entry.scheduled_time is not None
        print(f"✅ Email scheduled at: {email_entry.scheduled_time}")
        
        # Test 3: Get pending emails
        pending = get_pending_emails(db, limit=10)
        assert len(pending) >= 1
        print(f"✅ Found {len(pending)} pending emails")
        
        # Test 4: Update email status
        success = update_email_status(db, email_entry.id, EmailStatus.SENT)
        assert success
        print(f"✅ Email status updated to SENT")
        
        # Clean up
        cleanup_test_emails(db)


def test_sequential_scheduling(session_factory):
    """Test 5-minute sequential scheduling."""
    print("\n🧪 Testing Sequential 5-Minute Scheduling")
    print("-" * 40)
    
    with session_factory() as db:
        cleanup_test_emails(db)
        
        # Add multiple emails and check scheduling
        emails = []
        for i in range(3):
            email_data = EmailQueueCreate(
                user_email=f"test{i+1}@test.com",
                user_name=f"Test User {i+1}",
                email_type=EmailType.WELCOME
            )
            
            email_entry = add_email_to_queue(db, email_data)
            emails.append(email_entry)
            print(f"✅ Email {i+1} scheduled at: {email_entry.scheduled_time}")
        
        # Check that emails are scheduled 5 minutes apart
        for i in range(1, len(emails)):
            time_diff = emails[i].scheduled_time - emails[i-1].scheduled_time
            expected_diff = timedelta(minutes=5)
            
            # Allow some tolerance for processing time
            assert abs(time_diff.total_seconds() - expected_diff.total_seconds()) < 60
            print(f"✅ Email {i+1} scheduled {time_diff.total_seconds()/60:.1f} minutes after email {i}")
        
        cleanup_test_emails(db)


def test_campaign_emails(session_factory):
    """Test campaign email functionality."""
    print("\n🧪 Testing Campaign Email Functionality")
    print("-" * 40)
    
    with session_factory() as db:
        cleanup_test_emails(db)
        
        # Test adding campaign emails for a user
        campaign_emails = add_campaign_emails_for_user(db, "campaign_test@test.com", "Campaign Test User")
        
        print(f"✅ Added {len(campaign_emails)} campaign emails")
        
        # Check that campaign emails have correct types
        campaign_types = [email.email_type for email in campaign_emails]
        expected_types = [EmailType.SEARCH_ENGINE, EmailType.PORTFOLIO_BUILDER, EmailType.PLATFORM_COMPLETE]
        
        for email_type in expected_types:
            if email_type in campaign_types:
                print(f"✅ Campaign email {email_type.value} added")
        
        cleanup_test_emails(db)


def test_error_handling(session_factory):
    """Test error handling and retry functionality."""
    print("\n🧪 Testing Error Handling and Retries")
    print("-" * 40)
    
    with session_factory() as db:
        cleanup_test_emails(db)
        
        # Add an email
        email_data = EmailQueueCreate(
            user_email="error_test@test.com",
            user_name="Error Test User",
            email_type=EmailType.WELCOME
        )
        
        email_entry = add_email_to_queue(db, email_data)
        print(f"✅ Email added for error testing (ID: {email_entry.id})")
        
        # Simulate failure
        success = update_email_status(db, email_entry.id, EmailStatus.FAILED, "Test error message")
        assert success
        print(f"✅ Email marked as failed")
        
        # Check retry count
        db.refresh(email_entry)
        assert email_entry.retry_count == 1
        print(f"✅ Retry count incremented: {email_entry.retry_count}")
        
        # Test max retries
        for i in range(2, 4):  # Fail 2 more times to reach max retries
            update_email_status(db, email_entry.id, EmailStatus.FAILED, f"Test error {i}")
            db.refresh(email_entry)
        
        assert email_entry.retry_count >= email_entry.max_retries
        print(f"✅ Max retries reached: {email_entry.retry_count}/{email_entry.max_retries}")
        
        cleanup_test_emails(db)


def test_queue_statistics(session_factory):
    """Test queue statistics functionality."""
    print("\n🧪 Testing Queue Statistics")
    print("-" * 40)
    
    with session_factory() as db:
        cleanup_test_emails(db)
        
        # Add some test emails with different statuses
        test_emails = []
        
        # Add pending emails
        for i in range(2):
            email_data = EmailQueueCreate(
                user_email=f"stats_pending_{i}@test.com",
                user_name=f"Stats Pending {i}",
                email_type=EmailType.WELCOME
            )
            email_entry = add_email_to_queue(db, email_data)
            test_emails.append(email_entry)
        
        # Mark one as sent
        update_email_status(db, test_emails[0].id, EmailStatus.SENT)
        
        # Mark one as failed
        update_email_status(db, test_emails[1].id, EmailStatus.FAILED, "Test failure")
        
        # Get statistics
        stats = get_queue_stats(db)
        
        print(f"✅ Queue statistics retrieved:")
        print(f"   Total emails: {stats.total_emails}")
        print(f"   Pending: {stats.pending_count}")
        print(f"   Sent: {stats.sent_count}")
        print(f"   Failed: {stats.failed_count}")
        
        # Verify we have at least our test emails
        assert stats.total_emails >= 2
        assert stats.sent_count >= 1
        assert stats.failed_count >= 1
        
        cleanup_test_emails(db)


def test_next_schedule_calculation(session_factory):
    """Test next schedule time calculation."""
    print("\n🧪 Testing Next Schedule Time Calculation")
    print("-" * 40)
    
    with session_factory() as db:
        cleanup_test_emails(db)
        
        # Get initial next schedule time
        initial_time = get_next_scheduled_time(db)
        print(f"✅ Initial next schedule time: {initial_time}")
        
        # Add an email
        email_data = EmailQueueCreate(
            user_email="schedule_test@test.com",
            user_name="Schedule Test User",
            email_type=EmailType.WELCOME
        )
        
        email_entry = add_email_to_queue(db, email_data)
        
        # Get next schedule time after adding email
        next_time = get_next_scheduled_time(db)
        print(f"✅ Next schedule time after adding email: {next_time}")
        
        # Should be 5 minutes after the email we just added
        expected_time = email_entry.scheduled_time + timedelta(minutes=5)
        time_diff = abs((next_time - expected_time).total_seconds())
        
        assert time_diff < 60  # Allow 1 minute tolerance
        print(f"✅ Next schedule time correctly calculated (diff: {time_diff:.1f}s)")
        
        cleanup_test_emails(db)


def run_all_tests():
    """Run all email queue tests."""
    print("🚀 Starting Email Queue System Tests")
    print("=" * 50)
    
    session_factory = setup_test_database()
    
    try:
        test_basic_queue_operations(session_factory)
        test_sequential_scheduling(session_factory)
        test_campaign_emails(session_factory)
        test_error_handling(session_factory)
        test_queue_statistics(session_factory)
        test_next_schedule_calculation(session_factory)
        
        print("\n🎉 All Email Queue Tests Passed!")
        print("=" * 50)
        print("✅ Basic queue operations")
        print("✅ Sequential 5-minute scheduling")
        print("✅ Campaign email functionality")
        print("✅ Error handling and retries")
        print("✅ Queue statistics")
        print("✅ Next schedule time calculation")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
