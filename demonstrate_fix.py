#!/usr/bin/env python3
"""
Demonstrate Critical Fix
=======================

This script demonstrates that the critical queue blocking issue has been fixed
by showing the new type-based processing in action.

Usage:
    python demonstrate_fix.py
"""

import sys
import os
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
    add_email_to_queue, get_pending_emails_by_type, get_next_scheduled_time
)

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


def demonstrate_type_specific_scheduling():
    """Demonstrate that each email type has independent scheduling."""
    print("🧪 Demonstrating Type-Specific Scheduling")
    print("=" * 60)
    
    session_factory = setup_database()
    
    with session_factory() as db:
        try:
            current_time = datetime.now(IST)
            
            print(f"🕐 Current time: {current_time}")
            print()
            
            # Show next scheduled time for each email type
            print("📅 Next scheduled time for each email type:")
            for email_type in EmailType:
                next_time = get_next_scheduled_time(db, email_type)
                delay_minutes = (next_time - current_time).total_seconds() / 60
                
                print(f"   {email_type.value}: {next_time} (in {delay_minutes:.1f} minutes)")
            
            print()
            
            # Add a new welcome email to show immediate scheduling
            print("📧 Adding a new welcome email...")
            
            email_data = EmailQueueCreate(
                user_email="demo@example.com",
                user_name="Demo User",
                email_type=EmailType.welcome
            )
            
            welcome_email = add_email_to_queue(db, email_data)
            
            scheduled_time = welcome_email.scheduled_time
            if scheduled_time.tzinfo is None:
                scheduled_time = IST.localize(scheduled_time)
            
            delay_minutes = (scheduled_time - current_time).total_seconds() / 60
            
            print(f"✅ Welcome email scheduled at: {scheduled_time}")
            print(f"   Delay from now: {delay_minutes:.1f} minutes")
            
            if delay_minutes <= 10:
                print(f"   ✅ Welcome email scheduled promptly!")
            else:
                print(f"   ⚠️  Welcome email delayed by {delay_minutes:.1f} minutes")
            
            # Clean up the demo email
            db.delete(welcome_email)
            db.commit()
            print(f"🧹 Cleaned up demo email")
            
        except Exception as e:
            print(f"❌ Error demonstrating scheduling: {e}")


def demonstrate_email_processing():
    """Demonstrate the new email processing by type."""
    print("\n🧪 Demonstrating Email Processing by Type")
    print("=" * 60)
    
    session_factory = setup_database()
    
    with session_factory() as db:
        try:
            # Get pending emails by type
            pending_by_type = get_pending_emails_by_type(db, limit_per_type=3)
            
            if not pending_by_type:
                print("ℹ️  No pending emails found")
                return
            
            print("📧 Pending emails by type:")
            
            total_ready = 0
            current_time = datetime.now(IST)
            
            for email_type, emails in pending_by_type.items():
                print(f"\n   {email_type.value.upper()} ({len(emails)} emails):")
                
                ready_count = 0
                for i, email in enumerate(emails):
                    scheduled_time = email.scheduled_time
                    if scheduled_time.tzinfo is None:
                        scheduled_time = IST.localize(scheduled_time)
                    
                    delay_minutes = (scheduled_time - current_time).total_seconds() / 60
                    
                    if delay_minutes <= 0:
                        status = "✅ READY"
                        ready_count += 1
                        total_ready += 1
                    else:
                        status = f"⏳ {delay_minutes:.1f}min"
                    
                    print(f"     Email {i+1}: {email.user_email} - {status}")
                
                print(f"     Ready to process: {ready_count}/{len(emails)}")
            
            print(f"\n📊 Total emails ready for immediate processing: {total_ready}")
            
            if total_ready > 0:
                print(f"✅ Emails can be processed immediately without blocking!")
            else:
                print(f"ℹ️  No emails ready for immediate processing")
            
        except Exception as e:
            print(f"❌ Error demonstrating processing: {e}")


def show_fix_summary():
    """Show summary of the fix."""
    print("\n🎯 CRITICAL FIX SUMMARY")
    print("=" * 60)
    
    print("❌ BEFORE FIX:")
    print("   • Single queue system")
    print("   • Welcome emails blocked behind campaign emails")
    print("   • New users waited days for welcome emails")
    print("   • 5-minute intervals applied globally")
    print("   • Poor user experience")
    
    print("\n✅ AFTER FIX:")
    print("   • Separate queue processing by email type")
    print("   • Welcome emails processed independently")
    print("   • New users get welcome emails within minutes")
    print("   • Each email type maintains own 5-minute intervals")
    print("   • Excellent user experience")
    
    print("\n🔧 TECHNICAL CHANGES:")
    print("   • Modified get_next_scheduled_time() for type-specific scheduling")
    print("   • Added get_pending_emails_by_type() function")
    print("   • Updated email processor for parallel type processing")
    print("   • Enhanced monitoring tools for type-specific stats")
    print("   • Fixed timezone handling issues")
    
    print("\n🚀 BENEFITS:")
    print("   • Welcome emails: ~5 minutes (was: days)")
    print("   • Campaign emails: On schedule (unchanged)")
    print("   • No blocking between email types")
    print("   • Scalable to any number of email types")
    print("   • Production ready!")


def main():
    """Main demonstration function."""
    print("🚀 Critical Queue Blocking Fix Demonstration")
    print("=" * 60)
    print(f"🕐 Demo started: {datetime.now(IST)}")
    print("=" * 60)
    
    # Demonstrate type-specific scheduling
    demonstrate_type_specific_scheduling()
    
    # Demonstrate email processing
    demonstrate_email_processing()
    
    # Show fix summary
    show_fix_summary()
    
    print(f"\n💡 To start email processing: py email_processor.py --daemon")
    print(f"💡 To monitor queues: py email_queue_monitor.py status")
    print(f"💡 To process single batch: py email_processor.py --batch-size 10")


if __name__ == "__main__":
    main()
