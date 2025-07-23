#!/usr/bin/env python3
"""
Configuration validation script for Lawvriksh backend.
Run this script to validate your configuration before starting the application.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def validate_config():
    """Validate the application configuration."""
    print("🔍 Validating Lawvriksh configuration...")
    
    try:
        from app.core.config import settings
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    # Check database configuration
    try:
        db_url = settings.database_url
        print(f"✅ Database URL: {db_url[:20]}...")
    except Exception as e:
        print(f"❌ Database configuration error: {e}")
        return False
    
    # Check JWT secret key
    if len(settings.JWT_SECRET_KEY) < 32:
        print("⚠️  JWT_SECRET_KEY is too short (should be at least 32 characters)")
    elif settings.JWT_SECRET_KEY == "supersecretkey":
        print("⚠️  JWT_SECRET_KEY is using the default insecure value")
    else:
        print("✅ JWT_SECRET_KEY is properly configured")
    
    # Check SMTP configuration
    if not settings.SMTP_PASSWORD:
        print("⚠️  SMTP_PASSWORD is not set - email functionality may not work")
    else:
        print("✅ SMTP configuration appears complete")
    
    # Check cache directory
    cache_dir = Path(settings.CACHE_DIR)
    if not cache_dir.exists():
        print(f"⚠️  Cache directory {settings.CACHE_DIR} does not exist - will be created automatically")
    else:
        print(f"✅ Cache directory exists: {settings.CACHE_DIR}")
    
    # Check RabbitMQ URL
    if settings.RABBITMQ_URL:
        print(f"✅ RabbitMQ URL configured: {settings.RABBITMQ_URL}")
    else:
        print("⚠️  RabbitMQ URL not configured")
    
    print("\n🎉 Configuration validation complete!")
    return True

def main():
    """Main function."""
    if not validate_config():
        print("\n❌ Configuration validation failed!")
        print("Please check your .env file or environment variables.")
        sys.exit(1)
    
    print("\n✅ Configuration is valid!")
    print("You can now start the application with:")
    print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main()
