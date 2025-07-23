#!/usr/bin/env python3
"""
Test Sahil's Instant Welcome Email
==================================

This script tests that Sahil receives the instant welcome email during registration.
"""

import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sahil_instant_welcome_email():
    """Test sending instant welcome email to Sahil during registration simulation."""
    try:
        logger.info("🎯 TESTING SAHIL'S INSTANT WELCOME EMAIL")
        logger.info("=" * 50)
        logger.info("Email: sahilsaurav2507@gmail.com")
        logger.info("Name: Sahil Saurav")
        logger.info("=" * 50)
        
        # Simulate the registration process
        logger.info("🔄 Simulating registration process...")
        
        # This is exactly what happens in the registration flow
        from app.services.email_campaign_service import send_welcome_email_campaign
        
        user_email = "sahilsaurav2507@gmail.com"
        user_name = "Sahil Saurav"
        
        logger.info(f"📧 Sending instant welcome email to {user_email}...")
        
        result = send_welcome_email_campaign(user_email, user_name)
        
        if result:
            logger.info("✅ INSTANT WELCOME EMAIL SENT SUCCESSFULLY!")
            logger.info("📧 Sahil should receive the email at sahilsaurav2507@gmail.com")
            logger.info("📱 Check both inbox and spam folder")
            logger.info("")
            logger.info("📋 Email Details:")
            logger.info("   Subject: ✨ Welcome Aboard, LawVriksh Founding Member!")
            logger.info("   From: info@lawvriksh.com")
            logger.info("   To: sahilsaurav2507@gmail.com")
            logger.info("   Content: Full founding member welcome message")
            return True
        else:
            logger.error("❌ INSTANT WELCOME EMAIL FAILED!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing instant welcome email: {e}")
        return False

def test_all_campaign_emails_to_sahil():
    """Test sending all campaign emails to Sahil."""
    try:
        logger.info("\n🎯 TESTING ALL CAMPAIGN EMAILS TO SAHIL")
        logger.info("=" * 50)
        
        from app.services.email_campaign_service import send_scheduled_campaign_email
        
        campaigns = [
            ("search_engine", "🚀 Search Engine Complete"),
            ("portfolio_builder", "🌟 Portfolio Builder Complete"),
            ("platform_complete", "🎉 Platform Launch")
        ]
        
        results = []
        for campaign_type, description in campaigns:
            logger.info(f"📧 Sending {description} email...")
            
            result = send_scheduled_campaign_email(
                campaign_type, 
                "sahilsaurav2507@gmail.com", 
                "Sahil Saurav"
            )
            
            if result:
                logger.info(f"✅ {description}: SENT")
                results.append(True)
            else:
                logger.error(f"❌ {description}: FAILED")
                results.append(False)
            
            time.sleep(1)  # Brief pause between emails
        
        success_count = sum(results)
        total_count = len(results)
        
        logger.info(f"\n📊 Campaign Emails Results: {success_count}/{total_count} sent")
        
        return success_count == total_count
        
    except Exception as e:
        logger.error(f"❌ Error testing campaign emails: {e}")
        return False

def main():
    """Main test function."""
    logger.info("🚨 SAHIL'S EMAIL SYSTEM TEST")
    logger.info("=" * 60)
    
    tests = [
        ("Instant Welcome Email", test_sahil_instant_welcome_email),
        ("All Campaign Emails", test_all_campaign_emails_to_sahil),
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
    logger.info("📊 SAHIL'S EMAIL TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total Tests: {total}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {total - passed}")
    logger.info(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100.0:
        logger.info("🎉 ALL EMAILS SENT TO SAHIL!")
        logger.info("📧 Check sahilsaurav2507@gmail.com for:")
        logger.info("   1. ✨ Welcome Aboard, LawVriksh Founding Member!")
        logger.info("   2. 🚀 Big News! Search Engine Complete!")
        logger.info("   3. 🌟 Portfolio Builder Complete!")
        logger.info("   4. 🎉 LawVriksh Platform Launch!")
        logger.info("📱 Check both inbox and spam folder")
    else:
        logger.warning("⚠️  Some emails failed to send")
    
    logger.info("=" * 60)
    
    return success_rate == 100.0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
