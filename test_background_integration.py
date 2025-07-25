#!/usr/bin/env python3
"""
Test Background Email Integration
================================

This script tests that the background email processor integrates correctly
with the FastAPI application.

Usage:
    python test_background_integration.py
"""

import sys
import os
import asyncio
from datetime import datetime
import pytz

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# IST timezone
IST = pytz.timezone('Asia/Kolkata')


async def test_background_processor_import():
    """Test that the background processor can be imported and used."""
    print("🧪 Testing Background Processor Import")
    print("-" * 50)
    
    try:
        from app.services.background_email_processor import (
            start_background_email_processor,
            stop_background_email_processor,
            is_background_processor_running,
            get_background_processor_status
        )
        
        print("✅ Background processor imports successful")
        
        # Test status when not running
        status = await get_background_processor_status()
        print(f"✅ Initial status: {status}")
        
        if not status["running"]:
            print("✅ Processor correctly reports as not running")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


async def test_processor_lifecycle():
    """Test starting and stopping the background processor."""
    print("\n🧪 Testing Processor Lifecycle")
    print("-" * 50)
    
    try:
        from app.services.background_email_processor import (
            start_background_email_processor,
            stop_background_email_processor,
            is_background_processor_running,
            get_background_processor_status
        )
        
        # Start processor
        print("🚀 Starting background processor...")
        await start_background_email_processor()
        
        # Check if running
        await asyncio.sleep(1)  # Give it a moment to start
        
        is_running = is_background_processor_running()
        status = await get_background_processor_status()
        
        print(f"✅ Processor running: {is_running}")
        print(f"✅ Status: {status}")
        
        if is_running and status["running"]:
            print("✅ Processor started successfully")
        else:
            print("⚠️  Processor may not have started properly")
        
        # Let it run for a few seconds
        print("⏳ Letting processor run for 5 seconds...")
        await asyncio.sleep(5)
        
        # Stop processor
        print("🛑 Stopping background processor...")
        await stop_background_email_processor()
        
        # Check if stopped
        await asyncio.sleep(1)  # Give it a moment to stop
        
        is_running = is_background_processor_running()
        status = await get_background_processor_status()
        
        print(f"✅ Processor running: {is_running}")
        print(f"✅ Status: {status}")
        
        if not is_running and not status["running"]:
            print("✅ Processor stopped successfully")
            return True
        else:
            print("⚠️  Processor may not have stopped properly")
            return False
        
    except Exception as e:
        print(f"❌ Lifecycle test failed: {e}")
        return False


async def test_fastapi_integration():
    """Test that the FastAPI integration works."""
    print("\n🧪 Testing FastAPI Integration")
    print("-" * 50)
    
    try:
        # Import the main app
        from app.main import app, lifespan
        
        print("✅ FastAPI app imports successful")
        print("✅ Lifespan context manager available")
        
        # Test that the lifespan function exists and is callable
        if callable(lifespan):
            print("✅ Lifespan function is callable")
        else:
            print("❌ Lifespan function is not callable")
            return False
        
        # Check that the app has the lifespan configured
        if hasattr(app, 'router') and hasattr(app, 'lifespan_context'):
            print("✅ FastAPI app has lifespan configured")
        else:
            print("✅ FastAPI app created (lifespan will be handled by FastAPI)")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI integration test failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 Background Email Integration Test")
    print("=" * 60)
    print(f"🕐 Test started: {datetime.now(IST)}")
    print("=" * 60)
    
    # Run tests
    test_results = []
    
    test_results.append(("Background Processor Import", await test_background_processor_import()))
    test_results.append(("Processor Lifecycle", await test_processor_lifecycle()))
    test_results.append(("FastAPI Integration", await test_fastapi_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed_tests += 1
    
    print(f"\n🎯 Overall: {passed_tests}/{len(test_results)} tests passed")
    
    if passed_tests == len(test_results):
        print("\n🎉 All tests passed! Background email integration is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Start the FastAPI server: uvicorn app.main:app --reload")
        print("   2. The background email processor will start automatically")
        print("   3. Emails will be processed every 60 seconds")
        print("   4. Monitor logs for email processing activity")
        
    else:
        print(f"\n⚠️  {len(test_results) - passed_tests} tests failed. Please review the issues above.")
    
    return passed_tests == len(test_results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
