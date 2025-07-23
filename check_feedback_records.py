#!/usr/bin/env python3
"""
Check feedback records for missing email/name data
"""

import sys
import os
from sqlalchemy import create_engine, text

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def check_records():
    """Check for records with missing email/name data"""
    print("🔍 Checking feedback records...")
    
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Check all records
            result = conn.execute(text("SELECT id, email, name FROM feedback ORDER BY id"))
            records = result.fetchall()
            
            print(f"📊 Total records: {len(records)}")
            print("\n📋 All records:")
            
            problematic_records = []
            
            for record in records:
                record_id, email, name = record
                status = "✅"
                
                if not email or email == "" or email == "unknown@example.com":
                    status = "❌"
                    problematic_records.append(record_id)
                elif not name or name == "" or name == "Unknown User":
                    status = "❌"
                    problematic_records.append(record_id)
                
                print(f"   {status} ID {record_id}: email=\"{email}\", name=\"{name}\"")
            
            if problematic_records:
                print(f"\n⚠️ Found {len(problematic_records)} problematic records: {problematic_records}")
                return False
            else:
                print("\n✅ All records have valid email and name data!")
                return True
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_records()
