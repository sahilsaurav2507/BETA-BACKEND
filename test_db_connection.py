#!/usr/bin/env python3
"""
MySQL Database Connection Test Script for Lawvriksh Backend
This script tests MySQL database connectivity and provides detailed diagnostics.
"""

import sys
import os
from pathlib import Path
import traceback
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_config_loading():
    """Test if configuration loads correctly."""
    print("🔄 Testing configuration loading...")
    
    try:
        from app.core.config import settings
        print(f"✅ Configuration loaded successfully")
        print(f"   Database URL: {settings.database_url}")
        print(f"   Environment: {getattr(settings, 'ENVIRONMENT', 'not set')}")
        return settings
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        traceback.print_exc()
        return None

def test_database_engine():
    """Test database engine creation."""
    print("\n🔄 Testing database engine creation...")
    
    try:
        from app.core.dependencies import engine
        print(f"✅ Database engine created successfully")
        print(f"   Engine: {engine}")
        print(f"   URL: {engine.url}")
        print(f"   Driver: {engine.url.drivername}")
        return engine
    except Exception as e:
        print(f"❌ Database engine creation failed: {e}")
        traceback.print_exc()
        return None

def test_database_connection(engine):
    """Test actual database connection."""
    print("\n🔄 Testing database connection...")
    
    try:
        # Test connection
        with engine.connect() as connection:
            print("✅ Database connection successful")
            
            # Test a simple query
            from sqlalchemy import text
            result = connection.execute(text("SELECT 1 as test"))
            
            row = result.fetchone()
            print(f"✅ Test query successful: {row}")
            
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        traceback.print_exc()
        return False

def test_session_creation():
    """Test database session creation."""
    print("\n🔄 Testing database session creation...")
    
    try:
        from app.core.dependencies import get_db
        
        # Test session creation
        db_gen = get_db()
        db = next(db_gen)
        
        print("✅ Database session created successfully")
        print(f"   Session: {db}")
        
        # Close the session
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database session creation failed: {e}")
        traceback.print_exc()
        return False

def test_table_creation():
    """Test table creation."""
    print("\n🔄 Testing table creation...")
    
    try:
        from app.core.dependencies import engine
        from app.core.database import Base
        
        # Import all models to ensure they're registered
        from app.models import user, share
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"   Tables: {tables}")
        
        return True
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        traceback.print_exc()
        return False

def test_mysql_connection(host="localhost", port=3306, user="lawuser", password="example_pw", database="lawvriksh"):
    """Test MySQL connection specifically."""
    print(f"\n🔄 Testing MySQL connection to {user}@{host}:{port}/{database}...")
    
    try:
        import pymysql
        
        # Test MySQL connection
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        print("✅ MySQL connection successful")
        
        # Test query
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"✅ MySQL test query successful: {result}")
        
        connection.close()
        return True
        
    except ImportError:
        print("⚠️  PyMySQL not installed. Install with: pip install pymysql")
        return False
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        print("   Possible issues:")
        print("   - MySQL server not running")
        print("   - Incorrect credentials")
        print("   - Database doesn't exist")
        print("   - Firewall blocking connection")
        return False

def check_mysql_server():
    """Check if MySQL server is accessible."""
    print("\n🔄 Checking MySQL server accessibility...")

    try:
        settings = test_config_loading()
        if not settings:
            return False

        if 'mysql' not in settings.database_url:
            print("⚠️  Not using MySQL database")
            return False

        # Extract connection details from DATABASE_URL
        import re
        match = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', settings.database_url)
        if match:
            user, password, host, port, database = match.groups()
            return test_mysql_connection(host, int(port), user, password, database)
        else:
            print("❌ Could not parse MySQL connection string")
            return False

    except Exception as e:
        print(f"❌ MySQL server check failed: {e}")
        return False

def main():
    """Main function to run all tests."""
    print("🚀 Lawvriksh Database Connection Test")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Python Path: {sys.path[0]}")
    
    # Test configuration
    settings = test_config_loading()
    if not settings:
        return
    
    # Check if using MySQL
    if 'mysql' in settings.database_url:
        mysql_ok = check_mysql_server()
        if not mysql_ok:
            print("⚠️  MySQL server check failed, but continuing with other tests...")
    else:
        print("⚠️  Not using MySQL database")
    
    # Test engine creation
    engine = test_database_engine()
    if not engine:
        return
    
    # Test connection
    connection_ok = test_database_connection(engine)
    if not connection_ok:
        return
    
    # Test session creation
    session_ok = test_session_creation()
    if not session_ok:
        return
    
    # Test table creation
    tables_ok = test_table_creation()
    
    # If using MySQL, test direct MySQL connection
    if 'mysql' in settings.database_url:
        test_mysql_connection()
    
    print("\n" + "=" * 50)
    if connection_ok and session_ok and tables_ok:
        print("🎉 All database tests passed!")
        print("✅ Your database connection is working correctly")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n📋 Summary:")
    print(f"   Database Type: {'MySQL' if 'mysql' in settings.database_url else 'Other'}")
    print(f"   Database URL: {settings.database_url}")
    print(f"   Connection: {'✅ OK' if connection_ok else '❌ Failed'}")
    print(f"   Sessions: {'✅ OK' if session_ok else '❌ Failed'}")
    print(f"   Tables: {'✅ OK' if tables_ok else '❌ Failed'}")

    if 'mysql' in settings.database_url:
        print("\n💡 MySQL Setup Tips:")
        print("   - Run 'python setup_mysql_db.py' to set up the database")
        print("   - Make sure MySQL server is running")
        print("   - Check credentials in .env file")

if __name__ == "__main__":
    main()
