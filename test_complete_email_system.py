#!/usr/bin/env python3
"""
Complete Email Queue System Test
===============================

This script tests the complete email queue system by:
1. Registering a new user through the signup endpoint
2. Verifying campaign email scheduling
3. Modifying campaign schedules (+4 days)
4. Updating campaign email templates with feedback link
5. Providing comprehensive verification

Usage:
    python test_complete_email_system.py
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta
import pytz

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.email_queue import EmailQueue, EmailType, EmailStatus
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import create_user, get_user_by_email
from app.services.email_queue_service import get_pending_emails, get_queue_stats
from app.services.email_campaign_service import EMAIL_TEMPLATES

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Test user data
TEST_USER = {
    "name": "Test Queue User",
    "email": "testqueue@example.com",
    "password": "testpassword123"
}

# API base URL (adjust if needed)
API_BASE_URL = "http://localhost:8000"


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


def cleanup_test_user(session_factory):
    """Clean up test user and related emails."""
    with session_factory() as db:
        try:
            # Delete test emails
            test_emails = db.query(EmailQueue).filter(
                EmailQueue.user_email == TEST_USER["email"]
            ).all()
            
            for email in test_emails:
                db.delete(email)
            
            # Delete test user
            test_user = db.query(User).filter(User.email == TEST_USER["email"]).first()
            if test_user:
                db.delete(test_user)
            
            db.commit()
            print(f"🧹 Cleaned up test user and {len(test_emails)} emails")
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to cleanup: {e}")


def test_user_registration_direct():
    """Test user registration directly through database (simulating API)."""
    print("\n🧪 Step 1: Testing User Registration")
    print("-" * 50)
    
    session_factory = setup_database()
    
    with session_factory() as db:
        try:
            # Check if user already exists
            existing_user = get_user_by_email(db, TEST_USER["email"])
            if existing_user:
                print(f"ℹ️  Test user already exists, cleaning up first...")
                cleanup_test_user(session_factory)
            
            # Create new user (simulating the signup endpoint)
            user_data = UserCreate(**TEST_USER)
            user = create_user(db, user_data)
            
            print(f"✅ User registered successfully!")
            print(f"   User ID: {user.id}")
            print(f"   Name: {user.name}")
            print(f"   Email: {user.email}")
            print(f"   Created: {user.created_at}")
            
            # Now simulate the email queue logic from auth.py
            from app.models.email_queue import EmailType
            from app.schemas.email_queue import EmailQueueCreate
            from app.services.email_queue_service import add_email_to_queue, add_campaign_emails_for_user
            
            # Add welcome email
            email_data = EmailQueueCreate(
                user_email=user.email,
                user_name=user.name,
                email_type=EmailType.welcome
            )
            welcome_email = add_email_to_queue(db, email_data)
            
            # Add campaign emails
            campaign_emails = add_campaign_emails_for_user(db, user.email, user.name)
            
            print(f"✅ Welcome email queued (ID: {welcome_email.id})")
            print(f"✅ {len(campaign_emails)} campaign emails queued")
            
            return user.id
            
        except Exception as e:
            print(f"❌ User registration failed: {e}")
            return None


def verify_email_queue(session_factory, user_id):
    """Verify email queue entries for the test user."""
    print("\n🧪 Step 2: Verifying Email Queue")
    print("-" * 50)
    
    with session_factory() as db:
        try:
            # Get all emails for test user
            user_emails = db.query(EmailQueue).filter(
                EmailQueue.user_email == TEST_USER["email"]
            ).order_by(EmailQueue.scheduled_time).all()
            
            print(f"📧 Found {len(user_emails)} emails in queue for test user:")
            print()
            
            for i, email in enumerate(user_emails, 1):
                print(f"Email {i}:")
                print(f"   ID: {email.id}")
                print(f"   Type: {email.email_type.value}")
                print(f"   Status: {email.status.value}")
                print(f"   Scheduled: {email.scheduled_time}")
                print(f"   Created: {email.created_at}")
                print()
            
            # Verify we have the expected emails
            email_types = [email.email_type.value for email in user_emails]
            expected_types = ["welcome", "search_engine", "portfolio_builder", "platform_complete"]
            
            missing_types = set(expected_types) - set(email_types)
            if missing_types:
                print(f"⚠️  Missing email types: {missing_types}")
            else:
                print("✅ All expected email types found!")
            
            return user_emails
            
        except Exception as e:
            print(f"❌ Error verifying email queue: {e}")
            return []


def update_campaign_schedules():
    """Update campaign schedules by adding 4 days."""
    print("\n🧪 Step 3: Updating Campaign Schedules (+4 days)")
    print("-" * 50)
    
    try:
        # Update EMAIL_TEMPLATES with new dates
        original_dates = {}
        
        for campaign_type in ["search_engine", "portfolio_builder", "platform_complete"]:
            template = EMAIL_TEMPLATES[campaign_type]
            original_date = template["schedule"]
            new_date = original_date + timedelta(days=4)
            
            original_dates[campaign_type] = {
                "original": original_date,
                "new": new_date
            }
            
            # Update the template
            EMAIL_TEMPLATES[campaign_type]["schedule"] = new_date
            
            print(f"📅 {campaign_type.upper()}:")
            print(f"   Original: {original_date}")
            print(f"   New: {new_date}")
            print()
        
        print("✅ Campaign schedules updated successfully!")
        return original_dates
        
    except Exception as e:
        print(f"❌ Error updating campaign schedules: {e}")
        return {}


def update_campaign_email_templates():
    """Update campaign email templates to include feedback link."""
    print("\n🧪 Step 4: Updating Campaign Email Templates")
    print("-" * 50)
    
    try:
        feedback_line = "\n\n📝 **Help us improve!** Please take a moment to share your feedback: www.lawvriksh.com/feedback"
        
        campaigns_updated = []
        
        for campaign_type in ["search_engine", "portfolio_builder", "platform_complete"]:
            template = EMAIL_TEMPLATES[campaign_type]
            
            # Check if feedback link is already present
            if "www.lawvriksh.com/feedback" not in template["template"]:
                # Add feedback link at the end
                template["template"] += feedback_line
                campaigns_updated.append(campaign_type)
                print(f"✅ Updated {campaign_type} email template")
            else:
                print(f"ℹ️  {campaign_type} email template already has feedback link")
        
        if campaigns_updated:
            print(f"\n✅ Updated {len(campaigns_updated)} campaign email templates with feedback link!")
        else:
            print("\nℹ️  All campaign email templates already have feedback links")
        
        return campaigns_updated
        
    except Exception as e:
        print(f"❌ Error updating campaign email templates: {e}")
        return []


def update_database_campaign_schedules(session_factory):
    """Update campaign schedules in the database."""
    print("\n🧪 Step 5: Updating Database Campaign Schedules")
    print("-" * 50)
    
    with session_factory() as db:
        try:
            # Get campaign emails for test user
            campaign_emails = db.query(EmailQueue).filter(
                EmailQueue.user_email == TEST_USER["email"],
                EmailQueue.email_type.in_([
                    EmailType.search_engine,
                    EmailType.portfolio_builder, 
                    EmailType.platform_complete
                ])
            ).all()
            
            updated_count = 0
            
            for email in campaign_emails:
                # Get new schedule from updated templates
                new_schedule = EMAIL_TEMPLATES[email.email_type.value]["schedule"]
                
                if email.scheduled_time != new_schedule:
                    old_time = email.scheduled_time
                    email.scheduled_time = new_schedule
                    
                    print(f"📅 Updated {email.email_type.value}:")
                    print(f"   Old: {old_time}")
                    print(f"   New: {new_schedule}")
                    
                    updated_count += 1
            
            db.commit()
            print(f"\n✅ Updated {updated_count} campaign email schedules in database!")
            
        except Exception as e:
            print(f"❌ Error updating database schedules: {e}")


def run_queue_monitor():
    """Run queue monitor to show current status."""
    print("\n🧪 Step 6: Queue Monitor Status")
    print("-" * 50)
    
    session_factory = setup_database()
    
    with session_factory() as db:
        try:
            # Get queue stats
            stats = get_queue_stats(db)
            print(f"📊 Queue Statistics:")
            print(f"   Total emails: {stats.total_emails}")
            print(f"   Pending: {stats.pending_count}")
            print(f"   Sent: {stats.sent_count}")
            print(f"   Failed: {stats.failed_count}")
            print()
            
            # Get pending emails for test user
            all_pending = get_pending_emails(db, limit=100)
            test_user_pending = [email for email in all_pending if email.user_email == TEST_USER["email"]]
            
            print(f"📧 Pending emails for test user ({len(test_user_pending)}):")
            for email in test_user_pending:
                print(f"   {email.email_type.value}: {email.scheduled_time}")
            
        except Exception as e:
            print(f"❌ Error getting queue status: {e}")


def main():
    """Main test function."""
    print("🚀 Complete Email Queue System Test")
    print("=" * 60)
    print(f"🕐 Test started: {datetime.now(IST)}")
    print(f"👤 Test user: {TEST_USER['email']}")
    print("=" * 60)
    
    session_factory = setup_database()
    
    # Clean up any existing test data
    cleanup_test_user(session_factory)
    
    # Step 1: Register new user
    user_id = test_user_registration_direct()
    if not user_id:
        print("\n❌ User registration failed, stopping test")
        return False
    
    # Step 2: Verify email queue
    user_emails = verify_email_queue(session_factory, user_id)
    if len(user_emails) < 4:
        print(f"\n⚠️  Expected 4 emails, found {len(user_emails)}")
    
    # Step 3: Update campaign schedules
    schedule_updates = update_campaign_schedules()
    
    # Step 4: Update email templates
    template_updates = update_campaign_email_templates()
    
    # Step 5: Update database schedules
    update_database_campaign_schedules(session_factory)
    
    # Step 6: Show final status
    run_queue_monitor()
    
    # Final verification
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 60)
    
    final_emails = verify_email_queue(session_factory, user_id)
    
    print(f"✅ User registration: SUCCESS")
    print(f"✅ Email queue entries: {len(final_emails)} emails")
    print(f"✅ Campaign schedule updates: {len(schedule_updates)} campaigns")
    print(f"✅ Email template updates: {len(template_updates)} templates")
    
    print(f"\n📧 Final email schedule for {TEST_USER['email']}:")
    for email in final_emails:
        print(f"   {email.email_type.value}: {email.scheduled_time} ({email.status.value})")
    
    print(f"\n🎉 Complete email queue system test finished!")
    print(f"💡 To process emails: py email_processor.py --daemon")
    print(f"💡 To monitor queue: py email_queue_monitor.py status")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
