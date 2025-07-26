#!/usr/bin/env python3
"""
Comprehensive email system diagnostic script.
This will identify all issues preventing emails from being sent to new users.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import smtplib
import logging
from email.mime.text import MIMEText
from app.core.config import settings
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_email_configuration():
    """Check if email configuration is properly set up."""
    print("🔍 CHECKING EMAIL CONFIGURATION")
    print("=" * 50)
    
    issues = []
    
    # Check basic email settings
    print(f"📧 EMAIL_FROM: {settings.EMAIL_FROM}")
    print(f"🌐 SMTP_HOST: {settings.SMTP_HOST}")
    print(f"🔌 SMTP_PORT: {settings.SMTP_PORT}")
    print(f"👤 SMTP_USER: {settings.SMTP_USER}")
    print(f"🔑 SMTP_PASSWORD: {'SET' if settings.SMTP_PASSWORD else 'NOT SET'}")
    
    if not settings.SMTP_PASSWORD:
        issues.append("❌ SMTP_PASSWORD is not set")
    elif settings.SMTP_PASSWORD in ['your-smtp-password-here', 'your-hostinger-email-password-here', '']:
        issues.append("❌ SMTP_PASSWORD appears to be a placeholder value")
    
    if not settings.EMAIL_FROM:
        issues.append("❌ EMAIL_FROM is not set")
    
    if not settings.SMTP_HOST:
        issues.append("❌ SMTP_HOST is not set")
    
    if not settings.SMTP_USER:
        issues.append("❌ SMTP_USER is not set")
    
    return issues

def test_smtp_connection():
    """Test SMTP connection and authentication."""
    print("\n🔌 TESTING SMTP CONNECTION")
    print("=" * 50)
    
    try:
        print(f"Connecting to {settings.SMTP_HOST}:{settings.SMTP_PORT}...")
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            print("✅ Connected to SMTP server")
            
            print("🔐 Starting TLS...")
            server.starttls()
            print("✅ TLS started successfully")
            
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                print(f"🔑 Authenticating as {settings.SMTP_USER}...")
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                print("✅ Authentication successful")
            else:
                print("⚠️  No authentication credentials provided")
                
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {e}")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"❌ SMTP Connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ SMTP Test failed: {e}")
        return False

def test_email_sending():
    """Test sending a real email."""
    print("\n📧 TESTING EMAIL SENDING")
    print("=" * 50)
    
    test_email = input("Enter a test email address to send to (or press Enter to skip): ").strip()
    if not test_email:
        print("⏭️  Skipping email sending test")
        return True
    
    try:
        subject = "🧪 LawVriksh Email System Test"
        body = """Hello!

This is a test email from the LawVriksh email system diagnostic tool.

If you received this email, the email system is working correctly!

Best regards,
LawVriksh Team"""

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = test_email
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, [test_email], msg.as_string())
        
        print(f"✅ Test email sent successfully to {test_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False

def check_email_queue_status():
    """Check if database email queue is working (replaces Celery check)."""
    print("\n🔄 CHECKING EMAIL QUEUE STATUS")
    print("=" * 50)
    
    try:
        from app.services.email_queue_service import get_queue_stats
        from app.core.dependencies import get_db
        
        # Get database session
        db = next(get_db())
        try:
            # Get queue statistics
            stats = get_queue_stats(db)
            
            print(f"✅ Email queue system operational")
            print(f"📊 Total emails: {stats.total_emails}")
            print(f"⏳ Pending: {stats.pending_count}")
            print(f"🚀 Processing: {stats.processing_count}")
            print(f"✅ Sent: {stats.sent_count}")
            print(f"❌ Failed: {stats.failed_count}")
            
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Email queue check failed: {e}")
        return False

def check_signup_endpoint():
    """Check the current state of the signup endpoint."""
    print("\n📝 CHECKING SIGNUP ENDPOINT")
    print("=" * 50)
    
    try:
        # Read the auth.py file to check if email sending is enabled
        with open('app/api/auth.py', 'r') as f:
            content = f.read()
        
        if '# send_5_minute_welcome_email_task.apply_async(' in content:
            print("❌ Email sending is DISABLED in signup endpoint")
            print("   The welcome email task is commented out")
            return False
        elif 'send_5_minute_welcome_email_task.apply_async(' in content:
            print("✅ Email sending is ENABLED in signup endpoint")
            return True
        else:
            print("⚠️  Could not determine email sending status")
            return False
            
    except Exception as e:
        print(f"❌ Failed to check signup endpoint: {e}")
        return False

def main():
    """Run comprehensive email system diagnostics."""
    print("🚀 LAWVRIKSH EMAIL SYSTEM DIAGNOSTICS")
    print("=" * 60)
    
    all_issues = []
    
    # 1. Check email configuration
    config_issues = check_email_configuration()
    all_issues.extend(config_issues)
    
    # 2. Test SMTP connection
    smtp_ok = test_smtp_connection()
    if not smtp_ok:
        all_issues.append("❌ SMTP connection/authentication failed")
    
    # 3. Test email sending
    email_ok = test_email_sending()
    if not email_ok:
        all_issues.append("❌ Email sending test failed")
    
    # 4. Check Email Queue status
    queue_ok = check_email_queue_status()
    if not queue_ok:
        all_issues.append("❌ Email queue system issues detected")
    
    # 5. Check signup endpoint
    signup_ok = check_signup_endpoint()
    if not signup_ok:
        all_issues.append("❌ Email sending disabled in signup endpoint")
    
    # Summary
    print("\n📋 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    if all_issues:
        print("❌ ISSUES FOUND:")
        for issue in all_issues:
            print(f"   {issue}")
        
        print("\n🔧 RECOMMENDED FIXES:")
        if any("SMTP" in issue for issue in all_issues):
            print("   1. Verify SMTP credentials are correct")
            print("   2. Check if email provider allows SMTP access")
            print("   3. Try using Gmail with App Password as alternative")
        
        if any("signup endpoint" in issue for issue in all_issues):
            print("   4. Enable email sending in app/api/auth.py")
        
        if any("Celery" in issue for issue in all_issues):
            print("   5. Start Celery worker: celery -A app.tasks.email_tasks worker --loglevel=info")
            print("   6. Install/start RabbitMQ message broker")
        
    else:
        print("✅ ALL CHECKS PASSED!")
        print("   Email system appears to be working correctly.")
    
    return len(all_issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
