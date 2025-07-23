#!/usr/bin/env python3
"""
Simple Email Test for Sahil
===========================

This script tests email delivery to sahilsaurav2507@gmail.com
after you've updated the SMTP password in .env file.

Usage:
    1. Update SMTP_PASSWORD in .env file
    2. python test_email_simple.py
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_email_delivery():
    """Test email delivery to Sahil."""
    
    try:
        # Load configuration
        from app.core.config import settings
        
        logger.info("📧 Testing Email Delivery to Sahil Saurav")
        logger.info("=" * 50)
        
        # Display configuration (hide password)
        logger.info(f"From: {settings.EMAIL_FROM}")
        logger.info(f"SMTP Host: {settings.SMTP_HOST}")
        logger.info(f"SMTP Port: {settings.SMTP_PORT}")
        logger.info(f"SMTP User: {settings.SMTP_USER}")
        logger.info(f"To: sahilsaurav2507@gmail.com")
        
        # Check if password is set
        if not settings.SMTP_PASSWORD or settings.SMTP_PASSWORD == "your-smtp-password-here" or settings.SMTP_PASSWORD == "your-gmail-app-password-here" or settings.SMTP_PASSWORD == "your-hostinger-email-password-here":
            logger.error("❌ SMTP_PASSWORD is not set properly in .env file")
            logger.error("   Please update SMTP_PASSWORD with your actual password")
            return False
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_FROM
        msg['To'] = "sahilsaurav2507@gmail.com"
        msg['Subject'] = "🎉 Lawvriksh Email Test - Welcome Sahil!"
        
        # Email body
        body = f"""
Hello Sahil Saurav,

🎉 Great news! Your Lawvriksh email system is now working!

This test email confirms that:
✅ SMTP configuration is correct
✅ Email delivery is functional
✅ Welcome emails will be sent during registration

Test Details:
- Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- From: {settings.EMAIL_FROM}
- SMTP Server: {settings.SMTP_HOST}:{settings.SMTP_PORT}

Next Steps:
1. Complete your registration flow
2. Start sharing on social media platforms
3. Earn points: Twitter(+1), Facebook(+3), LinkedIn(+5), Instagram(+2)
4. Climb the leaderboard rankings!

Welcome to Lawvriksh! 🚀

Best regards,
The Lawvriksh Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        logger.info("🔌 Connecting to SMTP server...")
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.set_debuglevel(0)  # Set to 1 for debug output
        
        logger.info("🔒 Starting TLS encryption...")
        server.starttls()
        
        logger.info("🔑 Authenticating...")
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        
        logger.info("📤 Sending email...")
        text = msg.as_string()
        server.sendmail(settings.EMAIL_FROM, "sahilsaurav2507@gmail.com", text)
        server.quit()
        
        logger.info("✅ EMAIL SENT SUCCESSFULLY!")
        logger.info("📧 Check sahilsaurav2507@gmail.com inbox (and spam folder)")
        logger.info("🎉 Email system is working correctly!")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ SMTP Authentication failed: {e}")
        logger.error("   Check your email username and password")
        logger.error("   For Gmail: Use App Password, not regular password")
        return False
        
    except smtplib.SMTPConnectError as e:
        logger.error(f"❌ SMTP Connection failed: {e}")
        logger.error("   Check SMTP host and port settings")
        return False
        
    except Exception as e:
        logger.error(f"❌ Email test failed: {e}")
        return False

def test_welcome_email_service():
    """Test the application's welcome email service."""
    
    try:
        logger.info("\n📧 Testing Application Email Service")
        logger.info("=" * 40)
        
        from app.services.email_service import send_welcome_email
        
        logger.info("📤 Sending welcome email via application service...")
        send_welcome_email("sahilsaurav2507@gmail.com", "Sahil Saurav")
        
        logger.info("✅ Welcome email sent via application service!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Application email service failed: {e}")
        return False

def test_celery_email_task():
    """Test Celery email task."""
    
    try:
        logger.info("\n🔄 Testing Celery Email Task")
        logger.info("=" * 30)
        
        from app.tasks.email_tasks import send_welcome_email_task
        
        logger.info("📤 Queuing welcome email task...")
        task_result = send_welcome_email_task.delay("sahilsaurav2507@gmail.com", "Sahil Saurav")
        
        logger.info(f"✅ Email task queued with ID: {task_result.id}")
        logger.info("⏳ Task is being processed by Celery worker...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Celery email task failed: {e}")
        logger.error("   Make sure Celery worker is running:")
        logger.error("   celery -A app.tasks.celery_app worker --loglevel=info")
        return False

def main():
    """Main function to run email tests."""
    
    logger.info("🎯 SAHIL EMAIL DELIVERY TEST")
    logger.info("=" * 60)
    
    success_count = 0
    total_tests = 3
    
    # Test 1: Direct SMTP test
    if test_email_delivery():
        success_count += 1
    
    # Test 2: Application email service
    if test_welcome_email_service():
        success_count += 1
    
    # Test 3: Celery email task
    if test_celery_email_task():
        success_count += 1
    
    # Final results
    logger.info("\n" + "=" * 60)
    logger.info("📊 EMAIL TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"Tests Passed: {success_count}/{total_tests}")
    logger.info(f"Success Rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        logger.info("🎉 ALL EMAIL TESTS PASSED!")
        logger.info("✅ Sahil will now receive welcome emails during registration")
        logger.info("\n📋 Next Steps:")
        logger.info("1. Check sahilsaurav2507@gmail.com for test emails")
        logger.info("2. Run registration test: python test_sahil_registration_flow.py")
        logger.info("3. Welcome emails will be delivered automatically!")
    else:
        logger.warning("⚠️  Some email tests failed")
        logger.warning("Please fix the issues above before proceeding")
    
    logger.info("=" * 60)
    
    return success_count == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
