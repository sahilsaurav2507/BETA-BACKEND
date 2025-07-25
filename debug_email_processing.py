#!/usr/bin/env python3
"""
Debug Email Processing
======================

This script debugs why emails are not being processed and fixes the issue.

Usage:
    python debug_email_processing.py
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
from app.services.email_queue_service import get_pending_emails, get_pending_emails_by_type

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


def debug_pending_emails():
    """Debug why emails are not being processed."""
    print("🔍 Debugging Email Processing Issues")
    print("=" * 60)
    
    session_factory = setup_database()
    
    with session_factory() as db:
        try:
            current_time = datetime.now(IST)
            print(f"🕐 Current time: {current_time}")
            print()
            
            # Get all pending emails (regardless of schedule)
            all_pending = db.query(EmailQueue).filter(
                EmailQueue.status == EmailStatus.pending
            ).order_by(EmailQueue.scheduled_time).all()
            
            print(f"📧 All pending emails in database: {len(all_pending)}")
            
            for email in all_pending:
                scheduled_time = email.scheduled_time
                if scheduled_time.tzinfo is None:
                    scheduled_time = IST.localize(scheduled_time)
                
                time_diff = (scheduled_time - current_time).total_seconds() / 60
                
                if time_diff <= 0:
                    status = "✅ DUE NOW"
                elif time_diff <= 5:
                    status = f"⏳ Due in {time_diff:.1f} min"
                else:
                    status = f"🕒 Due in {time_diff:.1f} min"
                
                print(f"   ID {email.id}: {email.user_email} ({email.email_type.value}) - {status}")
                print(f"      Scheduled: {scheduled_time}")
                print(f"      Current:   {current_time}")
                print()
            
            # Test get_pending_emails function
            print("🧪 Testing get_pending_emails function:")
            pending_emails = get_pending_emails(db, limit=10)
            print(f"   Found {len(pending_emails)} emails ready to process")
            
            if not pending_emails and all_pending:
                print("   ❌ ISSUE: get_pending_emails is not finding due emails!")
                
                # Check the first pending email manually
                first_email = all_pending[0]
                scheduled_time = first_email.scheduled_time
                if scheduled_time.tzinfo is None:
                    scheduled_time = IST.localize(scheduled_time)
                
                print(f"   📧 First pending email:")
                print(f"      Scheduled: {scheduled_time} (tz: {scheduled_time.tzinfo})")
                print(f"      Current:   {current_time} (tz: {current_time.tzinfo})")
                print(f"      Comparison: {scheduled_time <= current_time}")
                
                # Test timezone-aware comparison
                if scheduled_time.tzinfo != current_time.tzinfo:
                    print("   ⚠️  TIMEZONE MISMATCH DETECTED!")
                    
                    # Convert both to UTC for comparison
                    scheduled_utc = scheduled_time.astimezone(pytz.UTC)
                    current_utc = current_time.astimezone(pytz.UTC)
                    
                    print(f"      Scheduled UTC: {scheduled_utc}")
                    print(f"      Current UTC:   {current_utc}")
                    print(f"      UTC Comparison: {scheduled_utc <= current_utc}")
            
            return len(pending_emails), len(all_pending)
            
        except Exception as e:
            print(f"❌ Error debugging emails: {e}")
            return 0, 0


def fix_timezone_issues():
    """Fix timezone issues in pending emails."""
    print("\n🔧 Fixing Timezone Issues")
    print("=" * 60)
    
    session_factory = setup_database()
    
    with session_factory() as db:
        try:
            # Get all pending emails with timezone issues
            pending_emails = db.query(EmailQueue).filter(
                EmailQueue.status == EmailStatus.pending
            ).all()
            
            fixed_count = 0
            current_time = datetime.now(IST)
            
            for email in pending_emails:
                # Check if scheduled_time is timezone-naive
                if email.scheduled_time.tzinfo is None:
                    print(f"📧 Fixing timezone for email ID {email.id}")
                    print(f"   Before: {email.scheduled_time} (naive)")
                    
                    # Convert to IST
                    email.scheduled_time = IST.localize(email.scheduled_time)
                    
                    print(f"   After:  {email.scheduled_time} (IST)")
                    fixed_count += 1
                
                # If email is overdue, reschedule it for immediate processing
                if email.scheduled_time <= current_time:
                    print(f"📧 Rescheduling overdue email ID {email.id} for immediate processing")
                    email.scheduled_time = current_time
            
            if fixed_count > 0:
                db.commit()
                print(f"✅ Fixed timezone issues for {fixed_count} emails")
            else:
                print("ℹ️  No timezone issues found")
            
            return fixed_count
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error fixing timezone issues: {e}")
            return 0


def force_process_due_emails():
    """Force process emails that are due."""
    print("\n🚀 Force Processing Due Emails")
    print("=" * 60)
    
    session_factory = setup_database()
    
    with session_factory() as db:
        try:
            current_time = datetime.now(IST)
            
            # Get emails that should be processed now
            due_emails = db.query(EmailQueue).filter(
                EmailQueue.status == EmailStatus.pending,
                EmailQueue.scheduled_time <= current_time
            ).order_by(EmailQueue.scheduled_time).all()
            
            print(f"📧 Found {len(due_emails)} emails due for processing")
            
            if due_emails:
                print("   Processing emails:")
                for email in due_emails:
                    print(f"   • ID {email.id}: {email.user_email} ({email.email_type.value})")
                
                # Import and use the email processor
                from email_processor import process_email_batch_by_type
                
                processed = process_email_batch_by_type(session_factory, batch_size=10, dry_run=True)
                
                total_processed = sum(processed.values())
                print(f"✅ Processed {total_processed} emails")
                
                for email_type, count in processed.items():
                    if count > 0:
                        print(f"   • {email_type}: {count} emails")
                
                return total_processed
            else:
                print("ℹ️  No emails due for processing")
                return 0
            
        except Exception as e:
            print(f"❌ Error force processing emails: {e}")
            return 0


def main():
    """Main debug function."""
    print("🔍 Email Processing Debug Tool")
    print("=" * 60)
    print(f"🕐 Debug started: {datetime.now(IST)}")
    print("=" * 60)
    
    # Debug pending emails
    ready_count, total_count = debug_pending_emails()
    
    # Fix timezone issues if needed
    if ready_count == 0 and total_count > 0:
        fixed_count = fix_timezone_issues()
        
        if fixed_count > 0:
            print("\n🔄 Re-checking after timezone fix...")
            ready_count, total_count = debug_pending_emails()
    
    # Force process due emails
    if ready_count > 0 or total_count > 0:
        processed_count = force_process_due_emails()
        
        if processed_count > 0:
            print(f"\n✅ Successfully processed {processed_count} emails!")
        else:
            print(f"\n⚠️  No emails were processed")
    
    print("\n" + "=" * 60)
    print("🎯 DEBUG SUMMARY")
    print("=" * 60)
    print(f"Total pending emails: {total_count}")
    print(f"Ready for processing: {ready_count}")
    print(f"Processed in this run: {processed_count if 'processed_count' in locals() else 0}")
    
    if total_count == 0:
        print("\n✅ No emails in queue - system is clean")
    elif ready_count == total_count:
        print("\n✅ All emails are ready for processing")
    elif ready_count == 0:
        print("\n⚠️  No emails ready - check scheduling logic")
    else:
        print(f"\n📊 {ready_count}/{total_count} emails ready for processing")
    
    print(f"\n💡 To process emails: py email_processor.py --daemon")
    print(f"💡 To monitor queue: py email_queue_monitor.py status")


if __name__ == "__main__":
    main()
