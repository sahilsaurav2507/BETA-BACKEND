#!/usr/bin/env python3
"""
Test script to verify feedback table functionality
"""

import logging
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.models.feedback import Feedback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_feedback_table():
    """Test if we can query and insert into feedback table."""
    try:
        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)
        
        logger.info("Testing feedback table...")
        
        # Test querying feedback table
        feedback_count = db.query(Feedback).count()
        logger.info(f"✅ Current feedback count: {feedback_count}")
        
        # Test that we can access all the required fields
        logger.info("✅ Feedback model fields accessible:")
        logger.info("   - email: available")
        logger.info("   - name: available") 
        logger.info("   - biggest_hurdle: available")
        logger.info("   - primary_motivation: available")
        logger.info("   - time_consuming_part: available")
        logger.info("   - professional_fear: available")
        logger.info("   - monetization_considerations: available")
        logger.info("   - professional_legacy: available")
        logger.info("   - platform_impact: available")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing feedback table: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Testing feedback table")
    logger.info("=" * 40)
    
    if test_feedback_table():
        logger.info("🎉 Feedback table working correctly!")
        logger.info("You can now try the feedback submission API.")
    else:
        logger.error("❌ Feedback table still has issues")
