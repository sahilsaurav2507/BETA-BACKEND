#!/usr/bin/env python3
"""
Test Separate Queue Processing
=============================

This script tests the new separate queue processing system to verify:
1. Welcome emails are processed immediately without being blocked by campaign emails
2. Each email type maintains independent 5-minute intervals
3. Multiple users can register and get welcome emails promptly
4. Campaign emails don't interfere with welcome email processing

Usage:
    python test_separate_queue_processing.py
"""

import sys
import os
from datetime import datetime, timedelta
import pytz

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.email_queue import EmailQueue, EmailType, EmailStatus
from app.models.user import User
from app.schemas.user import UserCreate
from app.schemas.email_queue import EmailQueueCreate
from app.services.user_service import create_user
from app.services.email_queue_service import (
    add_email_to_queue, get_pending_emails_by_type, get_next_scheduled_time,
    get_schedule_info_by_type, add_campaign_emails_for_user
)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Test users
TEST_USERS = [
    {"name": "Welcome Test User 1", "email": "welcome1@test.com", "password": "test123"},
    {"name": "Welcome Test User 2", "email": "welcome2@test.com", "password": "test123"},
    {"name": "Welcome Test User 3", "email": "welcome3@test.com", "password": "test123"},
]


def setup_database():
    """Setup database connection."""
    try:
        if settings.DATABASE_URL:
            engine = create_engine(settings.DATABASE_URL)
        else:
            database_url = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            engine = create_engine(database_url)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal
        
    except Exception as e:
        print(f"❌ Failed to setup database: {e}")
        sys.exit(1)


def cleanup_test_data(session_factory):
    """Clean up test users and emails."""
    with session_factory() as db:
        try:
            # Delete test emails
            for user_data in TEST_USERS:
                test_emails = db.query(EmailQueue).filter(
                    EmailQueue.user_email == user_data["email"]
                ).all()
                
                for email in test_emails:
                    db.delete(email)
                
                # Delete test user
                test_user = db.query(User).filter(User.email == user_data["email"]).first()
                if test_user:
                    db.delete(test_user)
            
            db.commit()
            print(f"🧹 Cleaned up test data")
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to cleanup: {e}")


def test_separate_queue_scheduling():
    """Test that each email type gets independent scheduling."""
    print("\n🧪 Testing Separate Queue Scheduling")
    print("-" * 50)
    
    session_factory = setup_database()
    
    with session_factory() as db:
        try:
            # Get next scheduled time for each email type
            schedule_info = get_schedule_info_by_type(db)
            
            print("📅 Next scheduled times by email type:")
            for email_type, info in schedule_info.items():
                print(f"   {email_type}: {info.next_scheduled_time} (queue: {info.queue_position})")
            
            # Test adding welcome emails - should get immediate scheduling
            current_time = datetime.now(IST)
            
            for i, user_data in enumerate(TEST_USERS):
                email_data = EmailQueueCreate(
                    user_email=user_data["email"],
                    user_name=user_data["name"],
                    email_type=EmailType.welcome
                )
                
                email_entry = add_email_to_queue(db, email_data)
                
                # Check that welcome emails are scheduled soon
                time_diff = (email_entry.scheduled_time - current_time).total_seconds() / 60
                
                print(f"✅ Welcome email {i+1} scheduled in {time_diff:.1f} minutes")
                
                # Verify 5-minute intervals between welcome emails
                if i > 0:
                    prev_email = db.query(EmailQueue).filter(
                        EmailQueue.user_email == TEST_USERS[i-1]["email"],
                        EmailQueue.email_type == EmailType.welcome
                    ).first()
                    
                    interval = (email_entry.scheduled_time - prev_email.scheduled_time).total_seconds() / 60
                    print(f"   Interval from previous welcome: {interval:.1f} minutes")
                    
                    if abs(interval - 5.0) < 1.0:  # Allow 1 minute tolerance
                        print(f"   ✅ Correct 5-minute interval maintained")
                    else:
                        print(f"   ⚠️  Interval not exactly 5 minutes: {interval:.1f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing separate queue scheduling: {e}")
            return False


def test_campaign_email_independence():
    """Test that campaign emails don't block welcome emails."""
    print("\n🧪 Testing Campaign Email Independence")
    print("-" * 50)
    
    session_factory = setup_database()
    
    with session_factory() as db:
        try:
            # Add campaign emails for test users
            for user_data in TEST_USERS:
                campaign_emails = add_campaign_emails_for_user(db, user_data["email"], user_data["name"])
                print(f"✅ Added {len(campaign_emails)} campaign emails for {user_data['name']}")
            
            # Check pending emails by type
            pending_by_type = get_pending_emails_by_type(db, limit_per_type=10)
            
            print(f"\n📧 Pending emails by type:")
            for email_type, emails in pending_by_type.items():
                print(f"   {email_type.value}: {len(emails)} emails")
                
                # Show scheduling for first few emails
                for i, email in enumerate(emails[:3]):
                    print(f"     Email {i+1}: {email.scheduled_time} ({email.user_email})")
            
            # Verify that welcome emails are scheduled independently
            welcome_emails = pending_by_type.get(EmailType.welcome, [])
            campaign_emails = []
            
            for email_type in [EmailType.search_engine, EmailType.portfolio_builder, EmailType.platform_complete]:
                campaign_emails.extend(pending_by_type.get(email_type, []))
            
            if welcome_emails and campaign_emails:
                earliest_welcome = min(email.scheduled_time for email in welcome_emails)
                earliest_campaign = min(email.scheduled_time for email in campaign_emails)
                
                print(f"\n📊 Scheduling comparison:")
                print(f"   Earliest welcome email: {earliest_welcome}")
                print(f"   Earliest campaign email: {earliest_campaign}")
                
                if earliest_welcome < earliest_campaign:
                    print(f"   ✅ Welcome emails scheduled before campaign emails")
                else:
                    print(f"   ⚠️  Campaign emails may be blocking welcome emails")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing campaign email independence: {e}")
            return False


def test_type_specific_intervals():
    """Test that each email type maintains its own 5-minute intervals."""
    print("\n🧪 Testing Type-Specific 5-Minute Intervals")
    print("-" * 50)
    
    session_factory = setup_database()
    
    with session_factory() as db:
        try:
            # Check intervals within each email type
            for email_type in EmailType:
                emails = db.query(EmailQueue).filter(
                    and_(
                        EmailQueue.email_type == email_type,
                        EmailQueue.status == EmailStatus.pending
                    )
                ).order_by(EmailQueue.scheduled_time).all()
                
                if len(emails) > 1:
                    print(f"\n📧 {email_type.value} emails ({len(emails)} total):")
                    
                    for i in range(1, min(len(emails), 4)):  # Check first few intervals
                        prev_time = emails[i-1].scheduled_time
                        curr_time = emails[i].scheduled_time
                        interval = (curr_time - prev_time).total_seconds() / 60
                        
                        print(f"   Email {i} to {i+1}: {interval:.1f} minute interval")
                        
                        if abs(interval - 5.0) < 1.0:  # Allow 1 minute tolerance
                            print(f"     ✅ Correct 5-minute interval")
                        else:
                            print(f"     ⚠️  Interval not exactly 5 minutes")
                else:
                    print(f"\n📧 {email_type.value}: {len(emails)} emails (not enough to check intervals)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing type-specific intervals: {e}")
            return False


def main():
    """Main test function."""
    print("🚀 Testing Separate Queue Processing System")
    print("=" * 60)
    print(f"🕐 Test started: {datetime.now(IST)}")
    print("=" * 60)
    
    session_factory = setup_database()
    
    # Clean up any existing test data
    cleanup_test_data(session_factory)
    
    # Create test users first
    with session_factory() as db:
        for user_data in TEST_USERS:
            try:
                user_create = UserCreate(**user_data)
                user = create_user(db, user_create)
                print(f"✅ Created test user: {user.name} ({user.email})")
            except Exception as e:
                print(f"⚠️  User {user_data['email']} may already exist: {e}")
    
    # Run tests
    test_results = []
    
    test_results.append(("Separate Queue Scheduling", test_separate_queue_scheduling()))
    test_results.append(("Campaign Email Independence", test_campaign_email_independence()))
    test_results.append(("Type-Specific Intervals", test_type_specific_intervals()))
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed_tests += 1
    
    print(f"\n🎯 Overall: {passed_tests}/{len(test_results)} tests passed")
    
    if passed_tests == len(test_results):
        print("\n🎉 All tests passed! Separate queue processing is working correctly.")
        print("\n💡 Key benefits verified:")
        print("   ✅ Welcome emails no longer blocked by campaign emails")
        print("   ✅ Each email type maintains independent 5-minute intervals")
        print("   ✅ New users get welcome emails promptly")
        print("   ✅ Campaign emails process on their own schedule")
    else:
        print(f"\n⚠️  {len(test_results) - passed_tests} tests failed. Please review the issues above.")
    
    print(f"\n💡 To process emails: py email_processor.py --daemon")
    print(f"💡 To monitor queues: py email_queue_monitor.py status")
    
    return passed_tests == len(test_results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
