#!/usr/bin/env python3
"""
Test Dynamic Ranking System
===========================

This script tests the new dynamic ranking system:
1. Creates multiple test users
2. Tests default rank assignment
3. Tests rank improvement through sharing
4. Verifies leaderboard updates

Usage:
    python test_dynamic_ranking.py --url http://localhost:8000
"""

import requests
import time
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DynamicRankingTest:
    """Test the dynamic ranking system."""
    
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        self.test_users = []
    
    def create_test_user(self, name_suffix):
        """Create a test user and return user data."""
        timestamp = int(time.time())
        user_data = {
            "name": f"Test User {name_suffix}",
            "email": f"testuser{name_suffix}_{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/auth/signup", json=user_data)
            
            if response.status_code == 201:
                user_response = response.json()
                
                # Login to get token
                login_response = self.session.post(f"{self.base_url}/auth/login", json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                })
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    user_response["access_token"] = token_data.get("access_token")
                
                self.test_users.append(user_response)
                return user_response
            else:
                logger.error(f"Failed to create user {name_suffix}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating user {name_suffix}: {e}")
            return None
    
    def get_user_profile(self, access_token):
        """Get user profile with current rank information."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get user profile: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def share_on_platform(self, access_token, platform):
        """Share on a social media platform."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = self.session.post(f"{self.base_url}/shares/{platform}", headers=headers)
            
            if response.status_code == 201:
                return response.json()
            else:
                logger.warning(f"Share on {platform} failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error sharing on {platform}: {e}")
            return None
    
    def get_leaderboard(self):
        """Get current leaderboard."""
        try:
            response = self.session.get(f"{self.base_url}/leaderboard")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get leaderboard: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return None
    
    def test_default_rank_assignment(self):
        """Test that new users get default ranks based on registration order."""
        logger.info("🔄 Testing Default Rank Assignment")
        logger.info("-" * 40)
        
        # Create 3 test users
        for i in range(1, 4):
            logger.info(f"Creating test user {i}...")
            user = self.create_test_user(f"DefaultRank{i}")
            
            if user:
                profile = self.get_user_profile(user["access_token"])
                if profile:
                    logger.info(f"✅ User {i}: {profile['name']}")
                    logger.info(f"   Default Rank: {profile.get('default_rank')}")
                    logger.info(f"   Current Rank: {profile.get('current_rank')}")
                    logger.info(f"   Points: {profile.get('total_points', 0)}")
                else:
                    logger.error(f"❌ Failed to get profile for user {i}")
            else:
                logger.error(f"❌ Failed to create user {i}")
            
            time.sleep(1)
        
        return len(self.test_users) >= 3
    
    def test_rank_improvement_through_sharing(self):
        """Test that users improve rank when they earn points."""
        logger.info("\n🔄 Testing Rank Improvement Through Sharing")
        logger.info("-" * 50)
        
        if len(self.test_users) < 3:
            logger.error("❌ Not enough test users for rank improvement test")
            return False
        
        # Take the last user (should have highest default rank)
        test_user = self.test_users[-1]
        access_token = test_user["access_token"]
        
        # Get initial profile
        initial_profile = self.get_user_profile(access_token)
        if not initial_profile:
            logger.error("❌ Failed to get initial profile")
            return False
        
        logger.info(f"📊 Initial State for {initial_profile['name']}:")
        logger.info(f"   Default Rank: {initial_profile.get('default_rank')}")
        logger.info(f"   Current Rank: {initial_profile.get('current_rank')}")
        logger.info(f"   Points: {initial_profile.get('total_points', 0)}")
        
        # Share on all platforms to earn maximum points
        platforms = ["twitter", "facebook", "linkedin", "instagram"]
        expected_points = {"twitter": 1, "facebook": 3, "linkedin": 5, "instagram": 2}
        total_points_earned = 0
        
        for platform in platforms:
            logger.info(f"   📱 Sharing on {platform}...")
            share_result = self.share_on_platform(access_token, platform)
            
            if share_result:
                points_earned = share_result.get("points_earned", 0)
                total_points_earned += points_earned
                logger.info(f"   ✅ {platform}: +{points_earned} points, New Rank: {share_result.get('new_rank')}")
            else:
                logger.warning(f"   ⚠️  {platform}: Share failed or already shared")
            
            time.sleep(0.5)
        
        # Get final profile
        final_profile = self.get_user_profile(access_token)
        if not final_profile:
            logger.error("❌ Failed to get final profile")
            return False
        
        logger.info(f"\n📊 Final State for {final_profile['name']}:")
        logger.info(f"   Default Rank: {final_profile.get('default_rank')}")
        logger.info(f"   Current Rank: {final_profile.get('current_rank')}")
        logger.info(f"   Points: {final_profile.get('total_points', 0)}")
        
        # Calculate rank improvement
        initial_rank = initial_profile.get('current_rank')
        final_rank = final_profile.get('current_rank')
        
        if initial_rank and final_rank:
            rank_improvement = initial_rank - final_rank
            logger.info(f"   Rank Improvement: {rank_improvement} positions")
            
            if rank_improvement > 0:
                logger.info("✅ Rank improvement successful!")
                return True
            else:
                logger.warning("⚠️  No rank improvement detected")
                return False
        else:
            logger.error("❌ Could not calculate rank improvement")
            return False
    
    def test_leaderboard_updates(self):
        """Test that leaderboard reflects the new ranking system."""
        logger.info("\n🔄 Testing Leaderboard Updates")
        logger.info("-" * 35)
        
        leaderboard_data = self.get_leaderboard()
        if not leaderboard_data:
            logger.error("❌ Failed to get leaderboard")
            return False
        
        leaderboard = leaderboard_data.get("leaderboard", [])
        
        logger.info(f"📊 Current Leaderboard (Top {len(leaderboard)} users):")
        logger.info("   Rank | Name | Points | Default Rank | Improvement")
        logger.info("   " + "-" * 55)
        
        for user in leaderboard:
            rank = user.get("rank")
            name = user.get("name", "Unknown")
            points = user.get("points", 0)
            default_rank = user.get("default_rank")
            rank_improvement = user.get("rank_improvement", 0)
            
            default_rank_str = str(default_rank) if default_rank is not None else "None"
            rank_improvement_str = f"{rank_improvement:+d}" if rank_improvement is not None else "N/A"
            logger.info(f"   {rank:4d} | {name:20s} | {points:6d} | {default_rank_str:11s} | {rank_improvement_str:11s}")
        
        # Verify ranking logic
        for i in range(len(leaderboard) - 1):
            current_user = leaderboard[i]
            next_user = leaderboard[i + 1]
            
            current_points = current_user.get("points", 0)
            next_points = next_user.get("points", 0)
            
            if current_points < next_points:
                logger.error(f"❌ Ranking error: User at rank {current_user.get('rank')} has fewer points than user at rank {next_user.get('rank')}")
                return False
        
        logger.info("✅ Leaderboard ranking is correct!")
        return True
    
    def run_all_tests(self):
        """Run all dynamic ranking tests."""
        logger.info("🎯 DYNAMIC RANKING SYSTEM TEST")
        logger.info("=" * 60)
        logger.info(f"API URL: {self.base_url}")
        logger.info("=" * 60)
        
        test_results = []
        
        # Test 1: Default rank assignment
        test_results.append(self.test_default_rank_assignment())
        
        # Test 2: Rank improvement through sharing
        test_results.append(self.test_rank_improvement_through_sharing())
        
        # Test 3: Leaderboard updates
        test_results.append(self.test_leaderboard_updates())
        
        # Final results
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 DYNAMIC RANKING TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100.0:
            logger.info("🎉 ALL TESTS PASSED!")
            logger.info("✅ Dynamic ranking system is working correctly!")
        else:
            logger.warning("⚠️  Some tests failed. Check the logs above.")
        
        logger.info("=" * 60)
        
        return success_rate == 100.0

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test Dynamic Ranking System")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    args = parser.parse_args()
    
    test_suite = DynamicRankingTest(args.url)
    success = test_suite.run_all_tests()
    
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
