#!/usr/bin/env python3
"""
Test Redis + Celery Setup for LawVriksh
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

def test_redis_connection():
    """Test Redis connection"""
    print("🔴 Testing Redis connection...")
    try:
        import redis
        # Try without password first (local development)
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis connection successful!")

        # Test basic operations
        r.set('test_key', 'LawVriksh Redis Test')
        value = r.get('test_key')
        print(f"✅ Redis read/write test: {value}")
        r.delete('test_key')

        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        # Try with password (production setup)
        try:
            r = redis.Redis(host='localhost', port=6379, password='Sahil@123', decode_responses=True)
            r.ping()
            print("✅ Redis connection successful (with password)!")
            return True
        except Exception as e2:
            print(f"❌ Redis connection failed (with password): {e2}")
            return False

def test_celery_with_redis():
    """Test Celery with Redis broker"""
    print("\n📦 Testing Celery with Redis...")
    try:
        from app.tasks.email_tasks import send_5_minute_welcome_email_task
        print("✅ Celery tasks imported successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to import Celery tasks: {e}")
        return False

def test_celery_task_execution():
    """Test sending a Celery task"""
    print("\n🚀 Testing Celery task execution...")
    try:
        from app.tasks.email_tasks import send_5_minute_welcome_email_task
        
        # Send a test task with 10-second delay
        task = send_5_minute_welcome_email_task.apply_async(
            args=["test@example.com", "Test User"],
            countdown=10  # 10-second delay for testing
        )
        
        print(f"✅ Task scheduled successfully! Task ID: {task.id}")
        print("📝 Note: Check Celery worker logs to see if the task executes")
        return True
    except Exception as e:
        print(f"❌ Failed to schedule Celery task: {e}")
        return False

def test_email_campaign_service():
    """Test email campaign service"""
    print("\n📧 Testing email campaign service...")
    try:
        from app.services.email_campaign_service import EMAIL_TEMPLATES
        print(f"✅ Found {len(EMAIL_TEMPLATES)} email templates:")
        for template_name in EMAIL_TEMPLATES.keys():
            print(f"   - {template_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to load email campaign service: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Redis + Celery Setup Test for LawVriksh")
    print("=" * 60)
    
    tests = [
        test_redis_connection,
        test_celery_with_redis,
        test_email_campaign_service,
        test_celery_task_execution,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Redis + Celery setup is ready!")
        print("\n📋 Next steps:")
        print("1. Start Redis: start_redis_docker.bat")
        print("2. Start Celery worker: start_celery_worker.bat")
        print("3. Start Celery beat: start_celery_beat.bat")
        print("4. Test user registration")
    else:
        print("❌ Some tests failed. Please check the setup.")
        if not test_redis_connection():
            print("\n🔧 To fix Redis:")
            print("- Install Redis or run with Docker: start_redis_docker.bat")
            print("- Make sure Redis is running on localhost:6379 with password 'Sahil@123'")

if __name__ == "__main__":
    main()
