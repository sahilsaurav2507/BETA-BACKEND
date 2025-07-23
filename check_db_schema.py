#!/usr/bin/env python3
"""
Database Schema Checker for Lawvriksh Backend
This script shows the current database schema and data.
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def main():
    """Check database schema and data."""
    print("📊 Lawvriksh Database Schema Check")
    print("=" * 40)
    
    try:
        from app.core.dependencies import engine
        from sqlalchemy import inspect, text
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"Database: {engine.url}")
        print(f"Tables found: {len(tables)}")
        print()
        
        for table in tables:
            print(f"📋 Table: {table}")
            
            # Get columns
            columns = inspector.get_columns(table)
            print("   Columns:")
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col['default'] else ""
                print(f"     - {col['name']} ({col['type']}) {nullable}{default}")
            
            # Get indexes
            indexes = inspector.get_indexes(table)
            if indexes:
                print("   Indexes:")
                for idx in indexes:
                    unique = "UNIQUE " if idx['unique'] else ""
                    print(f"     - {unique}{idx['name']}: {idx['column_names']}")
            
            # Count rows
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
                    count = result.fetchone()[0]
                    print(f"   Rows: {count}")
            except Exception as e:
                print(f"   Rows: Error counting - {e}")
            
            print()
        
        if not tables:
            print("⚠️  No tables found. Run 'python init_db.py' to create tables.")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
