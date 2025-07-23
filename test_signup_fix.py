#!/usr/bin/env python3
"""
Test script to verify signup functionality after fixing rank columns
"""

import logging
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.models.user import User
from app.services.user_service import get_user_by_email

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_user_query():
    """Test if we can query users without errors."""
    try:
        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)
        
        logger.info("Testing user query...")
        
        # Try to query a user by email (this was failing before)
        test_email = "sahilsaurav2fgjfg507@gmail.com"
        user = get_user_by_email(db, test_email)
        
        if user:
            logger.info(f"✅ Found user: {user.name} (ID: {user.id})")
            logger.info(f"   Default rank: {user.default_rank}")
            logger.info(f"   Current rank: {user.current_rank}")
        else:
            logger.info(f"✅ No user found with email {test_email} (this is expected)")
        
        # Test querying all users
        users = db.query(User).limit(5).all()
        logger.info(f"✅ Successfully queried {len(users)} users")
        
        for user in users:
            logger.info(f"   User: {user.name} (ID: {user.id}, default_rank: {user.default_rank}, current_rank: {user.current_rank})")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing user query: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Testing signup fix")
    logger.info("=" * 40)
    
    if test_user_query():
        logger.info("🎉 User queries working correctly!")
        logger.info("You can now try the signup API again.")
    else:
        logger.error("❌ User queries still failing")
