#!/usr/bin/env python3
"""
MySQL Database Setup Script for Lawvriksh Backend
This script sets up the MySQL database using the lawdata.sql file.
"""

import sys
import os
import subprocess
from pathlib import Path
import getpass

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def check_mysql_client():
    """Check if MySQL client is available."""
    print("🔄 Checking MySQL client availability...")
    
    try:
        result = subprocess.run(['mysql', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ MySQL client found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ MySQL client not found. Please install MySQL client.")
        print("   Download from: https://dev.mysql.com/downloads/mysql/")
        return False

def test_mysql_connection(host, port, user, password):
    """Test MySQL connection."""
    print(f"🔄 Testing MySQL connection to {user}@{host}:{port}...")
    
    try:
        import pymysql
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL connection successful. Version: {version[0]}")
        
        connection.close()
        return True
        
    except ImportError:
        print("❌ PyMySQL not installed. Installing...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pymysql'], check=True)
            print("✅ PyMySQL installed successfully")
            return test_mysql_connection(host, port, user, password)
        except subprocess.CalledProcessError:
            print("❌ Failed to install PyMySQL")
            return False
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        return False

def execute_sql_file(host, port, user, password, sql_file):
    """Execute SQL file using MySQL client."""
    print(f"🔄 Executing SQL file: {sql_file}")
    
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        return False
    
    try:
        # Build MySQL command
        cmd = [
            'mysql',
            f'--host={host}',
            f'--port={port}',
            f'--user={user}',
            f'--password={password}',
            '--default-character-set=utf8mb4'
        ]
        
        # Execute SQL file
        with open(sql_file, 'r', encoding='utf-8') as f:
            result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ SQL file executed successfully")
            if result.stdout:
                print(f"   Output: {result.stdout}")
            return True
        else:
            print(f"❌ SQL execution failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error executing SQL file: {e}")
        return False

def verify_database_setup():
    """Verify that the database was set up correctly."""
    print("🔄 Verifying database setup...")
    
    try:
        from app.core.config import settings
        from app.core.dependencies import engine
        from sqlalchemy import text
        
        # Test connection
        with engine.connect() as conn:
            # Check if tables exist
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = ['users', 'share_events']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            
            print(f"✅ All tables found: {tables}")
            
            # Check sample data
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            print(f"✅ Sample users: {user_count}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM share_events"))
            share_count = result.fetchone()[0]
            print(f"✅ Sample share events: {share_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

def main():
    """Main function."""
    print("🚀 Lawvriksh MySQL Database Setup")
    print("=" * 40)
    
    # Check MySQL client
    if not check_mysql_client():
        print("\n💡 Alternative: You can manually execute the SQL file:")
        print(f"   mysql -u root -p < {backend_dir}/lawdata.sql")
        return
    
    # Get MySQL connection details
    print("\n📋 MySQL Connection Details")
    host = input("MySQL Host (default: localhost): ").strip() or "localhost"
    port = int(input("MySQL Port (default: 3306): ").strip() or "3306")
    user = input("MySQL User (default: root): ").strip() or "root"
    password = getpass.getpass("MySQL Password: ")
    
    # Test connection
    if not test_mysql_connection(host, port, user, password):
        print("❌ Cannot connect to MySQL. Please check your credentials and server status.")
        return
    
    # Execute SQL file
    sql_file = backend_dir / "lawdata.sql"
    if not execute_sql_file(host, port, user, password, sql_file):
        print("❌ Failed to execute SQL file")
        return
    
    # Verify setup
    print("\n🔄 Verifying application configuration...")
    if verify_database_setup():
        print("\n🎉 MySQL database setup complete!")
        print("\n📋 What was created:")
        print("   ✅ Database: lawvriksh_referral")
        print("   ✅ User: lawuser@% (password: Sahil@123)")
        print("   ✅ Tables: users, share_events")
        print("   ✅ Sample data: 5 users, 10 share events")
        print("   ✅ Stored procedures and triggers")
        print("   ✅ Views for statistics")
        
        print("\n🚀 Next steps:")
        print("   1. Start the application: uvicorn app.main:app --reload")
        print("   2. Access API docs: http://localhost:8000/docs")
        print("   3. Login as admin: admin@lawvriksh.com / password123")
    else:
        print("\n⚠️  Database setup completed but verification failed.")
        print("   The database may still be functional. Try starting the application.")

if __name__ == "__main__":
    main()
