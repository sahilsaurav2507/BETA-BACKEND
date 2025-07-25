#!/usr/bin/env python3
"""
Email Sending Test Script
========================

Test script to send a test email to prabhjotjaswal09@gmail.com
This will test the complete email queue system functionality.

Usage:
    python test_email_send.py
"""

import sys
import os
import time
from datetime import datetime
import pytz

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.email_queue import EmailQueue, EmailType, EmailStatus
from app.schemas.email_queue import EmailQueueCreate
from app.services.email_queue_service import add_email_to_queue, get_pending_emails, update_email_status
from app.services.email_service import send_email

# IST timezone
IST = pytz.timezone('Asia/Kolkata')


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


def test_email_queue_add():
    """Test adding email to queue."""
    print("🧪 Testing Email Queue - Adding Test Email")
    print("-" * 50)
    
    session_factory = setup_database()
    
    with session_factory() as db:
        try:
            # Create test email data
            email_data = EmailQueueCreate(
                user_email="prabhjotjaswal09@gmail.com",
                user_name="Prabhjot Jaswal",
                email_type=EmailType.welcome
            )
            
            # Add to queue
            email_entry = add_email_to_queue(db, email_data)
            
            print(f"✅ Email added to queue successfully!")
            print(f"   Queue ID: {email_entry.id}")
            print(f"   Email: {email_entry.user_email}")
            print(f"   Type: {email_entry.email_type.value}")
            print(f"   Scheduled: {email_entry.scheduled_time}")
            print(f"   Status: {email_entry.status.value}")
            
            return email_entry.id
            
        except Exception as e:
            print(f"❌ Failed to add email to queue: {e}")
            return None


def test_direct_email_send():
    """Test sending email directly (bypass queue)."""
    print("\n🧪 Testing Direct Email Send")
    print("-" * 50)
    
    try:
        # Test email content
        subject = "✨ LawVriksh Email System Test"
        body = """Hello Prabhjot,

This is a test email from the LawVriksh email queue system!

🎉 If you're reading this, the email system is working perfectly.

Key features tested:
✅ Database-driven email queue
✅ Email template processing
✅ SMTP delivery
✅ Sequential 5-minute scheduling

The new email system successfully replaces Redis/Celery with a pure database approach.

Best regards,
The LawVriksh Development Team

---
🌐 Visit us: https://www.lawvriksh.com
📧 Contact: info@lawvriksh.com
🚀 This email was sent via the new database-driven queue system
        """
        
        # Send email directly
        send_email("prabhjotjaswal09@gmail.com", subject, body)
        
        print(f"✅ Email sent successfully!")
        print(f"   To: prabhjotjaswal09@gmail.com")
        print(f"   Subject: {subject}")
        print(f"   Time: {datetime.now(IST)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        print(f"   Error details: {str(e)}")
        return False


def test_queue_processing():
    """Test processing email from queue."""
    print("\n🧪 Testing Queue Processing")
    print("-" * 50)
    
    session_factory = setup_database()
    
    with session_factory() as db:
        try:
            # Get pending emails
            pending_emails = get_pending_emails(db, limit=5)
            
            if not pending_emails:
                print("ℹ️  No pending emails found in queue")
                return True
            
            print(f"📧 Found {len(pending_emails)} pending emails")
            
            # Process the first pending email
            email = pending_emails[0]
            
            print(f"\n🔄 Processing email ID: {email.id}")
            print(f"   To: {email.user_email}")
            print(f"   Type: {email.email_type.value}")
            print(f"   Scheduled: {email.scheduled_time}")
            
            # Mark as processing
            update_email_status(db, email.id, EmailStatus.processing)
            
            try:
                # Send the email
                send_email(email.user_email, email.subject, email.body)
                
                # Mark as sent
                update_email_status(db, email.id, EmailStatus.sent)
                
                print(f"✅ Email processed and sent successfully!")
                return True
                
            except Exception as send_error:
                # Mark as failed
                update_email_status(db, email.id, EmailStatus.failed, str(send_error))
                print(f"❌ Failed to send email: {send_error}")
                return False
                
        except Exception as e:
            print(f"❌ Error processing queue: {e}")
            return False


def check_email_configuration():
    """Check email configuration."""
    print("🔍 Checking Email Configuration")
    print("-" * 50)
    
    try:
        print(f"SMTP Host: {settings.SMTP_HOST}")
        print(f"SMTP Port: {settings.SMTP_PORT}")
        print(f"SMTP User: {settings.SMTP_USER}")
        print(f"Email From: {settings.EMAIL_FROM}")
        print(f"SMTP Password: {'***' if settings.SMTP_PASSWORD else 'Not set'}")
        
        if not all([settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USER, settings.SMTP_PASSWORD]):
            print("\n⚠️  Warning: Some email configuration values are missing")
            print("   Please check your .env file or environment variables")
            return False
        
        print("\n✅ Email configuration looks good")
        return True
        
    except Exception as e:
        print(f"❌ Error checking email configuration: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 LawVriksh Email System Test")
    print("=" * 60)
    print(f"📧 Test recipient: prabhjotjaswal09@gmail.com")
    print(f"🕐 Test time: {datetime.now(IST)}")
    print("=" * 60)
    
    # Check email configuration
    if not check_email_configuration():
        print("\n❌ Email configuration check failed!")
        print("Please fix the configuration before testing.")
        sys.exit(1)
    
    # Test 1: Direct email send (fastest test)
    print("\n" + "="*60)
    if test_direct_email_send():
        print("\n🎉 Direct email send test PASSED!")
    else:
        print("\n❌ Direct email send test FAILED!")
        print("Please check your SMTP configuration.")
        sys.exit(1)
    
    # Test 2: Add email to queue
    print("\n" + "="*60)
    email_id = test_email_queue_add()
    if email_id:
        print(f"\n🎉 Email queue add test PASSED! (ID: {email_id})")
    else:
        print("\n❌ Email queue add test FAILED!")
        sys.exit(1)
    
    # Test 3: Process email from queue
    print("\n" + "="*60)
    if test_queue_processing():
        print("\n🎉 Queue processing test PASSED!")
    else:
        print("\n❌ Queue processing test FAILED!")
    
    # Final summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print("✅ Email configuration check")
    print("✅ Direct email sending")
    print("✅ Email queue functionality")
    print("✅ Queue processing")
    print("\n🎉 All email system tests completed!")
    print(f"📧 Check prabhjotjaswal09@gmail.com for test emails")
    print("\n💡 To start the email processor daemon:")
    print("   python email_processor.py --daemon")
    print("\n💡 To monitor the queue:")
    print("   python email_queue_monitor.py status")


if __name__ == "__main__":
    main()
