#!/usr/bin/env python3
"""
Fix Instant Welcome Email Issue
===============================

This script diagnoses and fixes the instant welcome email issue for Sahil.
"""

import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_email_service():
    """Test the basic email service."""
    try:
        logger.info("🔧 Testing Basic Email Service")
        from app.services.email_service import send_email
        
        subject = "Test Email from LawVriksh"
        body = "This is a test email to verify SMTP is working."
        
        send_email("sahilsaurav2507@gmail.com", subject, body)
        logger.info("✅ Basic email service working!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic email service failed: {e}")
        logger.error(traceback.format_exc())
        return False

def test_welcome_email_campaign():
    """Test the welcome email campaign."""
    try:
        logger.info("📧 Testing Welcome Email Campaign")
        from app.services.email_campaign_service import send_welcome_email_campaign
        
        result = send_welcome_email_campaign("sahilsaurav2507@gmail.com", "Sahil Saurav")
        
        if result:
            logger.info("✅ Welcome email campaign sent successfully!")
            return True
        else:
            logger.error("❌ Welcome email campaign failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Welcome email campaign error: {e}")
        logger.error(traceback.format_exc())
        return False

def test_email_template():
    """Test the email template rendering."""
    try:
        logger.info("📝 Testing Email Template")
        from app.services.email_campaign_service import EMAIL_TEMPLATES
        
        template = EMAIL_TEMPLATES["welcome"]
        subject = template["subject"]
        body = template["template"].format(name="Sahil Saurav")
        
        logger.info(f"✅ Template rendered successfully!")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body length: {len(body)} characters")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Template rendering failed: {e}")
        logger.error(traceback.format_exc())
        return False

def send_direct_welcome_email():
    """Send welcome email directly using basic email service."""
    try:
        logger.info("📤 Sending Direct Welcome Email to Sahil")
        from app.services.email_service import send_email
        
        subject = "✨ Welcome Aboard, LawVriksh Founding Member!"
        body = """
Dear Sahil Saurav,

A huge, heartfelt **CONGRATULATIONS** for becoming one of our exclusive LawVriksh Beta Testing Founding Members! 🎉

Welcome aboard! We're absolutely thrilled to have you join our growing community of forward-thinking legal professionals and enthusiasts. By registering with LawVriksh, you've taken the first monumental step towards unlocking a wealth of legal knowledge, connecting with brilliant peers, and staying not just ahead, but **leading** in the ever-evolving legal landscape.

We're incredibly committed to providing you with invaluable resources and unparalleled opportunities to grow, learn, and connect. Your insights as a founding member will be crucial in shaping LawVriksh into the ultimate platform for the legal community.

Get ready for an exciting journey! We'll be in touch very soon with more updates and access details.

Warmly,
The LawVriksh Team

---
🌐 Visit us: https://www.lawvriksh.com
📧 Contact: info@lawvriksh.com
        """
        
        send_email("sahilsaurav2507@gmail.com", subject, body)
        logger.info("✅ Direct welcome email sent to Sahil!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Direct welcome email failed: {e}")
        logger.error(traceback.format_exc())
        return False

def test_smtp_configuration():
    """Test SMTP configuration."""
    try:
        logger.info("🔌 Testing SMTP Configuration")
        from app.core.config import settings
        
        logger.info(f"EMAIL_FROM: {settings.EMAIL_FROM}")
        logger.info(f"SMTP_HOST: {settings.SMTP_HOST}")
        logger.info(f"SMTP_PORT: {settings.SMTP_PORT}")
        logger.info(f"SMTP_USER: {settings.SMTP_USER}")
        logger.info(f"SMTP_PASSWORD: {'SET' if settings.SMTP_PASSWORD else 'NOT SET'}")
        
        if not settings.SMTP_PASSWORD or settings.SMTP_PASSWORD in ['your-smtp-password-here', 'your-hostinger-email-password-here']:
            logger.error("❌ SMTP password not properly configured!")
            return False
        
        logger.info("✅ SMTP configuration looks good!")
        return True
        
    except Exception as e:
        logger.error(f"❌ SMTP configuration check failed: {e}")
        return False

def fix_registration_email():
    """Test the registration flow email sending."""
    try:
        logger.info("🔄 Testing Registration Email Flow")
        
        # Simulate what happens during registration
        user_email = "sahilsaurav2507@gmail.com"
        user_name = "Sahil Saurav"
        
        # Test the exact code from auth.py
        try:
            from app.services.email_campaign_service import send_welcome_email_campaign
            result = send_welcome_email_campaign(user_email, user_name)
            
            if result:
                logger.info("✅ Registration email flow working!")
                return True
            else:
                logger.error("❌ Registration email flow failed!")
                return False
                
        except Exception as e:
            logger.error(f"❌ Registration email flow error: {e}")
            logger.error(traceback.format_exc())
            return False
            
    except Exception as e:
        logger.error(f"❌ Registration email flow test failed: {e}")
        return False

def main():
    """Main diagnostic and fix function."""
    logger.info("🚨 FIXING INSTANT WELCOME EMAIL ISSUE")
    logger.info("=" * 60)
    logger.info("Target: sahilsaurav2507@gmail.com")
    logger.info("User: Sahil Saurav")
    logger.info("=" * 60)
    
    tests = [
        ("SMTP Configuration", test_smtp_configuration),
        ("Email Template", test_email_template),
        ("Basic Email Service", test_email_service),
        ("Welcome Email Campaign", test_welcome_email_campaign),
        ("Registration Email Flow", fix_registration_email),
        ("Direct Welcome Email", send_direct_welcome_email),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n🔄 Running: {test_name}")
        try:
            result = test_func()
            results.append(result)
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED with exception: {e}")
            results.append(False)
    
    # Final results
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total) * 100
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 INSTANT EMAIL FIX RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total Tests: {total}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {total - passed}")
    logger.info(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80.0:
        logger.info("🎉 EMAIL SYSTEM FIXED!")
        logger.info("📧 Sahil should receive welcome email at sahilsaurav2507@gmail.com")
        logger.info("✅ Check inbox and spam folder")
    else:
        logger.warning("⚠️  Email system needs more fixes")
        logger.warning("Please check the failed tests above")
    
    logger.info("=" * 60)
    
    return success_rate >= 80.0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
