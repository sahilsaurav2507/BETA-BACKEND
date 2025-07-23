#!/usr/bin/env python3
"""
MySQL Database initialization script for Lawvriksh backend.
This script creates all database tables and optionally creates an admin user.
Requires MySQL server to be running and configured.
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def init_database():
    """Initialize the database with all tables."""
    print("🔄 Initializing database...")
    
    try:
        from app.core.dependencies import engine
        from app.core.database import Base
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Import all models to ensure they're registered
        from app.models import user, share  # This ensures all models are loaded
        
        print("✅ All models loaded successfully")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    
    return True

def create_admin_user():
    """Create an admin user if it doesn't exist."""
    print("🔄 Creating admin user...")
    
    try:
        from app.core.dependencies import get_db
        from app.models.user import User
        from passlib.context import CryptContext
        
        # Get database session
        db = next(get_db())
        
        # Check if admin user already exists
        admin_email = "admin@lawvriksh.com"
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        
        if existing_admin:
            print(f"ℹ️  Admin user already exists: {admin_email}")
            return True
        
        # Create password context
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Create admin user
        admin_user = User(
            name="Admin User",
            email=admin_email,
            password_hash=pwd_context.hash("admin123"),  # Change this password!
            is_admin=True,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Email: {admin_email}")
        print(f"   Password: admin123 (Please change this!)")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    
    return True

def main():
    """Main function."""
    print("🚀 Lawvriksh Database Initialization")
    print("=" * 40)
    
    # Initialize database
    if not init_database():
        print("\n❌ Database initialization failed!")
        sys.exit(1)
    
    # Ask if user wants to create admin user
    create_admin = input("\n❓ Do you want to create an admin user? (y/N): ").lower().strip()
    
    if create_admin in ['y', 'yes']:
        if not create_admin_user():
            print("\n⚠️  Admin user creation failed, but database is initialized.")
    
    print("\n🎉 Database initialization complete!")
    print("\nYou can now start the application with:")
    print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main()
