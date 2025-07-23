#!/usr/bin/env python3
"""
LawVriksh Email Campaign System Test
===================================

This script tests the complete email campaign system for LawVriksh Beta Launch.

Test Coverage:
1. Campaign schedule verification
2. Welcome email (instant on signup)
3. Scheduled campaign emails
4. Campaign management API
5. Sahil Saurav email delivery

Usage:
    python test_email_campaigns.py --url http://localhost:8000
"""

import requests
import time
import logging
import argparse
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailCampaignTest:
    """Test the email campaign system."""
    
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        self.admin_token = None
        
    def get_admin_token(self):
        """Get admin token for API access."""
        try:
            # Try to login as admin
            admin_credentials = {
                "email": "admin@lawvriksh.com",
                "password": "password123"
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", json=admin_credentials)
            
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data.get("access_token")
                logger.info("✅ Admin token obtained successfully")
                return True
            else:
                logger.error(f"❌ Failed to get admin token: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error getting admin token: {e}")
            return False
    
    def test_campaign_schedule(self):
        """Test campaign schedule API."""
        logger.info("🔄 Testing Campaign Schedule API")
        
        if not self.admin_token:
            logger.error("❌ No admin token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{self.base_url}/campaigns/schedule", headers=headers)
            
            if response.status_code == 200:
                schedule_data = response.json()
                campaigns = schedule_data.get("campaigns", {})
                due_campaigns = schedule_data.get("due_campaigns", [])
                
                logger.info("✅ Campaign schedule retrieved successfully")
                logger.info(f"   Total campaigns: {len(campaigns)}")
                logger.info(f"   Due campaigns: {len(due_campaigns)}")
                
                # Display campaign details
                for campaign_type, details in campaigns.items():
                    schedule_time = details.get("schedule")
                    subject = details.get("subject", "")[:50] + "..."
                    logger.info(f"   📧 {campaign_type}: {subject}")
                    logger.info(f"      Schedule: {schedule_time}")
                
                return True
            else:
                logger.error(f"❌ Failed to get campaign schedule: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing campaign schedule: {e}")
            return False
    
    def test_campaign_preview(self):
        """Test campaign preview functionality."""
        logger.info("🔄 Testing Campaign Preview")
        
        if not self.admin_token:
            logger.error("❌ No admin token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            campaigns = ["welcome", "search_engine", "portfolio_builder", "platform_complete"]
            
            for campaign_type in campaigns:
                response = self.session.get(f"{self.base_url}/campaigns/preview/{campaign_type}", headers=headers)
                
                if response.status_code == 200:
                    preview_data = response.json()
                    subject = preview_data.get("subject", "")
                    logger.info(f"✅ {campaign_type}: {subject}")
                else:
                    logger.error(f"❌ Failed to preview {campaign_type}: {response.status_code}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error testing campaign preview: {e}")
            return False
    
    def test_sahil_welcome_email(self):
        """Test sending welcome email to Sahil."""
        logger.info("🔄 Testing Sahil Welcome Email")
        
        if not self.admin_token:
            logger.error("❌ No admin token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(f"{self.base_url}/campaigns/test-sahil?campaign_type=welcome", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id")
                logger.info("✅ Welcome email sent to Sahil Saurav")
                logger.info(f"   Task ID: {task_id}")
                logger.info(f"   Recipient: {result.get('recipient')}")
                return True
            else:
                logger.error(f"❌ Failed to send welcome email to Sahil: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending welcome email to Sahil: {e}")
            return False
    
    def test_campaign_email_to_sahil(self, campaign_type):
        """Test sending a specific campaign email to Sahil."""
        logger.info(f"🔄 Testing {campaign_type} Email to Sahil")
        
        if not self.admin_token:
            logger.error("❌ No admin token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(f"{self.base_url}/campaigns/test-sahil?campaign_type={campaign_type}", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id")
                logger.info(f"✅ {campaign_type} email sent to Sahil Saurav")
                logger.info(f"   Task ID: {task_id}")
                return True
            else:
                logger.error(f"❌ Failed to send {campaign_type} email to Sahil: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending {campaign_type} email to Sahil: {e}")
            return False
    
    def test_new_user_registration_with_welcome_email(self):
        """Test new user registration triggers welcome email."""
        logger.info("🔄 Testing New User Registration with Welcome Email")
        
        try:
            # Create a new test user
            timestamp = int(time.time())
            user_data = {
                "name": f"Campaign Test User {timestamp}",
                "email": f"campaigntest{timestamp}@example.com",
                "password": "TestPassword123!"
            }
            
            response = self.session.post(f"{self.base_url}/auth/signup", json=user_data)
            
            if response.status_code == 201:
                user_response = response.json()
                logger.info("✅ New user registered successfully")
                logger.info(f"   User: {user_response.get('name')}")
                logger.info(f"   Email: {user_response.get('email')}")
                logger.info("   Welcome email should be sent automatically")
                return True
            else:
                logger.error(f"❌ Failed to register new user: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing new user registration: {e}")
            return False
    
    def test_campaign_status(self):
        """Test campaign status API."""
        logger.info("🔄 Testing Campaign Status API")
        
        if not self.admin_token:
            logger.error("❌ No admin token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            campaigns = ["welcome", "search_engine", "portfolio_builder", "platform_complete"]
            
            for campaign_type in campaigns:
                response = self.session.get(f"{self.base_url}/campaigns/status/{campaign_type}", headers=headers)
                
                if response.status_code == 200:
                    status_data = response.json()
                    is_due = status_data.get("is_due", False)
                    schedule = status_data.get("schedule", "")
                    logger.info(f"✅ {campaign_type}: Due={is_due}, Schedule={schedule}")
                else:
                    logger.error(f"❌ Failed to get status for {campaign_type}: {response.status_code}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error testing campaign status: {e}")
            return False
    
    def run_complete_test_suite(self):
        """Run the complete email campaign test suite."""
        logger.info("📧 LAWVRIKSH EMAIL CAMPAIGN SYSTEM TEST")
        logger.info("=" * 60)
        logger.info(f"API URL: {self.base_url}")
        logger.info("=" * 60)
        
        test_results = []
        
        # Get admin token first
        if not self.get_admin_token():
            logger.error("❌ Cannot proceed without admin token")
            return False
        
        # Test sequence
        tests = [
            ("Campaign Schedule API", self.test_campaign_schedule),
            ("Campaign Preview", self.test_campaign_preview),
            ("Campaign Status API", self.test_campaign_status),
            ("Sahil Welcome Email", self.test_sahil_welcome_email),
            ("New User Registration", self.test_new_user_registration_with_welcome_email),
        ]
        
        # Test individual campaign emails to Sahil
        campaign_types = ["search_engine", "portfolio_builder", "platform_complete"]
        for campaign_type in campaign_types:
            tests.append((f"Sahil {campaign_type.title()} Email", 
                         lambda ct=campaign_type: self.test_campaign_email_to_sahil(ct)))
        
        # Run all tests
        for test_name, test_function in tests:
            logger.info(f"\n🔄 Running: {test_name}")
            try:
                result = test_function()
                test_results.append(result)
                if result:
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                logger.error(f"❌ {test_name}: FAILED with exception: {e}")
                test_results.append(False)
        
        # Final results
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 EMAIL CAMPAIGN TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100.0:
            logger.info("🎉 ALL TESTS PASSED!")
            logger.info("✅ Email campaign system is fully functional!")
            logger.info("📧 Sahil should receive all test emails")
        else:
            logger.warning("⚠️  Some tests failed. Check the logs above.")
        
        logger.info("=" * 60)
        
        return success_rate == 100.0

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test LawVriksh Email Campaign System")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    args = parser.parse_args()
    
    test_suite = EmailCampaignTest(args.url)
    success = test_suite.run_complete_test_suite()
    
    if success:
        print("\n🎉 Email campaign system is working perfectly!")
        print("📧 Check sahilsaurav2507@gmail.com for test emails")
    else:
        print("\n❌ Some tests failed. Please check the logs above.")
    
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
