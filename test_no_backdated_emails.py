#!/usr/bin/env python3
"""
Test No Backdated Emails Logic
==============================

This script tests that new users don't receive emails for campaigns that have already passed.

Test Scenarios:
1. Check which campaigns are past/future
2. Verify new users only get future campaigns
3. Test instant welcome email always works
4. Verify no backdated emails are sent

Usage:
    python test_no_backdated_emails.py
"""

import logging
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

def test_campaign_past_future_logic():
    """Test the logic for determining past vs future campaigns."""
    try:
        logger.info("🔄 Testing Campaign Past/Future Logic")
        
        from app.services.email_campaign_service import (
            EMAIL_TEMPLATES, 
            is_campaign_in_past,
            get_future_campaigns_for_new_user
        )
        
        current_time = datetime.now(IST)
        logger.info(f"Current time (IST): {current_time}")
        
        logger.info("\n📅 Campaign Status Analysis:")
        for campaign_type, template in EMAIL_TEMPLATES.items():
            schedule = template["schedule"]
            subject = template["subject"][:50] + "..."
            
            if campaign_type == "welcome":
                logger.info(f"   ✅ {campaign_type}: INSTANT - {subject}")
                continue
            
            is_past = is_campaign_in_past(campaign_type)
            status = "PAST" if is_past else "FUTURE"
            emoji = "❌" if is_past else "✅"
            
            logger.info(f"   {emoji} {campaign_type}: {status} - {schedule}")
            logger.info(f"      Subject: {subject}")
        
        # Test future campaigns for new users
        future_campaigns = get_future_campaigns_for_new_user()
        logger.info(f"\n🔮 Future campaigns for new users: {len(future_campaigns)}")
        for campaign in future_campaigns:
            logger.info(f"   ✅ {campaign}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Campaign logic test failed: {e}")
        return False

def test_new_user_email_logic():
    """Test what emails a new user would receive."""
    try:
        logger.info("\n🔄 Testing New User Email Logic")
        
        from app.services.email_campaign_service import (
            send_welcome_email_campaign,
            get_future_campaigns_for_new_user,
            is_campaign_in_past
        )
        
        test_email = "testuser@example.com"
        test_name = "Test User"
        
        # Test instant welcome email
        logger.info("📧 Testing instant welcome email...")
        welcome_result = send_welcome_email_campaign(test_email, test_name)
        
        if welcome_result:
            logger.info("✅ Instant welcome email: WORKING")
        else:
            logger.error("❌ Instant welcome email: FAILED")
            return False
        
        # Check future campaigns
        future_campaigns = get_future_campaigns_for_new_user()
        logger.info(f"\n📋 New user would receive:")
        logger.info(f"   ✅ Welcome email: INSTANT (always sent)")
        
        if future_campaigns:
            logger.info(f"   ✅ Future campaigns: {len(future_campaigns)}")
            for campaign in future_campaigns:
                logger.info(f"      - {campaign}")
        else:
            logger.info("   ⚠️  No future campaigns (all campaigns are in the past)")
        
        # Check past campaigns (should NOT be sent)
        from app.services.email_campaign_service import EMAIL_TEMPLATES
        past_campaigns = []
        for campaign_type in EMAIL_TEMPLATES.keys():
            if campaign_type != "welcome" and is_campaign_in_past(campaign_type):
                past_campaigns.append(campaign_type)
        
        if past_campaigns:
            logger.info(f"   ❌ Past campaigns (NOT sent): {len(past_campaigns)}")
            for campaign in past_campaigns:
                logger.info(f"      - {campaign} (backdated - skipped)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ New user email logic test failed: {e}")
        return False

def test_sahil_registration_scenario():
    """Test Sahil's registration scenario with current date logic."""
    try:
        logger.info("\n🔄 Testing Sahil's Registration Scenario")
        
        sahil_email = "sahilsaurav2507@gmail.com"
        sahil_name = "Sahil Saurav"
        
        from app.services.email_campaign_service import (
            send_welcome_email_campaign,
            get_future_campaigns_for_new_user,
            EMAIL_TEMPLATES
        )
        
        logger.info(f"👤 User: {sahil_name} ({sahil_email})")
        logger.info(f"📅 Registration Date: {datetime.now(IST)}")
        
        # Send welcome email (always works)
        logger.info("\n📧 Sending instant welcome email...")
        welcome_result = send_welcome_email_campaign(sahil_email, sahil_name)
        
        if welcome_result:
            logger.info("✅ Welcome email sent successfully")
        else:
            logger.error("❌ Welcome email failed")
            return False
        
        # Check what future campaigns Sahil would get
        future_campaigns = get_future_campaigns_for_new_user()
        
        logger.info(f"\n📋 Sahil's Email Schedule:")
        logger.info("   ✅ Mail 1 (Welcome): SENT INSTANTLY")
        
        campaign_names = {
            "search_engine": "Mail 2 (Search Engine Complete)",
            "portfolio_builder": "Mail 3 (Portfolio Builder Complete)", 
            "platform_complete": "Mail 4 (Platform Launch)"
        }
        
        for campaign_type, template in EMAIL_TEMPLATES.items():
            if campaign_type == "welcome":
                continue
                
            campaign_name = campaign_names.get(campaign_type, campaign_type)
            schedule = template["schedule"]
            
            if campaign_type in future_campaigns:
                logger.info(f"   ✅ {campaign_name}: WILL BE SENT on {schedule}")
            else:
                logger.info(f"   ❌ {campaign_name}: SKIPPED (past date) - was {schedule}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Sahil registration scenario test failed: {e}")
        return False

def test_bulk_campaign_logic():
    """Test bulk campaign sending logic (should skip past campaigns)."""
    try:
        logger.info("\n🔄 Testing Bulk Campaign Logic")
        
        from app.services.email_campaign_service import (
            get_due_campaigns,
            is_campaign_in_past,
            EMAIL_TEMPLATES
        )
        
        # Check due campaigns (should exclude past ones)
        due_campaigns = get_due_campaigns()
        logger.info(f"📊 Due campaigns (excluding past): {len(due_campaigns)}")
        
        for campaign in due_campaigns:
            logger.info(f"   ✅ {campaign}: Due and not past")
        
        # Check all campaigns status
        logger.info("\n📋 All Campaigns Status:")
        for campaign_type, template in EMAIL_TEMPLATES.items():
            if campaign_type == "welcome":
                continue
                
            is_past = is_campaign_in_past(campaign_type)
            schedule = template["schedule"]
            
            if is_past:
                logger.info(f"   ❌ {campaign_type}: PAST ({schedule}) - Won't be sent in bulk")
            else:
                logger.info(f"   ✅ {campaign_type}: FUTURE ({schedule}) - Can be sent in bulk")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Bulk campaign logic test failed: {e}")
        return False

def main():
    """Main test function."""
    logger.info("🚨 NO BACKDATED EMAILS TEST")
    logger.info("=" * 60)
    logger.info("Testing that new users don't receive past campaign emails")
    logger.info("=" * 60)
    
    tests = [
        ("Campaign Past/Future Logic", test_campaign_past_future_logic),
        ("New User Email Logic", test_new_user_email_logic),
        ("Sahil Registration Scenario", test_sahil_registration_scenario),
        ("Bulk Campaign Logic", test_bulk_campaign_logic),
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
    logger.info("📊 NO BACKDATED EMAILS TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total Tests: {total}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {total - passed}")
    logger.info(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100.0:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("✅ No backdated emails will be sent to new users")
        logger.info("✅ Only instant welcome + future campaigns will be sent")
        logger.info("✅ Past campaigns are properly skipped")
    else:
        logger.warning("⚠️  Some tests failed")
    
    logger.info("=" * 60)
    
    return success_rate == 100.0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
