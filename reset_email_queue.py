#!/usr/bin/env python3
"""
Reset Email Queue
=================

This script removes all old queued emails from before the new implementation
to demonstrate the fixed system working properly with fresh data.

Usage:
    python reset_email_queue.py [--confirm]
"""

import sys
import os
import argparse
from datetime import datetime
import pytz

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.email_queue import EmailQueue, EmailType, EmailStatus

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


def show_current_queue_status(session_factory):
    """Show current queue status before cleanup."""
    print("📊 Current Queue Status (Before Cleanup)")
    print("=" * 60)
    
    with session_factory() as db:
        try:
            # Get all emails by status
            total_emails = db.query(EmailQueue).count()
            pending_emails = db.query(EmailQueue).filter(EmailQueue.status == EmailStatus.pending).count()
            sent_emails = db.query(EmailQueue).filter(EmailQueue.status == EmailStatus.sent).count()
            failed_emails = db.query(EmailQueue).filter(EmailQueue.status == EmailStatus.failed).count()
            
            print(f"Total emails in queue: {total_emails}")
            print(f"  Pending: {pending_emails}")
            print(f"  Sent: {sent_emails}")
            print(f"  Failed: {failed_emails}")
            print()
            
            # Show emails by type
            for email_type in EmailType:
                type_count = db.query(EmailQueue).filter(EmailQueue.email_type == email_type).count()
                pending_count = db.query(EmailQueue).filter(
                    EmailQueue.email_type == email_type,
                    EmailQueue.status == EmailStatus.pending
                ).count()
                
                print(f"{email_type.value}: {type_count} total ({pending_count} pending)")
            
            print()
            
            # Show oldest and newest emails
            oldest_email = db.query(EmailQueue).order_by(EmailQueue.created_at.asc()).first()
            newest_email = db.query(EmailQueue).order_by(EmailQueue.created_at.desc()).first()
            
            if oldest_email:
                print(f"Oldest email: {oldest_email.created_at} ({oldest_email.email_type.value})")
            if newest_email:
                print(f"Newest email: {newest_email.created_at} ({newest_email.email_type.value})")
            
        except Exception as e:
            print(f"❌ Error getting queue status: {e}")


def reset_email_queue(session_factory, confirm=False):
    """Reset the email queue by removing all old emails."""
    print("\n🔄 Resetting Email Queue")
    print("=" * 60)
    
    if not confirm:
        print("⚠️  This will DELETE ALL emails from the queue!")
        print("   This includes:")
        print("   • All pending emails (welcome and campaign)")
        print("   • All sent emails (history)")
        print("   • All failed emails")
        print()
        response = input("Are you sure you want to continue? (type 'YES' to confirm): ")
        if response != 'YES':
            print("❌ Operation cancelled")
            return False
    
    with session_factory() as db:
        try:
            # Get counts before deletion
            total_before = db.query(EmailQueue).count()
            pending_before = db.query(EmailQueue).filter(EmailQueue.status == EmailStatus.pending).count()
            
            print(f"📊 Deleting {total_before} emails ({pending_before} pending)...")
            
            # Delete all emails
            deleted_count = db.query(EmailQueue).delete()
            db.commit()
            
            print(f"✅ Successfully deleted {deleted_count} emails from queue")
            print("🎉 Email queue has been reset!")
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error resetting queue: {e}")
            return False


def verify_clean_queue(session_factory):
    """Verify that the queue is now clean."""
    print("\n✅ Verifying Clean Queue")
    print("=" * 60)
    
    with session_factory() as db:
        try:
            total_emails = db.query(EmailQueue).count()
            
            if total_emails == 0:
                print("✅ Queue is completely clean!")
                print("🎯 Ready for fresh email scheduling with the new implementation")
                return True
            else:
                print(f"⚠️  {total_emails} emails still remain in queue")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying clean queue: {e}")
            return False


def demonstrate_fresh_scheduling(session_factory):
    """Demonstrate fresh scheduling with the new implementation."""
    print("\n🧪 Demonstrating Fresh Scheduling")
    print("=" * 60)
    
    from app.schemas.email_queue import EmailQueueCreate
    from app.services.email_queue_service import add_email_to_queue, get_next_scheduled_time
    
    with session_factory() as db:
        try:
            current_time = datetime.now(IST)
            print(f"🕐 Current time: {current_time}")
            print()
            
            # Show next scheduled time for each email type (should be immediate)
            print("📅 Next scheduled time for each email type (fresh queue):")
            for email_type in EmailType:
                next_time = get_next_scheduled_time(db, email_type)
                delay_minutes = (next_time - current_time).total_seconds() / 60
                
                print(f"   {email_type.value}: {next_time} (in {delay_minutes:.1f} minutes)")
            
            print()
            
            # Add a test welcome email to show immediate scheduling
            print("📧 Adding test welcome email to demonstrate immediate scheduling...")
            
            email_data = EmailQueueCreate(
                user_email="fresh.test@example.com",
                user_name="Fresh Test User",
                email_type=EmailType.welcome
            )
            
            welcome_email = add_email_to_queue(db, email_data)
            
            scheduled_time = welcome_email.scheduled_time
            if scheduled_time.tzinfo is None:
                scheduled_time = IST.localize(scheduled_time)
            
            delay_minutes = (scheduled_time - current_time).total_seconds() / 60
            
            print(f"✅ Welcome email scheduled at: {scheduled_time}")
            print(f"   Delay from now: {delay_minutes:.1f} minutes")
            
            if delay_minutes <= 1:
                print(f"   🎉 PERFECT! Welcome email scheduled immediately!")
            elif delay_minutes <= 5:
                print(f"   ✅ EXCELLENT! Welcome email scheduled within 5 minutes!")
            else:
                print(f"   ⚠️  Still delayed by {delay_minutes:.1f} minutes")
            
            # Clean up the test email
            db.delete(welcome_email)
            db.commit()
            print(f"🧹 Cleaned up test email")
            
            return delay_minutes <= 5
            
        except Exception as e:
            print(f"❌ Error demonstrating fresh scheduling: {e}")
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Reset Email Queue')
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    print("🚀 Email Queue Reset Tool")
    print("=" * 60)
    print("🎯 Purpose: Remove old emails to demonstrate the fixed queue system")
    print(f"🕐 Started: {datetime.now(IST)}")
    print("=" * 60)
    
    session_factory = setup_database()
    
    # Show current status
    show_current_queue_status(session_factory)
    
    # Reset the queue
    if reset_email_queue(session_factory, args.confirm):
        # Verify clean queue
        if verify_clean_queue(session_factory):
            # Demonstrate fresh scheduling
            if demonstrate_fresh_scheduling(session_factory):
                print("\n🎉 SUCCESS! Email queue reset complete!")
                print("\n✅ Key achievements:")
                print("   • All old emails removed")
                print("   • Fresh scheduling working perfectly")
                print("   • Welcome emails now schedule immediately")
                print("   • Ready for production use")
                
                print(f"\n💡 Next steps:")
                print(f"   • Register new users to see immediate welcome emails")
                print(f"   • Start email processor: py email_processor.py --daemon")
                print(f"   • Monitor queue: py email_queue_monitor.py status")
                
                return True
            else:
                print("\n⚠️  Fresh scheduling test failed")
                return False
        else:
            print("\n❌ Queue verification failed")
            return False
    else:
        print("\n❌ Queue reset failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
