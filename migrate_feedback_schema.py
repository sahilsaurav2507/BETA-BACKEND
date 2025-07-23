#!/usr/bin/env python3
"""
Database migration script to update feedback table schema
Adds email and name fields and makes some fields optional
"""

import sys
import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_database():
    """Run the database migration"""
    print("🔄 Starting feedback table migration...")
    
    try:
        # Create database engine
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Check if email column already exists
                if not check_column_exists(engine, 'feedback', 'email'):
                    print("📝 Adding email column...")
                    conn.execute(text("""
                        ALTER TABLE feedback 
                        ADD COLUMN email VARCHAR(255) NOT NULL DEFAULT 'unknown@example.com'
                    """))
                    
                    # Create index for email
                    print("📝 Creating email index...")
                    conn.execute(text("""
                        CREATE INDEX ix_feedback_email ON feedback (email)
                    """))
                else:
                    print("✅ Email column already exists")
                
                # Check if name column already exists
                if not check_column_exists(engine, 'feedback', 'name'):
                    print("📝 Adding name column...")
                    conn.execute(text("""
                        ALTER TABLE feedback 
                        ADD COLUMN name VARCHAR(255) NOT NULL DEFAULT 'Unknown User'
                    """))
                else:
                    print("✅ Name column already exists")
                
                # Make primary_motivation nullable
                print("📝 Making primary_motivation nullable...")
                conn.execute(text("""
                    ALTER TABLE feedback 
                    MODIFY COLUMN primary_motivation ENUM('A', 'B', 'C', 'D') NULL
                """))
                
                # Make time_consuming_part nullable
                print("📝 Making time_consuming_part nullable...")
                conn.execute(text("""
                    ALTER TABLE feedback 
                    MODIFY COLUMN time_consuming_part ENUM('A', 'B', 'C', 'D') NULL
                """))
                
                # Make monetization_considerations nullable
                print("📝 Making monetization_considerations nullable...")
                conn.execute(text("""
                    ALTER TABLE feedback 
                    MODIFY COLUMN monetization_considerations TEXT NULL
                """))
                
                # Make professional_legacy nullable
                print("📝 Making professional_legacy nullable...")
                conn.execute(text("""
                    ALTER TABLE feedback 
                    MODIFY COLUMN professional_legacy TEXT NULL
                """))
                
                # Remove default values from new columns
                print("📝 Removing default values...")
                conn.execute(text("""
                    ALTER TABLE feedback 
                    ALTER COLUMN email DROP DEFAULT
                """))
                
                conn.execute(text("""
                    ALTER TABLE feedback 
                    ALTER COLUMN name DROP DEFAULT
                """))
                
                # Commit transaction
                trans.commit()
                print("✅ Migration completed successfully!")
                
                # Show updated schema
                print("\n📊 Updated feedback table schema:")
                result = conn.execute(text("DESCRIBE feedback"))
                for row in result:
                    print(f"   - {row[0]} ({row[1]}) {'NULL' if row[2] == 'YES' else 'NOT NULL'}")
                
            except Exception as e:
                trans.rollback()
                raise e
                
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

def rollback_migration():
    """Rollback the migration (for testing purposes)"""
    print("🔄 Rolling back feedback table migration...")
    
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Make fields non-nullable again (only if they have data)
                print("📝 Making fields non-nullable...")
                conn.execute(text("""
                    ALTER TABLE feedback 
                    MODIFY COLUMN professional_legacy TEXT NOT NULL
                """))
                
                conn.execute(text("""
                    ALTER TABLE feedback 
                    MODIFY COLUMN monetization_considerations TEXT NOT NULL
                """))
                
                conn.execute(text("""
                    ALTER TABLE feedback 
                    MODIFY COLUMN time_consuming_part ENUM('A', 'B', 'C', 'D') NOT NULL
                """))
                
                conn.execute(text("""
                    ALTER TABLE feedback 
                    MODIFY COLUMN primary_motivation ENUM('A', 'B', 'C', 'D') NOT NULL
                """))
                
                # Drop new columns
                if check_column_exists(engine, 'feedback', 'email'):
                    print("📝 Dropping email column...")
                    conn.execute(text("DROP INDEX ix_feedback_email ON feedback"))
                    conn.execute(text("ALTER TABLE feedback DROP COLUMN email"))
                
                if check_column_exists(engine, 'feedback', 'name'):
                    print("📝 Dropping name column...")
                    conn.execute(text("ALTER TABLE feedback DROP COLUMN name"))
                
                trans.commit()
                print("✅ Rollback completed successfully!")
                
            except Exception as e:
                trans.rollback()
                raise e
                
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        migrate_database()
