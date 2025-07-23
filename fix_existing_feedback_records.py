#!/usr/bin/env python3
"""
Fix existing feedback records that don't have email and name fields
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def fix_existing_records():
    """Update existing feedback records with default email and name values"""
    print("🔄 Fixing existing feedback records...")
    
    try:
        # Create database engine
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Check for records with empty email or name
                result = conn.execute(text("""
                    SELECT id, email, name 
                    FROM feedback 
                    WHERE email = 'unknown@example.com' OR name = 'Unknown User'
                    OR email IS NULL OR name IS NULL
                    OR email = '' OR name = ''
                """))
                
                records_to_fix = result.fetchall()
                
                if not records_to_fix:
                    print("✅ No records need fixing")
                    return True
                
                print(f"📝 Found {len(records_to_fix)} records that need fixing")
                
                # Update records with proper default values
                for record in records_to_fix:
                    record_id = record[0]
                    current_email = record[1]
                    current_name = record[2]
                    
                    # Set better default values
                    new_email = current_email if current_email and current_email != 'unknown@example.com' else f'legacy_user_{record_id}@lawvriksh.com'
                    new_name = current_name if current_name and current_name != 'Unknown User' else f'Legacy User {record_id}'
                    
                    conn.execute(text("""
                        UPDATE feedback 
                        SET email = :email, name = :name 
                        WHERE id = :id
                    """), {
                        'email': new_email,
                        'name': new_name,
                        'id': record_id
                    })
                    
                    print(f"   ✅ Fixed record {record_id}: {new_name} ({new_email})")
                
                # Commit transaction
                trans.commit()
                print("✅ All existing records fixed successfully!")
                
                # Verify the fix
                print("\n📊 Verifying fix...")
                result = conn.execute(text("""
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN email IS NULL OR email = '' THEN 1 END) as null_emails,
                           COUNT(CASE WHEN name IS NULL OR name = '' THEN 1 END) as null_names
                    FROM feedback
                """))
                
                stats = result.fetchone()
                print(f"   Total records: {stats[0]}")
                print(f"   Records with null/empty email: {stats[1]}")
                print(f"   Records with null/empty name: {stats[2]}")
                
                if stats[1] == 0 and stats[2] == 0:
                    print("✅ All records now have valid email and name fields!")
                else:
                    print("⚠️ Some records still have missing data")
                
            except Exception as e:
                trans.rollback()
                raise e
                
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    fix_existing_records()
