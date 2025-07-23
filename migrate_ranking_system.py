#!/usr/bin/env python3
"""
Database Migration for Dynamic Ranking System
=============================================

This script migrates the database to support the new dynamic ranking system:
1. Adds default_rank and current_rank columns to users table
2. Assigns default ranks to existing users based on registration order
3. Calculates current ranks based on points

Usage:
    python migrate_ranking_system.py
"""

import logging
from sqlalchemy import text
from app.core.dependencies import get_db
from app.models.user import User
from app.services.ranking_service import assign_default_rank, update_all_ranks

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_columns_exist(db):
    """Check if the new rank columns already exist."""
    try:
        result = db.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'users' 
            AND COLUMN_NAME IN ('default_rank', 'current_rank')
        """)).fetchall()
        
        existing_columns = [row[0] for row in result]
        return 'default_rank' in existing_columns, 'current_rank' in existing_columns
        
    except Exception as e:
        logger.error(f"Error checking columns: {e}")
        return False, False

def add_rank_columns(db):
    """Add the new rank columns to users table."""
    try:
        logger.info("Adding rank columns to users table...")
        
        # Add default_rank column
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN default_rank INT NULL,
            ADD INDEX idx_users_default_rank (default_rank)
        """))
        
        # Add current_rank column
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN current_rank INT NULL,
            ADD INDEX idx_users_current_rank (current_rank)
        """))
        
        db.commit()
        logger.info("✅ Rank columns added successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error adding rank columns: {e}")
        db.rollback()
        return False

def migrate_existing_users(db):
    """Migrate existing users to the new ranking system."""
    try:
        logger.info("Migrating existing users to new ranking system...")
        
        # Get all non-admin users ordered by creation date
        users = db.query(User).filter(
            User.is_admin == False
        ).order_by(User.created_at.asc()).all()
        
        logger.info(f"Found {len(users)} users to migrate")
        
        # Assign default ranks based on registration order
        for rank, user in enumerate(users, 1):
            user.default_rank = rank
            logger.info(f"Assigned default rank {rank} to user {user.id} ({user.name})")
        
        db.commit()
        logger.info("✅ Default ranks assigned")
        
        # Update current ranks based on points
        logger.info("Calculating current ranks based on points...")
        update_all_ranks(db)
        
        logger.info("✅ Current ranks calculated")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error migrating users: {e}")
        db.rollback()
        return False

def verify_migration(db):
    """Verify the migration was successful."""
    try:
        logger.info("Verifying migration...")
        
        # Check that all users have ranks assigned
        users_without_default_rank = db.query(User).filter(
            User.is_admin == False,
            User.default_rank.is_(None)
        ).count()
        
        users_without_current_rank = db.query(User).filter(
            User.is_admin == False,
            User.current_rank.is_(None)
        ).count()
        
        if users_without_default_rank > 0:
            logger.warning(f"⚠️  {users_without_default_rank} users without default rank")
            return False
        
        if users_without_current_rank > 0:
            logger.warning(f"⚠️  {users_without_current_rank} users without current rank")
            return False
        
        # Show sample of migrated users
        sample_users = db.query(User).filter(
            User.is_admin == False
        ).order_by(User.current_rank.asc()).limit(5).all()
        
        logger.info("📊 Sample of migrated users:")
        for user in sample_users:
            rank_improvement = (user.default_rank - user.current_rank) if user.default_rank and user.current_rank else 0
            logger.info(f"   {user.name}: Default Rank {user.default_rank} → Current Rank {user.current_rank} (Points: {user.total_points}, Improvement: {rank_improvement})")
        
        logger.info("✅ Migration verification successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying migration: {e}")
        return False

def main():
    """Main migration function."""
    logger.info("🚀 STARTING DYNAMIC RANKING SYSTEM MIGRATION")
    logger.info("=" * 60)
    
    try:
        # Get database session
        db = next(get_db())
        
        # Step 1: Check if columns already exist
        logger.info("Step 1: Checking existing database structure...")
        default_exists, current_exists = check_columns_exist(db)
        
        if default_exists and current_exists:
            logger.info("✅ Rank columns already exist")
        else:
            logger.info(f"Columns status - default_rank: {default_exists}, current_rank: {current_exists}")
            
            # Step 2: Add rank columns if needed
            if not (default_exists and current_exists):
                logger.info("Step 2: Adding rank columns...")
                if not add_rank_columns(db):
                    logger.error("❌ Failed to add rank columns")
                    return False
            else:
                logger.info("Step 2: Skipped - columns already exist")
        
        # Step 3: Migrate existing users
        logger.info("Step 3: Migrating existing users...")
        if not migrate_existing_users(db):
            logger.error("❌ Failed to migrate users")
            return False
        
        # Step 4: Verify migration
        logger.info("Step 4: Verifying migration...")
        if not verify_migration(db):
            logger.error("❌ Migration verification failed")
            return False
        
        # Close database session
        db.close()
        
        logger.info("=" * 60)
        logger.info("🎉 DYNAMIC RANKING SYSTEM MIGRATION COMPLETED!")
        logger.info("=" * 60)
        logger.info("✅ Database schema updated")
        logger.info("✅ Existing users migrated")
        logger.info("✅ Default ranks assigned based on registration order")
        logger.info("✅ Current ranks calculated based on points")
        logger.info("")
        logger.info("📋 New Features Available:")
        logger.info("   • New users get default rank based on registration order")
        logger.info("   • Users improve rank when they earn points from sharing")
        logger.info("   • Leaderboard shows both default and current ranks")
        logger.info("   • Rank improvement tracking")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
