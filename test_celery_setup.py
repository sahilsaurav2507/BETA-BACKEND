#!/usr/bin/env python3
"""
Test Celery + RabbitMQ Setup
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

def test_rabbitmq_connection():
    """Test RabbitMQ connection"""
    print("🐰 Testing RabbitMQ connection...")
    try:
        import kombu
        connection = kombu.Connection('amqp://guest:guest@localhost:5672//')
        connection.connect()
        print("✅ RabbitMQ connection successful!")
        connection.close()
        return True
    except Exception as e:
        print(f"❌ RabbitMQ connection failed: {e}")
        return False

def test_celery_import():
    """Test Celery task import"""
    print("\n📦 Testing Celery task import...")
    try:
        from app.tasks.email_tasks import send_5_minute_welcome_email_task, check_and_send_scheduled_campaigns_task
        print("✅ Celery tasks imported successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to import Celery tasks: {e}")
        return False

def test_celery_task():
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
    print("🧪 Celery + RabbitMQ Setup Test")
    print("=" * 50)
    
    tests = [
        test_rabbitmq_connection,
        test_celery_import,
        test_email_campaign_service,
        test_celery_task,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Celery + RabbitMQ setup is ready!")
        print("\n📋 Next steps:")
        print("1. Start RabbitMQ (if not already running)")
        print("2. Start Celery worker: start_celery_worker.bat")
        print("3. Start Celery beat: start_celery_beat.bat")
        print("4. Test user registration")
    else:
        print("❌ Some tests failed. Please check the setup.")
        if not test_rabbitmq_connection():
            print("\n🔧 To fix RabbitMQ:")
            print("- Install RabbitMQ from: https://www.rabbitmq.com/download.html")
            print("- Or run with Docker: start_rabbitmq_docker.bat")

if __name__ == "__main__":
    main()
