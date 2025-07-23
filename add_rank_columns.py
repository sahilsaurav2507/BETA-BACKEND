#!/usr/bin/env python3
"""
Simple script to add missing rank columns to users table
"""

import logging
from sqlalchemy import create_engine, text
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_rank_columns():
    """Add the missing rank columns to users table."""
    try:
        # Create engine
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        
        logger.info("Connecting to database...")
        
        with engine.connect() as connection:
            # Check if columns already exist
            logger.info("Checking if rank columns exist...")
            
            result = connection.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME IN ('default_rank', 'current_rank')
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            logger.info(f"Existing rank columns: {existing_columns}")
            
            # Add default_rank if it doesn't exist
            if 'default_rank' not in existing_columns:
                logger.info("Adding default_rank column...")
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN default_rank INT NULL
                """))
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD INDEX idx_users_default_rank (default_rank)
                """))
                logger.info("✅ default_rank column added")
            else:
                logger.info("✅ default_rank column already exists")
            
            # Add current_rank if it doesn't exist
            if 'current_rank' not in existing_columns:
                logger.info("Adding current_rank column...")
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN current_rank INT NULL
                """))
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD INDEX idx_users_current_rank (current_rank)
                """))
                logger.info("✅ current_rank column added")
            else:
                logger.info("✅ current_rank column already exists")
            
            # Commit the changes
            connection.commit()
            logger.info("✅ All rank columns are now available")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error adding rank columns: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Adding rank columns to users table")
    logger.info("=" * 50)
    
    if add_rank_columns():
        logger.info("🎉 Rank columns added successfully!")
    else:
        logger.error("❌ Failed to add rank columns")
