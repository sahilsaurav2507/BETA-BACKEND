#!/usr/bin/env python3
"""
MySQL Setup and Connection Test Script for Lawvriksh Backend
This script helps you set up and test MySQL database connection.
"""

import sys
import os
from pathlib import Path
import getpass

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_mysql_availability():
    """Test if MySQL server is available."""
    print("🔄 Testing MySQL server availability...")
    
    try:
        import pymysql
        print("✅ PyMySQL library is available")
    except ImportError:
        print("❌ PyMySQL not installed. Installing...")
        os.system("pip install pymysql")
        try:
            import pymysql
            print("✅ PyMySQL installed successfully")
        except ImportError:
            print("❌ Failed to install PyMySQL")
            return False
    
    return True

def test_mysql_connection(host, port, user, password, database=None):
    """Test MySQL connection with given parameters."""
    print(f"🔄 Testing connection to {user}@{host}:{port}" + (f"/{database}" if database else ""))
    
    try:
        import pymysql
        
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
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL version: {version[0]}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        return False

def create_database_and_user(host, port, admin_user, admin_password, db_name, db_user, db_password):
    """Create database and user."""
    print(f"🔄 Creating database '{db_name}' and user '{db_user}'...")
    
    try:
        import pymysql
        
        # Connect as admin
        connection = pymysql.connect(
            host=host,
            port=port,
            user=admin_user,
            password=admin_password
        )
        
        with connection.cursor() as cursor:
            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            print(f"✅ Database '{db_name}' created/verified")
            
            # Create user
            cursor.execute(f"CREATE USER IF NOT EXISTS '{db_user}'@'localhost' IDENTIFIED BY '{db_password}'")
            print(f"✅ User '{db_user}' created/verified")
            
            # Grant privileges
            cursor.execute(f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            print(f"✅ Privileges granted to '{db_user}' on '{db_name}'")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Database/user creation failed: {e}")
        return False

def update_env_file(database_url):
    """Update .env file with MySQL configuration."""
    print("🔄 Updating .env file...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    # Read current content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update DATABASE_URL
    updated_lines = []
    database_url_updated = False
    
    for line in lines:
        if line.startswith('DATABASE_URL='):
            updated_lines.append(f'DATABASE_URL={database_url}\n')
            database_url_updated = True
        elif line.startswith('# DATABASE_URL=mysql'):
            updated_lines.append(f'# DATABASE_URL=sqlite:///./lawvriksh.db\n')
        else:
            updated_lines.append(line)
    
    if not database_url_updated:
        updated_lines.append(f'DATABASE_URL={database_url}\n')
    
    # Write updated content
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print("✅ .env file updated successfully")
    return True

def main():
    """Main function for MySQL setup."""
    print("🚀 Lawvriksh MySQL Setup")
    print("=" * 40)
    
    # Test MySQL availability
    if not test_mysql_availability():
        return
    
    print("\n📋 MySQL Connection Setup")
    print("Please provide your MySQL connection details:")
    
    # Get connection details
    host = input("MySQL Host (default: localhost): ").strip() or "localhost"
    port = int(input("MySQL Port (default: 3306): ").strip() or "3306")
    
    print("\n🔐 Database Setup Options:")
    print("1. Use existing database and user")
    print("2. Create new database and user (requires admin access)")
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == "2":
        print("\n👤 Admin credentials (to create database and user):")
        admin_user = input("Admin username (default: root): ").strip() or "root"
        admin_password = getpass.getpass("Admin password: ")
        
        print("\n📊 New database details:")
        db_name = input("Database name (default: lawvriksh): ").strip() or "lawvriksh"
        db_user = input("Database user (default: lawuser): ").strip() or "lawuser"
        db_password = getpass.getpass("Database password: ")
        
        # Test admin connection
        if not test_mysql_connection(host, port, admin_user, admin_password):
            print("❌ Cannot connect with admin credentials")
            return
        
        # Create database and user
        if not create_database_and_user(host, port, admin_user, admin_password, db_name, db_user, db_password):
            return
        
    else:
        print("\n📊 Existing database details:")
        db_name = input("Database name: ").strip()
        db_user = input("Database user: ").strip()
        db_password = getpass.getpass("Database password: ")
    
    # Test connection with database user
    print(f"\n🔄 Testing connection with user '{db_user}'...")
    if not test_mysql_connection(host, port, db_user, db_password, db_name):
        print("❌ Cannot connect with database user credentials")
        return
    
    # Create DATABASE_URL
    database_url = f"mysql+pymysql://{db_user}:{db_password}@{host}:{port}/{db_name}"
    
    # Update .env file
    if update_env_file(database_url):
        print(f"\n🎉 MySQL setup complete!")
        print(f"Database URL: {database_url}")
        print("\n📋 Next steps:")
        print("1. Run: python init_db.py")
        print("2. Start the application: uvicorn app.main:app --reload")
    
    # Test the updated configuration
    print("\n🔄 Testing updated configuration...")
    try:
        # Reload configuration
        import importlib
        from app.core import config
        importlib.reload(config)
        
        from app.core.config import settings
        print(f"✅ New configuration loaded: {settings.database_url}")
        
        # Test connection with new config
        from app.core.dependencies import engine
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            print("✅ Connection test with new configuration successful")
        
    except Exception as e:
        print(f"⚠️  Configuration test failed: {e}")
        print("You may need to restart the application")

if __name__ == "__main__":
    main()
