#!/usr/bin/env python3
"""
Simple Campaign Email Test
==========================

Test the email campaign system by sending emails to Sahil.
"""

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_welcome_email():
    """Test sending welcome email to Sahil."""
    try:
        from app.services.email_campaign_service import send_welcome_email_campaign
        
        logger.info("📧 Testing Welcome Email Campaign")
        result = send_welcome_email_campaign('sahilsaurav2507@gmail.com', 'Sahil Saurav')
        
        if result:
            logger.info("✅ Welcome email sent successfully to Sahil!")
            return True
        else:
            logger.error("❌ Failed to send welcome email to Sahil")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending welcome email: {e}")
        return False

def test_campaign_email(campaign_type):
    """Test sending a specific campaign email to Sahil."""
    try:
        from app.services.email_campaign_service import send_scheduled_campaign_email
        
        logger.info(f"📧 Testing {campaign_type} Campaign Email")
        result = send_scheduled_campaign_email(campaign_type, 'sahilsaurav2507@gmail.com', 'Sahil Saurav')
        
        if result:
            logger.info(f"✅ {campaign_type} email sent successfully to Sahil!")
            return True
        else:
            logger.error(f"❌ Failed to send {campaign_type} email to Sahil")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending {campaign_type} email: {e}")
        return False

def test_campaign_schedule():
    """Test campaign schedule functionality."""
    try:
        from app.services.email_campaign_service import get_campaign_schedule
        
        logger.info("📅 Testing Campaign Schedule")
        schedule = get_campaign_schedule()
        
        logger.info(f"✅ Found {len(schedule)} campaigns:")
        for campaign_type, details in schedule.items():
            subject = details.get('subject', '')[:50] + "..."
            schedule_time = details.get('schedule', '')
            logger.info(f"   📧 {campaign_type}: {subject}")
            logger.info(f"      Schedule: {schedule_time}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error getting campaign schedule: {e}")
        return False

def main():
    """Main test function."""
    logger.info("🎯 LAWVRIKSH EMAIL CAMPAIGN SIMPLE TEST")
    logger.info("=" * 50)
    
    tests = [
        ("Campaign Schedule", test_campaign_schedule),
        ("Welcome Email", test_welcome_email),
        ("Search Engine Email", lambda: test_campaign_email("search_engine")),
        ("Portfolio Builder Email", lambda: test_campaign_email("portfolio_builder")),
        ("Platform Complete Email", lambda: test_campaign_email("platform_complete")),
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
    
    logger.info("\n" + "=" * 50)
    logger.info("📊 TEST RESULTS")
    logger.info("=" * 50)
    logger.info(f"Total Tests: {total}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {total - passed}")
    logger.info(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100.0:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("📧 Check sahilsaurav2507@gmail.com for campaign emails!")
    else:
        logger.warning("⚠️  Some tests failed")
    
    logger.info("=" * 50)
    
    return success_rate == 100.0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
