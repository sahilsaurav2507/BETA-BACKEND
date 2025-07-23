#!/usr/bin/env python3
"""
Email System Test Script
========================

This script tests the email functionality to identify why emails aren't being sent during user registration.
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.services.email_service import send_welcome_email, send_email
from app.services.email_campaign_service import send_welcome_email_campaign

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_email_configuration():
    """Test email configuration settings."""
    print("🔧 TESTING EMAIL CONFIGURATION")
    print("=" * 50)
    
    print(f"EMAIL_FROM: {settings.EMAIL_FROM}")
    print(f"SMTP_HOST: {settings.SMTP_HOST}")
    print(f"SMTP_PORT: {settings.SMTP_PORT}")
    print(f"SMTP_USER: {settings.SMTP_USER}")
    print(f"SMTP_PASSWORD: {'*' * len(settings.SMTP_PASSWORD) if settings.SMTP_PASSWORD else 'NOT SET'}")
    
    # Check if required settings are configured
    missing_settings = []
    if not settings.EMAIL_FROM:
        missing_settings.append("EMAIL_FROM")
    if not settings.SMTP_HOST:
        missing_settings.append("SMTP_HOST")
    if not settings.SMTP_USER:
        missing_settings.append("SMTP_USER")
    if not settings.SMTP_PASSWORD:
        missing_settings.append("SMTP_PASSWORD")
    
    if missing_settings:
        print(f"❌ Missing email settings: {', '.join(missing_settings)}")
        return False
    else:
        print("✅ All email settings are configured")
        return True

def test_smtp_connection():
    """Test SMTP connection without sending email."""
    print("\n🔌 TESTING SMTP CONNECTION")
    print("=" * 50)
    
    try:
        import smtplib
        
        print(f"Connecting to {settings.SMTP_HOST}:{settings.SMTP_PORT}...")
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            print("✅ SMTP connection established")
            
            print("Starting TLS...")
            server.starttls()
            print("✅ TLS started successfully")
            
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                print("Attempting login...")
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                print("✅ SMTP authentication successful")
            else:
                print("⚠️ No SMTP credentials provided")
                
        return True
        
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False

def test_send_welcome_email():
    """Test sending a welcome email."""
    print("\n📧 TESTING WELCOME EMAIL SENDING")
    print("=" * 50)
    
    test_email = "test@example.com"
    test_name = "Test User"
    
    try:
        print(f"Sending welcome email to {test_email}...")
        send_welcome_email(test_email, test_name)
        print("✅ Welcome email sent successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to send welcome email: {e}")
        return False

def test_send_campaign_email():
    """Test sending a campaign email."""
    print("\n🎯 TESTING CAMPAIGN EMAIL SENDING")
    print("=" * 50)
    
    test_email = "test@example.com"
    test_name = "Test User"
    
    try:
        print(f"Sending campaign email to {test_email}...")
        send_welcome_email_campaign(test_email, test_name)
        print("✅ Campaign email sent successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to send campaign email: {e}")
        return False

def test_user_registration_flow():
    """Test the complete user registration flow including email."""
    print("\n👤 TESTING USER REGISTRATION FLOW")
    print("=" * 50)
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Test user data
        test_user = {
            "name": "Email Test User",
            "email": f"emailtest{os.urandom(4).hex()}@example.com",
            "password": "testpassword123"
        }
        
        print(f"Registering user: {test_user['email']}")
        
        # Make registration request
        response = requests.post(f"{base_url}/auth/signup", json=test_user)
        
        print(f"Registration response status: {response.status_code}")
        
        if response.status_code == 201:
            user_data = response.json()
            print(f"✅ User registered successfully: ID={user_data['user_id']}")
            print("📧 Check if welcome email was sent (check logs above)")
            return True
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
        return False

def main():
    """Run all email tests."""
    print("🚀 EMAIL SYSTEM DIAGNOSTIC")
    print("=" * 50)
    
    tests = [
        ("Email Configuration", test_email_configuration),
        ("SMTP Connection", test_smtp_connection),
        ("Welcome Email", test_send_welcome_email),
        ("Campaign Email", test_send_campaign_email),
        ("Registration Flow", test_user_registration_flow),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All email tests passed!")
    else:
        print("⚠️ Some email tests failed. Check the issues above.")
        
        # Provide troubleshooting suggestions
        print("\n💡 TROUBLESHOOTING SUGGESTIONS:")
        print("1. Check your .env file has correct email settings")
        print("2. For Gmail: Use App Password, not regular password")
        print("3. Ensure 2FA is enabled for Gmail")
        print("4. Check firewall/antivirus blocking SMTP connections")
        print("5. Try different SMTP provider (Hostinger, Outlook, etc.)")

if __name__ == "__main__":
    main()
