#!/usr/bin/env python3
"""
LawVriksh Email System Startup Script
====================================

This script helps you set up and start the email queue system.
It will guide you through the setup process and start the email processor.

Usage:
    python start_email_system.py [--setup-only] [--start-only]
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def check_database_connection():
    """Check if database connection is working."""
    try:
        from app.core.config import settings
        from sqlalchemy import create_engine, text
        
        print("🔍 Checking database connection...")
        
        if settings.DATABASE_URL:
            engine = create_engine(settings.DATABASE_URL)
        else:
            database_url = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            engine = create_engine(database_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def check_email_queue_table():
    """Check if email_queue table exists."""
    try:
        from app.core.config import settings
        from sqlalchemy import create_engine, text
        
        print("🔍 Checking email_queue table...")
        
        if settings.DATABASE_URL:
            engine = create_engine(settings.DATABASE_URL)
        else:
            database_url = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            engine = create_engine(database_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES LIKE 'email_queue'"))
            table_exists = result.fetchone() is not None
        
        if table_exists:
            print("✅ email_queue table exists")
            return True
        else:
            print("❌ email_queue table not found")
            return False
        
    except Exception as e:
        print(f"❌ Error checking email_queue table: {e}")
        return False


def run_database_migration():
    """Run the email queue database migration."""
    print("🔄 Running email queue database migration...")
    
    migration_file = Path("BETA-SQL/add_email_queue.sql")
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    try:
        from app.core.config import settings
        
        # Construct mysql command
        if settings.DATABASE_URL:
            # Parse DATABASE_URL
            import urllib.parse
            parsed = urllib.parse.urlparse(settings.DATABASE_URL)
            host = parsed.hostname
            port = parsed.port or 3306
            username = parsed.username
            password = parsed.password
            database = parsed.path.lstrip('/')
        else:
            host = settings.DB_HOST
            port = settings.DB_PORT
            username = settings.DB_USER
            password = settings.DB_PASSWORD
            database = settings.DB_NAME
        
        # Run mysql command
        cmd = [
            "mysql",
            f"-h{host}",
            f"-P{port}",
            f"-u{username}",
            f"-p{password}",
            database
        ]
        
        print(f"Running: mysql -h{host} -P{port} -u{username} -p*** {database} < {migration_file}")
        
        with open(migration_file, 'r') as f:
            result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database migration completed successfully")
            return True
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
        
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        print("\n💡 You can manually run the migration:")
        print(f"   mysql -u your_user -p your_database < {migration_file}")
        return False


def test_email_queue():
    """Test the email queue system."""
    print("🧪 Testing email queue system...")
    
    try:
        result = subprocess.run([sys.executable, "test_email_queue.py"], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Email queue tests passed")
            return True
        else:
            print(f"❌ Email queue tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
        
    except subprocess.TimeoutExpired:
        print("❌ Email queue tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def start_email_processor(daemon=True):
    """Start the email processor."""
    print("🚀 Starting email processor...")
    
    try:
        cmd = [sys.executable, "email_processor.py"]
        
        if daemon:
            cmd.extend(["--daemon", "--interval", "30", "--batch-size", "5"])
            print("Starting email processor as daemon...")
            
            # Start as background process
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if it's still running
            if process.poll() is None:
                print(f"✅ Email processor started successfully (PID: {process.pid})")
                print("📝 Logs are written to: email_processor.log")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Email processor failed to start:")
                print(stdout.decode())
                print(stderr.decode())
                return False
        else:
            cmd.extend(["--batch-size", "10"])
            print("Running single batch...")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Email processor batch completed")
                print(result.stdout)
                return True
            else:
                print(f"❌ Email processor batch failed:")
                print(result.stderr)
                return False
        
    except Exception as e:
        print(f"❌ Error starting email processor: {e}")
        return False


def setup_email_system():
    """Set up the email queue system."""
    print("🔧 Setting up Email Queue System")
    print("=" * 40)
    
    # Check database connection
    if not check_database_connection():
        print("\n❌ Setup failed: Database connection issue")
        return False
    
    # Check if email_queue table exists
    if not check_email_queue_table():
        print("\n🔄 Email queue table not found, running migration...")
        if not run_database_migration():
            print("\n❌ Setup failed: Migration issue")
            return False
    
    # Test email queue system
    if not test_email_queue():
        print("\n⚠️  Setup completed but tests failed")
        print("You may need to check your configuration")
        return True  # Continue anyway
    
    print("\n✅ Email queue system setup completed successfully!")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='LawVriksh Email System Startup')
    parser.add_argument('--setup-only', action='store_true', help='Only run setup, don\'t start processor')
    parser.add_argument('--start-only', action='store_true', help='Only start processor, skip setup')
    parser.add_argument('--single-batch', action='store_true', help='Run single batch instead of daemon')
    
    args = parser.parse_args()
    
    print("🚀 LawVriksh Email Queue System")
    print("=" * 50)
    
    # Setup phase
    if not args.start_only:
        if not setup_email_system():
            print("\n❌ Setup failed!")
            sys.exit(1)
    
    # Start phase
    if not args.setup_only:
        print("\n🚀 Starting Email Processor")
        print("-" * 30)
        
        daemon_mode = not args.single_batch
        if start_email_processor(daemon=daemon_mode):
            if daemon_mode:
                print("\n🎉 Email system is now running!")
                print("\nMonitoring commands:")
                print("  python email_queue_monitor.py status")
                print("  python email_queue_monitor.py pending")
                print("  tail -f email_processor.log")
            else:
                print("\n✅ Single batch completed successfully!")
        else:
            print("\n❌ Failed to start email processor!")
            sys.exit(1)


if __name__ == "__main__":
    main()
