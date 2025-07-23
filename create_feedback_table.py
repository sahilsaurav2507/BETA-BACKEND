#!/usr/bin/env python3
"""
Script to create the feedback table with email and name fields
"""

import logging
from sqlalchemy import create_engine, text
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_feedback_table():
    """Create the feedback table with all required fields."""
    try:
        # Create engine
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        
        logger.info("Connecting to database...")
        
        with engine.connect() as connection:
            # Check if table already exists
            logger.info("Checking if feedback table exists...")
            
            result = connection.execute(text("""
                SELECT COUNT(*) as table_count
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'feedback'
            """))
            
            table_exists = result.fetchone()[0] > 0
            
            if table_exists:
                logger.info("✅ Feedback table already exists")
                return True
            
            logger.info("Creating feedback table...")
            
            # Create the feedback table
            connection.execute(text("""
                CREATE TABLE feedback (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    
                    -- User identification (optional - can be anonymous)
                    user_id INT NULL,
                    ip_address VARCHAR(45) NULL,
                    user_agent TEXT NULL,
                    
                    -- Contact information
                    email VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    
                    -- Multiple choice responses
                    biggest_hurdle ENUM('A', 'B', 'C', 'D', 'E') NOT NULL,
                    biggest_hurdle_other TEXT NULL,
                    primary_motivation ENUM('A', 'B', 'C', 'D') NULL,
                    time_consuming_part ENUM('A', 'B', 'C', 'D') NULL,
                    professional_fear ENUM('A', 'B', 'C', 'D') NOT NULL,
                    
                    -- Short answer responses (2-4 sentences each)
                    monetization_considerations TEXT NULL,
                    professional_legacy TEXT NULL,
                    platform_impact TEXT NOT NULL,
                    
                    -- Metadata
                    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    -- Indexes for performance
                    INDEX idx_feedback_user_id (user_id),
                    INDEX idx_feedback_email (email),
                    INDEX idx_feedback_submitted_at (submitted_at),
                    INDEX idx_feedback_biggest_hurdle (biggest_hurdle),
                    INDEX idx_feedback_primary_motivation (primary_motivation),
                    INDEX idx_feedback_professional_fear (professional_fear),
                    INDEX idx_feedback_time_consuming_part (time_consuming_part),
                    
                    -- Foreign key constraint (optional, allows anonymous feedback)
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Commit the changes
            connection.commit()
            logger.info("✅ Feedback table created successfully")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating feedback table: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Creating feedback table")
    logger.info("=" * 40)
    
    if create_feedback_table():
        logger.info("🎉 Feedback table ready!")
    else:
        logger.error("❌ Failed to create feedback table")
