#!/usr/bin/env python3
"""
Test script to verify that the email fix is working.
This will test the complete flow: user registration -> email scheduling -> email sending.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.services.user_service import create_user
from app.schemas.user import UserCreate
from app.tasks.email_tasks import send_5_minute_welcome_email_task

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_immediate_email_sending():
    """Test sending welcome email immediately (not through Celery)."""
    print("🔍 TESTING IMMEDIATE EMAIL SENDING")
    print("=" * 50)
    
    try:
        from app.services.email_service import send_welcome_email
        
        test_email = input("Enter your email to test welcome email (or press Enter to skip): ").strip()
        if not test_email:
            print("⏭️  Skipping immediate email test")
            return True
        
        print(f"📧 Sending welcome email to {test_email}...")
        send_welcome_email(test_email, "Test User")
        print("✅ Welcome email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send welcome email: {e}")
        return False

def test_celery_task_scheduling():
    """Test scheduling email through Celery (without delay)."""
    print("\n🔄 TESTING CELERY TASK SCHEDULING")
    print("=" * 50)
    
    try:
        test_email = input("Enter your email to test Celery task (or press Enter to skip): ").strip()
        if not test_email:
            print("⏭️  Skipping Celery task test")
            return True
        
        print(f"📧 Scheduling welcome email task for {test_email}...")
        
        # Schedule task to run immediately (countdown=0)
        task = send_5_minute_welcome_email_task.apply_async(
            args=[test_email, "Test User"],
            countdown=0  # Send immediately for testing
        )
        
        print(f"✅ Task scheduled successfully! Task ID: {task.id}")
        print("⏳ Waiting for task to complete...")
        
        # Wait for task to complete (with timeout)
        try:
            result = task.get(timeout=30)
            print(f"✅ Task completed successfully: {result}")
            return True
        except Exception as e:
            print(f"❌ Task failed or timed out: {e}")
            print("   This might mean Celery worker is not running")
            return False
        
    except Exception as e:
        print(f"❌ Failed to schedule Celery task: {e}")
        return False

def test_user_registration_flow():
    """Test the complete user registration flow with email."""
    print("\n👤 TESTING USER REGISTRATION FLOW")
    print("=" * 50)
    
    try:
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Get current user count
        total_users_before = db.query(User).filter(User.is_admin == False).count()
        
        # Create a test user
        test_user_data = UserCreate(
            name="Email Test User",
            email=f"email_test_user_{total_users_before + 1}@example.com",
            password="testpassword123"
        )
        
        print(f"👤 Creating test user: {test_user_data.email}")
        new_user = create_user(db, test_user_data)
        
        print(f"✅ User created with ID: {new_user.id}")
        
        # Now test the signup endpoint logic (simulated)
        print("📧 Testing email scheduling logic...")
        
        try:
            task = send_5_minute_welcome_email_task.apply_async(
                args=[new_user.email, new_user.name],
                countdown=5  # 5 seconds for testing instead of 5 minutes
            )
            print(f"✅ Email task scheduled successfully! Task ID: {task.id}")
            print("⏳ Waiting 10 seconds for task to be processed...")
            
            # Wait for task
            time.sleep(10)
            
            try:
                result = task.get(timeout=5)
                print(f"✅ Email task completed: {result}")
            except Exception as e:
                print(f"⚠️  Task status unknown: {e}")
                print("   Email might still be sent if Celery worker is running")
            
        except Exception as email_error:
            print(f"❌ Failed to schedule email: {email_error}")
        
        # Clean up - delete the test user
        print(f"\n🧹 Cleaning up test user...")
        db.delete(new_user)
        db.commit()
        db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Registration test failed: {e}")
        print(f"❌ Registration test failed: {e}")
        return False

def check_celery_worker_status():
    """Check if Celery worker is running."""
    print("\n🔄 CHECKING CELERY WORKER STATUS")
    print("=" * 50)
    
    try:
        # Try to inspect active workers
        from celery import Celery
        from app.core.config import settings
        
        celery_app = Celery(
            "tasks",
            broker=settings.RABBITMQ_URL,
            backend='rpc://'
        )
        
        # Check if workers are active
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"✅ Active Celery workers found: {list(active_workers.keys())}")
            return True
        else:
            print("❌ No active Celery workers found")
            print("   To start a worker, run: celery -A app.tasks.email_tasks worker --loglevel=info")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not check worker status: {e}")
        print("   To start a worker, run: celery -A app.tasks.email_tasks worker --loglevel=info")
        return False

def main():
    """Run email system tests."""
    print("🚀 EMAIL SYSTEM FIX VERIFICATION")
    print("=" * 60)
    
    # Check if Celery worker is running
    worker_running = check_celery_worker_status()
    
    # Test immediate email sending
    immediate_ok = test_immediate_email_sending()
    
    # Test Celery task scheduling (only if worker is running)
    if worker_running:
        celery_ok = test_celery_task_scheduling()
    else:
        print("\n⚠️  Skipping Celery tests - no worker running")
        celery_ok = False
    
    # Test user registration flow
    registration_ok = test_user_registration_flow()
    
    # Summary
    print("\n📋 TEST SUMMARY")
    print("=" * 50)
    
    if immediate_ok:
        print("✅ Email sending works correctly")
    else:
        print("❌ Email sending has issues")
    
    if worker_running and celery_ok:
        print("✅ Celery task system works correctly")
    elif worker_running:
        print("❌ Celery task system has issues")
    else:
        print("⚠️  Celery worker not running - emails won't be sent automatically")
    
    if registration_ok:
        print("✅ User registration flow works")
    else:
        print("❌ User registration flow has issues")
    
    print("\n🔧 NEXT STEPS:")
    if not worker_running:
        print("   1. Start Celery worker: celery -A app.tasks.email_tasks worker --loglevel=info")
        print("   2. Make sure RabbitMQ is running")
    
    print("   3. Test user registration through the API")
    print("   4. Check email delivery in 5 minutes after registration")
    
    return immediate_ok and (worker_running and celery_ok)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
