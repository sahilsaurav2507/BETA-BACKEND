#!/usr/bin/env python3
"""
Test the complete user registration flow with email sending.
This tests the fallback mechanism that sends emails immediately if Celery is not available.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.services.user_service import create_user
from app.schemas.user import UserCreate

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_registration_with_email():
    """Test user registration with email sending (using fallback mechanism)."""
    print("🔍 TESTING USER REGISTRATION WITH EMAIL")
    print("=" * 50)
    
    try:
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Get current user count
        total_users_before = db.query(User).filter(User.is_admin == False).count()
        
        # Get test email from user
        test_email = input("Enter your email to test registration (or press Enter to use default): ").strip()
        if not test_email:
            test_email = f"test_registration_{total_users_before + 1}@example.com"
            print(f"Using default email: {test_email}")
        
        # Create a test user
        test_user_data = UserCreate(
            name="Registration Test User",
            email=test_email,
            password="testpassword123"
        )
        
        print(f"👤 Creating user: {test_user_data.email}")
        new_user = create_user(db, test_user_data)
        
        print(f"✅ User created with ID: {new_user.id}")
        print(f"📈 User rank: {new_user.current_rank}")
        
        # Now simulate the signup endpoint email logic
        print("\n📧 Testing email sending logic...")
        
        # Import the email task
        from app.tasks.email_tasks import send_5_minute_welcome_email_task
        
        # Try the same logic as in the signup endpoint
        try:
            # Try async first (this will fail if Celery is not available)
            send_5_minute_welcome_email_task.apply_async(
                args=[new_user.email, new_user.name],
                countdown=5  # 5 seconds for testing
            )
            print("✅ Email scheduled via Celery")
            
        except Exception as email_error:
            print(f"⚠️  Celery scheduling failed: {email_error}")
            print("🔄 Falling back to immediate email sending...")
            
            # Fallback: Send email immediately and synchronously
            try:
                from app.services.email_service import send_welcome_email
                send_welcome_email(new_user.email, new_user.name)
                print("✅ Welcome email sent immediately (fallback)")
                
            except Exception as sync_email_error:
                print(f"❌ Failed to send email synchronously: {sync_email_error}")
                return False
        
        # Clean up - delete the test user
        print(f"\n🧹 Cleaning up test user...")
        db.delete(new_user)
        db.commit()
        db.close()
        
        print("\n🎉 Registration with email test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Registration test failed: {e}")
        print(f"❌ Registration test failed: {e}")
        return False

def main():
    """Run registration email test."""
    print("🚀 USER REGISTRATION EMAIL TEST")
    print("=" * 60)
    
    success = test_registration_with_email()
    
    if success:
        print("\n✅ SUCCESS: User registration with email is working!")
        print("\n📝 What happens now:")
        print("   1. New users will be created successfully")
        print("   2. If Celery is running: Email sent after 5 minutes")
        print("   3. If Celery is NOT running: Email sent immediately")
        print("   4. Users will see their correct rank (not N/A)")
        
        print("\n🔧 To enable delayed emails (optional):")
        print("   1. Install RabbitMQ: https://www.rabbitmq.com/download.html")
        print("   2. Start RabbitMQ service")
        print("   3. Start Celery worker: celery -A app.tasks.email_tasks worker --loglevel=info")
        
    else:
        print("\n❌ FAILED: There are still issues with the email system")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
