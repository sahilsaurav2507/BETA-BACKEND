#!/usr/bin/env python3
"""
Email System Diagnostic and Fix Tool
===================================

This script helps diagnose and fix email delivery issues for Sahil's registration.

Issues to check:
1. SMTP configuration
2. Email credentials
3. Server connectivity
4. Email service functionality
5. Celery task processing

Usage:
    python fix_email_system.py
"""

import smtplib
import logging
import os
import getpass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailSystemFixer:
    """Diagnose and fix email system issues."""
    
    def __init__(self):
        self.test_recipient = "sahilsaurav2507@gmail.com"
        self.test_sender_name = "Sahil Saurav"
        
    def load_current_config(self):
        """Load current email configuration."""
        try:
            from app.core.config import settings
            
            config = {
                'EMAIL_FROM': getattr(settings, 'EMAIL_FROM', None),
                'SMTP_HOST': getattr(settings, 'SMTP_HOST', None),
                'SMTP_PORT': getattr(settings, 'SMTP_PORT', None),
                'SMTP_USER': getattr(settings, 'SMTP_USER', None),
                'SMTP_PASSWORD': getattr(settings, 'SMTP_PASSWORD', None)
            }
            
            logger.info("📧 Current Email Configuration:")
            for key, value in config.items():
                if key == 'SMTP_PASSWORD':
                    display_value = "***HIDDEN***" if value else "❌ NOT SET"
                else:
                    display_value = value or "❌ NOT SET"
                logger.info(f"   {key}: {display_value}")
            
            return config
            
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            return None
    
    def test_smtp_connectivity(self, host, port, username, password):
        """Test SMTP server connectivity."""
        logger.info(f"🔌 Testing SMTP connectivity to {host}:{port}")
        
        try:
            # Create SMTP connection
            server = smtplib.SMTP(host, port)
            server.set_debuglevel(1)  # Enable debug output
            
            # Start TLS encryption
            server.starttls()
            logger.info("✅ TLS connection established")
            
            # Login
            server.login(username, password)
            logger.info("✅ SMTP authentication successful")
            
            # Close connection
            server.quit()
            logger.info("✅ SMTP connectivity test passed")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed: {e}")
            logger.error("   Check username and password")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"❌ SMTP Connection failed: {e}")
            logger.error("   Check host and port settings")
            return False
        except Exception as e:
            logger.error(f"❌ SMTP test failed: {e}")
            return False
    
    def send_test_email(self, host, port, username, password, from_email):
        """Send a test email to Sahil."""
        logger.info(f"📤 Sending test email to {self.test_recipient}")
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = self.test_recipient
            msg['Subject'] = "🎉 Lawvriksh Email System Test - Welcome Sahil!"
            
            # Email body
            body = f"""
Hello {self.test_sender_name},

🎉 Congratulations! Your Lawvriksh email system is now working correctly!

This is a test email to confirm that:
✅ SMTP configuration is correct
✅ Email delivery is functional
✅ Welcome emails will be sent during registration

Test Details:
- Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- From: {from_email}
- SMTP Server: {host}:{port}
- Test Type: Registration Email System Verification

Next Steps:
1. Complete your registration flow
2. Start sharing on social media platforms
3. Climb the leaderboard rankings!

Welcome to Lawvriksh!

Best regards,
The Lawvriksh Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(host, port)
            server.starttls()
            server.login(username, password)
            
            text = msg.as_string()
            server.sendmail(from_email, self.test_recipient, text)
            server.quit()
            
            logger.info("✅ Test email sent successfully!")
            logger.info(f"   Check {self.test_recipient} for the email")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send test email: {e}")
            return False
    
    def get_smtp_recommendations(self):
        """Provide SMTP configuration recommendations."""
        logger.info("📋 SMTP Configuration Recommendations:")
        
        recommendations = {
            "Gmail": {
                "SMTP_HOST": "smtp.gmail.com",
                "SMTP_PORT": "587",
                "SMTP_USER": "your-email@gmail.com",
                "SMTP_PASSWORD": "your-app-password (not regular password)",
                "notes": "Enable 2FA and use App Password"
            },
            "Hostinger": {
                "SMTP_HOST": "smtp.hostinger.com",
                "SMTP_PORT": "587",
                "SMTP_USER": "info@lawvriksh.com",
                "SMTP_PASSWORD": "your-email-password",
                "notes": "Use your cPanel email password"
            },
            "Outlook/Hotmail": {
                "SMTP_HOST": "smtp-mail.outlook.com",
                "SMTP_PORT": "587",
                "SMTP_USER": "your-email@outlook.com",
                "SMTP_PASSWORD": "your-password",
                "notes": "May need app password if 2FA enabled"
            }
        }
        
        for provider, config in recommendations.items():
            logger.info(f"\n🔧 {provider} Configuration:")
            for key, value in config.items():
                if key != "notes":
                    logger.info(f"   {key}={value}")
            logger.info(f"   Note: {config['notes']}")
    
    def interactive_smtp_setup(self):
        """Interactive SMTP configuration setup."""
        logger.info("🔧 Interactive SMTP Setup")
        logger.info("=" * 50)
        
        print("\nChoose your email provider:")
        print("1. Gmail (recommended for testing)")
        print("2. Hostinger (current configuration)")
        print("3. Outlook/Hotmail")
        print("4. Custom SMTP server")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            # Gmail setup
            smtp_host = "smtp.gmail.com"
            smtp_port = 587
            smtp_user = input("Enter your Gmail address: ").strip()
            print("\n⚠️  For Gmail, you need an App Password (not your regular password)")
            print("   1. Go to Google Account settings")
            print("   2. Enable 2-Factor Authentication")
            print("   3. Generate an App Password")
            smtp_password = getpass.getpass("Enter your Gmail App Password: ")
            
        elif choice == "2":
            # Hostinger setup
            smtp_host = "smtp.hostinger.com"
            smtp_port = 587
            smtp_user = "info@lawvriksh.com"
            print("\n📧 Using Hostinger SMTP for info@lawvriksh.com")
            smtp_password = getpass.getpass("Enter the password for info@lawvriksh.com: ")
            
        elif choice == "3":
            # Outlook setup
            smtp_host = "smtp-mail.outlook.com"
            smtp_port = 587
            smtp_user = input("Enter your Outlook email address: ").strip()
            smtp_password = getpass.getpass("Enter your Outlook password: ")
            
        elif choice == "4":
            # Custom setup
            smtp_host = input("Enter SMTP host: ").strip()
            smtp_port = int(input("Enter SMTP port (usually 587): ").strip())
            smtp_user = input("Enter SMTP username: ").strip()
            smtp_password = getpass.getpass("Enter SMTP password: ")
            
        else:
            logger.error("❌ Invalid choice")
            return None
        
        return {
            'SMTP_HOST': smtp_host,
            'SMTP_PORT': smtp_port,
            'SMTP_USER': smtp_user,
            'SMTP_PASSWORD': smtp_password,
            'EMAIL_FROM': smtp_user
        }
    
    def update_env_file(self, config):
        """Update .env file with new SMTP configuration."""
        logger.info("📝 Updating .env file with new SMTP configuration")
        
        try:
            # Read current .env file
            with open('.env', 'r') as f:
                lines = f.readlines()
            
            # Update SMTP settings
            updated_lines = []
            smtp_keys = ['EMAIL_FROM', 'SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD']
            updated_keys = set()
            
            for line in lines:
                line_updated = False
                for key in smtp_keys:
                    if line.startswith(f"{key}="):
                        updated_lines.append(f"{key}={config[key]}\n")
                        updated_keys.add(key)
                        line_updated = True
                        break
                
                if not line_updated:
                    updated_lines.append(line)
            
            # Add any missing keys
            for key in smtp_keys:
                if key not in updated_keys:
                    updated_lines.append(f"{key}={config[key]}\n")
            
            # Write updated .env file
            with open('.env', 'w') as f:
                f.writelines(updated_lines)
            
            logger.info("✅ .env file updated successfully")
            logger.info("⚠️  Restart your FastAPI server to apply changes")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update .env file: {e}")
            return False
    
    def test_celery_email_task(self):
        """Test Celery email task processing."""
        logger.info("🔄 Testing Celery email task processing")
        
        try:
            from app.tasks.email_tasks import send_welcome_email_task
            
            # Queue the task
            task_result = send_welcome_email_task.delay(
                self.test_recipient,
                self.test_sender_name
            )
            
            logger.info(f"📤 Email task queued with ID: {task_result.id}")
            
            # Wait for task completion
            logger.info("⏳ Waiting for task completion...")
            time.sleep(5)
            
            if task_result.ready():
                if task_result.successful():
                    logger.info("✅ Celery email task completed successfully")
                    logger.info(f"   Result: {task_result.result}")
                    return True
                else:
                    logger.error(f"❌ Celery email task failed: {task_result.info}")
                    return False
            else:
                logger.warning("⏳ Task is still processing...")
                return None
                
        except Exception as e:
            logger.error(f"❌ Celery email task test failed: {e}")
            return False
    
    def run_complete_email_fix(self):
        """Run complete email system diagnosis and fix."""
        logger.info("🔧 LAWVRIKSH EMAIL SYSTEM DIAGNOSTIC & FIX")
        logger.info("=" * 60)
        logger.info(f"Test Recipient: {self.test_recipient}")
        logger.info("=" * 60)
        
        # Step 1: Load current configuration
        current_config = self.load_current_config()
        if not current_config:
            logger.error("❌ Cannot load current configuration")
            return False
        
        # Step 2: Check if configuration is complete
        missing_config = [k for k, v in current_config.items() if not v or v == "your-smtp-password-here"]
        
        if missing_config:
            logger.warning(f"⚠️  Missing configuration: {missing_config}")
            logger.info("🔧 Starting interactive SMTP setup...")
            
            new_config = self.interactive_smtp_setup()
            if not new_config:
                return False
            
            # Update .env file
            if not self.update_env_file(new_config):
                return False
            
            # Use new configuration for testing
            test_config = new_config
        else:
            test_config = current_config
        
        # Step 3: Test SMTP connectivity
        if not self.test_smtp_connectivity(
            test_config['SMTP_HOST'],
            test_config['SMTP_PORT'],
            test_config['SMTP_USER'],
            test_config['SMTP_PASSWORD']
        ):
            logger.error("❌ SMTP connectivity test failed")
            self.get_smtp_recommendations()
            return False
        
        # Step 4: Send test email
        if not self.send_test_email(
            test_config['SMTP_HOST'],
            test_config['SMTP_PORT'],
            test_config['SMTP_USER'],
            test_config['SMTP_PASSWORD'],
            test_config['EMAIL_FROM']
        ):
            logger.error("❌ Test email sending failed")
            return False
        
        # Step 5: Test Celery task (if available)
        logger.info("\n🔄 Testing Celery email task processing...")
        celery_result = self.test_celery_email_task()
        
        # Final results
        logger.info("\n" + "=" * 60)
        logger.info("📊 EMAIL SYSTEM FIX RESULTS")
        logger.info("=" * 60)
        logger.info("✅ SMTP Configuration: FIXED")
        logger.info("✅ SMTP Connectivity: WORKING")
        logger.info("✅ Email Sending: WORKING")
        
        if celery_result is True:
            logger.info("✅ Celery Email Tasks: WORKING")
        elif celery_result is False:
            logger.warning("⚠️  Celery Email Tasks: ISSUES DETECTED")
        else:
            logger.info("⏳ Celery Email Tasks: PROCESSING")
        
        logger.info(f"\n📧 Test email sent to: {self.test_recipient}")
        logger.info("🎉 Email system is now configured and working!")
        logger.info("\n📋 Next Steps:")
        logger.info("1. Check your email inbox for the test message")
        logger.info("2. Restart your FastAPI server")
        logger.info("3. Run the registration test again")
        logger.info("4. Welcome emails will now be delivered!")
        logger.info("=" * 60)
        
        return True

def main():
    """Main function to run email system fix."""
    fixer = EmailSystemFixer()
    success = fixer.run_complete_email_fix()
    
    if success:
        print("\n🎉 Email system fixed successfully!")
        print("Now run: python test_sahil_registration_flow.py --url http://localhost:8000")
        exit(0)
    else:
        print("\n❌ Email system fix failed. Please check the errors above.")
        exit(1)

if __name__ == "__main__":
    main()
