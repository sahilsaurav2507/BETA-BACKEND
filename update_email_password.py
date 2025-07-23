#!/usr/bin/env python3
"""
Update Email Password in .env File
==================================

This script helps you securely update the SMTP password in your .env file.
"""

import getpass
import os

def update_smtp_password():
    """Update SMTP password in .env file."""
    
    print("🔧 Hostinger Email Password Update")
    print("=" * 40)
    print("Current configuration:")
    print("  Email: info@lawvriksh.com")
    print("  SMTP Host: smtp.hostinger.com")
    print("  SMTP Port: 587")
    print()
    
    # Get password securely
    print("Please enter the password for info@lawvriksh.com")
    print("(You can find this in your Hostinger cPanel → Email Accounts)")
    password = getpass.getpass("Enter password: ")
    
    if not password:
        print("❌ No password entered. Exiting.")
        return False
    
    try:
        # Read current .env file
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        # Update SMTP_PASSWORD line
        updated_lines = []
        password_updated = False
        
        for line in lines:
            if line.startswith('SMTP_PASSWORD='):
                updated_lines.append(f'SMTP_PASSWORD={password}\n')
                password_updated = True
                print("✅ SMTP_PASSWORD updated")
            else:
                updated_lines.append(line)
        
        if not password_updated:
            # Add SMTP_PASSWORD if it doesn't exist
            updated_lines.append(f'SMTP_PASSWORD={password}\n')
            print("✅ SMTP_PASSWORD added")
        
        # Write updated .env file
        with open('.env', 'w') as f:
            f.writelines(updated_lines)
        
        print("✅ .env file updated successfully!")
        print()
        print("📧 Now testing email delivery...")
        
        # Test email delivery
        import subprocess
        result = subprocess.run(['python', 'test_email_simple.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("🎉 Email test successful!")
            print("📧 Check sahilsaurav2507@gmail.com for the test email")
        else:
            print("❌ Email test failed:")
            print(result.stdout)
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def main():
    """Main function."""
    success = update_smtp_password()
    
    if success:
        print("\n🎉 Email system is now configured!")
        print("📋 Next steps:")
        print("1. Check sahilsaurav2507@gmail.com for test email")
        print("2. Run: python test_sahil_registration_flow.py")
        print("3. Sahil will now receive welcome emails!")
    else:
        print("\n❌ Email configuration failed")
        print("Please check your Hostinger email password and try again")

if __name__ == "__main__":
    main()
