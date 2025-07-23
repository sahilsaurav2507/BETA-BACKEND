#!/usr/bin/env python3
"""
Manual Welcome Email Sender
============================

This script manually sends welcome emails to users who registered before the email system was fixed.
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.services.email_campaign_service import send_welcome_email_campaign

def send_welcome_to_user(email, name):
    """Send welcome email to a specific user."""
    try:
        print(f"Sending welcome email to {name} ({email})...")
        send_welcome_email_campaign(email, name)
        print("✅ Welcome email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send welcome email: {e}")
        return False

def main():
    """Send welcome email to Prabhjot."""
    print("🚀 MANUAL WELCOME EMAIL SENDER")
    print("=" * 50)
    
    # User details
    user_email = "prabhjotjaswal11@gmail.com"
    user_name = "Prabhjot1223"
    
    print(f"Sending welcome email to: {user_name}")
    print(f"Email address: {user_email}")
    print()
    
    success = send_welcome_to_user(user_email, user_name)
    
    if success:
        print("\n🎉 Welcome email sent successfully!")
        print("The user should receive the email shortly.")
    else:
        print("\n❌ Failed to send welcome email.")
        print("Please check the email configuration and try again.")

if __name__ == "__main__":
    main()
