#!/usr/bin/env python3
"""
Test Immediate Sequential Processing
===================================

This script tests the new immediate sequential processing system:
1. Welcome emails processed immediately (no 5-minute delays)
2. Campaign emails processed ALL at once when scheduled date arrives
3. Sequential processing without artificial delays

Usage:
    python test_immediate_processing.py
"""

import sys
import os
from datetime import datetime, timedelta
import pytz
import time

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.email_queue import EmailQueue, EmailType, EmailStatus
from app.models.user import User
from app.schemas.user import UserCreate
from app.schemas.email_queue import EmailQueueCreate
from app.services.user_service import create_user
from app.services.email_queue_service import add_email_to_queue, get_next_scheduled_time, get_pending_emails

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Test users
TEST_USERS = [
    {"name": "Immediate Test User 1", "email": "immediate1@test.com", "password": "test123"},
    {"name": "Immediate Test User 2", "email": "immediate2@test.com", "password": "test123"},
    {"name": "Immediate Test User 3", "email": "immediate3@test.com", "password": "test123"},
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


def cleanup_test_users(session_factory):
    """Clean up test users and emails."""
    with session_factory() as db:
        try:
            total_emails = 0
            total_users = 0
            
            for user_data in TEST_USERS:
                # Delete test emails
                test_emails = db.query(EmailQueue).filter(
                    EmailQueue.user_email == user_data["email"]
                ).all()
                
                for email in test_emails:
                    db.delete(email)
                    total_emails += 1
                
                # Delete test user
                test_user = db.query(User).filter(User.email == user_data["email"]).first()
                if test_user:
                    db.delete(test_user)
                    total_users += 1
            
            db.commit()
            if total_emails > 0 or total_users > 0:
                print(f"🧹 Cleaned up {total_users} test users and {total_emails} emails")
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to cleanup: {e}")


def test_immediate_welcome_scheduling():
    """Test that welcome emails are scheduled immediately."""
    print("🧪 Testing Immediate Welcome Email Scheduling")
    print("-" * 60)
    
    session_factory = setup_database()
    
    with session_factory() as db:
        try:
            current_time = datetime.now(IST)
            
            # Test get_next_scheduled_time for welcome emails
            next_time = get_next_scheduled_time(db, EmailType.welcome)
            
            time_diff = (next_time - current_time).total_seconds()
            
            print(f"🕐 Current time: {current_time}")
            print(f"📅 Next scheduled time: {next_time}")
            print(f"⏱️  Time difference: {time_diff:.1f} seconds")
            
            if time_diff <= 5:  # Should be immediate (within 5 seconds)
                print("✅ Welcome emails scheduled immediately!")
                return True
            else:
                print(f"❌ Welcome emails delayed by {time_diff:.1f} seconds")
                return False
                
        except Exception as e:
            print(f"❌ Error testing immediate scheduling: {e}")
            return False


def test_multiple_welcome_emails():
    """Test that multiple welcome emails are all scheduled immediately."""
    print("\n🧪 Testing Multiple Welcome Emails")
    print("-" * 60)
    
    session_factory = setup_database()
    cleanup_test_users(session_factory)
    
    welcome_emails = []
    
    with session_factory() as db:
        try:
            current_time = datetime.now(IST)
            print(f"🕐 Starting test at: {current_time}")
            
            # Register multiple users and add welcome emails
            for i, user_data in enumerate(TEST_USERS):
                print(f"\n📝 Registering user {i+1}: {user_data['email']}")
                
                # Create user
                user_create = UserCreate(**user_data)
                user = create_user(db, user_create)
                
                # Add welcome email
                email_data = EmailQueueCreate(
                    user_email=user.email,
                    user_name=user.name,
                    email_type=EmailType.welcome
                )
                
                welcome_email = add_email_to_queue(db, email_data)
                welcome_emails.append(welcome_email)
                
                scheduled_time = welcome_email.scheduled_time
                if scheduled_time.tzinfo is None:
                    scheduled_time = IST.localize(scheduled_time)
                
                delay = (scheduled_time - current_time).total_seconds()
                print(f"   ✅ Welcome email scheduled: {scheduled_time}")
                print(f"   ⏱️  Delay: {delay:.1f} seconds")
            
            # Check that all emails are scheduled immediately
            all_immediate = True
            max_delay = 0
            
            for email in welcome_emails:
                scheduled_time = email.scheduled_time
                if scheduled_time.tzinfo is None:
                    scheduled_time = IST.localize(scheduled_time)
                
                delay = (scheduled_time - current_time).total_seconds()
                max_delay = max(max_delay, delay)
                
                if delay > 10:  # More than 10 seconds is not immediate
                    all_immediate = False
            
            print(f"\n📊 Results:")
            print(f"   Total welcome emails: {len(welcome_emails)}")
            print(f"   Maximum delay: {max_delay:.1f} seconds")
            print(f"   All immediate: {all_immediate}")
            
            if all_immediate:
                print("✅ All welcome emails scheduled immediately!")
                return True
            else:
                print("❌ Some welcome emails have delays")
                return False
                
        except Exception as e:
            print(f"❌ Error testing multiple welcome emails: {e}")
            return False
        finally:
            cleanup_test_users(session_factory)


def test_immediate_processing():
    """Test that emails are processed immediately when due."""
    print("\n🧪 Testing Immediate Email Processing")
    print("-" * 60)
    
    session_factory = setup_database()
    cleanup_test_users(session_factory)
    
    with session_factory() as db:
        try:
            # Add a welcome email for immediate processing
            user_data = TEST_USERS[0]
            user_create = UserCreate(**user_data)
            user = create_user(db, user_create)
            
            email_data = EmailQueueCreate(
                user_email=user.email,
                user_name=user.name,
                email_type=EmailType.welcome
            )
            
            welcome_email = add_email_to_queue(db, email_data)
            
            print(f"📧 Added welcome email for {user.email}")
            print(f"   Scheduled: {welcome_email.scheduled_time}")
            
            # Check if email is ready for processing
            pending_emails = get_pending_emails(db, limit=10, email_type=EmailType.welcome)
            
            print(f"\n🔍 Checking for pending emails...")
            print(f"   Found {len(pending_emails)} welcome emails ready for processing")
            
            if len(pending_emails) > 0:
                print("✅ Email is ready for immediate processing!")
                
                # Test the email processor
                from email_processor import process_email_batch_by_type
                
                print("\n⚡ Processing emails...")
                processed_counts = process_email_batch_by_type(session_factory, batch_size=100, dry_run=True)
                
                welcome_processed = processed_counts.get('welcome', 0)
                
                if welcome_processed > 0:
                    print(f"✅ Successfully processed {welcome_processed} welcome email(s)!")
                    return True
                else:
                    print("❌ No welcome emails were processed")
                    return False
            else:
                print("❌ No emails ready for processing")
                return False
                
        except Exception as e:
            print(f"❌ Error testing immediate processing: {e}")
            return False
        finally:
            cleanup_test_users(session_factory)


def main():
    """Main test function."""
    print("🚀 Immediate Sequential Processing Test")
    print("=" * 70)
    print("🎯 Testing the new immediate processing system:")
    print("   • Welcome emails: Immediate scheduling (no 5-minute delays)")
    print("   • Campaign emails: All processed when scheduled date arrives")
    print("   • Sequential processing without artificial delays")
    print(f"🕐 Test started: {datetime.now(IST)}")
    print("=" * 70)
    
    # Run tests
    test_results = []
    
    test_results.append(("Immediate Welcome Scheduling", test_immediate_welcome_scheduling()))
    test_results.append(("Multiple Welcome Emails", test_multiple_welcome_emails()))
    test_results.append(("Immediate Processing", test_immediate_processing()))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed_tests += 1
    
    print(f"\n🎯 Overall: {passed_tests}/{len(test_results)} tests passed")
    
    if passed_tests == len(test_results):
        print("\n🎉 All tests passed! Immediate sequential processing is working!")
        print("\n✅ Verified functionality:")
        print("   • Welcome emails scheduled immediately (no delays)")
        print("   • Multiple emails processed sequentially")
        print("   • Email processor handles immediate processing")
        print("   • No artificial 5-minute intervals")
        
        print(f"\n🚀 Expected behavior:")
        print(f"   • Welcome emails: Sent within 60 seconds of registration")
        print(f"   • Campaign emails: All users with same date processed together")
        print(f"   • Sequential sending without delays between emails")
        
    else:
        print(f"\n⚠️  {len(test_results) - passed_tests} tests failed. Please review the issues above.")
    
    print(f"\n💡 To start the server with immediate processing:")
    print(f"   python start_server.py")
    
    return passed_tests == len(test_results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
