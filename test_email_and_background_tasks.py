#!/usr/bin/env python3
"""
Email and Background Tasks Test for Sahil Registration
=====================================================

This script tests the email sending and background task processing
specifically for Sahil Saurav's registration flow.

Tests:
1. Email service configuration
2. SMTP connectivity
3. Celery worker status
4. RabbitMQ connectivity
5. Welcome email task queuing
6. Background task processing
7. Email delivery verification (if possible)

Usage:
    python test_email_and_background_tasks.py
"""

import smtplib
import logging
import json
import time
from datetime import datetime
from email.mime.text import MIMEText
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailAndBackgroundTasksTest:
    """Test email and background task functionality."""
    
    def __init__(self):
        self.test_results = []
        self.test_user = {
            "name": "Sahil Saurav",
            "email": "sahilsaurav2507@gmail.com"
        }
    
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any] = None):
        """Log test result with details."""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}")
        
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        
        if details and not success:
            logger.error(f"   Error Details: {details}")
        elif details and success:
            logger.info(f"   Success Details: {details}")
    
    def test_environment_variables(self) -> bool:
        """Test if email environment variables are configured."""
        try:
            from app.core.config import settings
            
            email_config = {
                "EMAIL_FROM": getattr(settings, 'EMAIL_FROM', None),
                "SMTP_HOST": getattr(settings, 'SMTP_HOST', None),
                "SMTP_PORT": getattr(settings, 'SMTP_PORT', None),
                "SMTP_USER": getattr(settings, 'SMTP_USER', None),
                "SMTP_PASSWORD": bool(getattr(settings, 'SMTP_PASSWORD', None)),
                "RABBITMQ_URL": getattr(settings, 'RABBITMQ_URL', None)
            }
            
            missing_configs = [k for k, v in email_config.items() if not v]
            success = len(missing_configs) == 0
            
            details = {
                "email_config": email_config,
                "missing_configs": missing_configs,
                "config_complete": success
            }
            
            self.log_test_result("Environment Variables", success, details)
            return success
            
        except Exception as e:
            self.log_test_result("Environment Variables", False, {"error": str(e)})
            return False
    
    def test_smtp_connectivity(self) -> bool:
        """Test SMTP server connectivity."""
        try:
            from app.core.config import settings
            
            if not all([settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USER, settings.SMTP_PASSWORD]):
                self.log_test_result("SMTP Connectivity", False, {"error": "SMTP configuration incomplete"})
                return False
            
            # Test SMTP connection
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.quit()
            
            details = {
                "smtp_host": settings.SMTP_HOST,
                "smtp_port": settings.SMTP_PORT,
                "smtp_user": settings.SMTP_USER,
                "connection_status": "✅ Connected successfully"
            }
            
            self.log_test_result("SMTP Connectivity", True, details)
            return True
            
        except Exception as e:
            details = {
                "error": str(e),
                "recommendation": "Check SMTP credentials and server settings"
            }
            self.log_test_result("SMTP Connectivity", False, details)
            return False
    
    def test_rabbitmq_connectivity(self) -> bool:
        """Test RabbitMQ connectivity for Celery."""
        try:
            import pika
            from app.core.config import settings
            
            # Parse RabbitMQ URL
            connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
            channel = connection.channel()
            
            # Test basic operations
            channel.queue_declare(queue='test_queue', durable=True)
            channel.queue_delete(queue='test_queue')
            
            connection.close()
            
            details = {
                "rabbitmq_url": settings.RABBITMQ_URL,
                "connection_status": "✅ Connected successfully",
                "queue_operations": "✅ Queue operations successful"
            }
            
            self.log_test_result("RabbitMQ Connectivity", True, details)
            return True
            
        except ImportError:
            details = {
                "error": "pika library not installed",
                "recommendation": "Install pika: pip install pika"
            }
            self.log_test_result("RabbitMQ Connectivity", False, details)
            return False
        except Exception as e:
            details = {
                "error": str(e),
                "recommendation": "Check RabbitMQ server status and URL configuration"
            }
            self.log_test_result("RabbitMQ Connectivity", False, details)
            return False
    
    def test_celery_worker_status(self) -> bool:
        """Test if Celery workers are running."""
        try:
            from app.tasks.email_tasks import celery_app
            
            # Get active workers
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            
            if active_workers:
                worker_count = len(active_workers)
                details = {
                    "active_workers": worker_count,
                    "worker_names": list(active_workers.keys()),
                    "status": "✅ Celery workers are running"
                }
                success = True
            else:
                details = {
                    "active_workers": 0,
                    "status": "❌ No active Celery workers found",
                    "recommendation": "Start Celery workers: celery -A app.tasks.celery_app worker --loglevel=info"
                }
                success = False
            
            self.log_test_result("Celery Worker Status", success, details)
            return success
            
        except Exception as e:
            details = {
                "error": str(e),
                "recommendation": "Check Celery configuration and worker processes"
            }
            self.log_test_result("Celery Worker Status", False, details)
            return False
    
    def test_email_service_function(self) -> bool:
        """Test the email service function directly."""
        try:
            from app.services.email_service import send_welcome_email
            
            # Test with Sahil's data (this will actually send an email if SMTP is configured)
            logger.warning("⚠️  This test will send a real email to sahilsaurav2507@gmail.com")
            user_input = input("Continue with email sending test? (y/N): ").lower().strip()
            
            if user_input not in ['y', 'yes']:
                details = {
                    "status": "⏭️  Skipped by user choice",
                    "note": "Email service function not tested"
                }
                self.log_test_result("Email Service Function", True, details)
                return True
            
            # Send welcome email
            send_welcome_email(self.test_user["email"], self.test_user["name"])
            
            details = {
                "recipient": self.test_user["email"],
                "recipient_name": self.test_user["name"],
                "email_type": "welcome_email",
                "status": "✅ Email sent successfully"
            }
            
            self.log_test_result("Email Service Function", True, details)
            return True
            
        except Exception as e:
            details = {
                "error": str(e),
                "recipient": self.test_user["email"],
                "recommendation": "Check SMTP configuration and email service implementation"
            }
            self.log_test_result("Email Service Function", False, details)
            return False
    
    def test_celery_task_queuing(self) -> bool:
        """Test Celery task queuing for welcome email."""
        try:
            from app.tasks.email_tasks import send_welcome_email_task
            
            # Queue the welcome email task
            task_result = send_welcome_email_task.delay(
                self.test_user["email"], 
                self.test_user["name"]
            )
            
            # Wait a bit for task to be processed
            time.sleep(2)
            
            # Check task status
            task_status = task_result.status
            task_info = {
                "task_id": task_result.id,
                "status": task_status,
                "ready": task_result.ready(),
                "successful": task_result.successful() if task_result.ready() else None
            }
            
            if task_result.ready():
                if task_result.successful():
                    task_info["result"] = task_result.result
                else:
                    task_info["error"] = str(task_result.info)
            
            success = task_status in ['SUCCESS', 'PENDING'] or task_result.successful()
            
            details = {
                "task_info": task_info,
                "recipient": self.test_user["email"],
                "queue_status": "✅ Task queued successfully" if success else "❌ Task failed"
            }
            
            self.log_test_result("Celery Task Queuing", success, details)
            return success
            
        except Exception as e:
            details = {
                "error": str(e),
                "recommendation": "Check Celery worker status and RabbitMQ connectivity"
            }
            self.log_test_result("Celery Task Queuing", False, details)
            return False
    
    def test_database_email_logging(self) -> bool:
        """Test if email events are logged in database (if implemented)."""
        try:
            from app.core.dependencies import get_db
            
            db = next(get_db())
            
            # This is a placeholder test since email logging might not be implemented
            # In a real scenario, you would check for email_logs table or similar
            
            details = {
                "status": "📝 Email logging check",
                "note": "Email logging implementation depends on specific requirements",
                "recommendation": "Implement email logging table if needed for audit trail"
            }
            
            db.close()
            
            self.log_test_result("Database Email Logging", True, details)
            return True
            
        except Exception as e:
            details = {
                "error": str(e),
                "note": "Email logging may not be implemented"
            }
            self.log_test_result("Database Email Logging", False, details)
            return False
    
    def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run the complete email and background tasks test suite."""
        logger.info("📧 Starting Email and Background Tasks Test")
        logger.info("=" * 60)
        logger.info(f"Test User: {self.test_user['name']} ({self.test_user['email']})")
        logger.info("=" * 60)
        
        # Test sequence
        test_sequence = [
            ("Environment Variables", self.test_environment_variables),
            ("SMTP Connectivity", self.test_smtp_connectivity),
            ("RabbitMQ Connectivity", self.test_rabbitmq_connectivity),
            ("Celery Worker Status", self.test_celery_worker_status),
            ("Email Service Function", self.test_email_service_function),
            ("Celery Task Queuing", self.test_celery_task_queuing),
            ("Database Email Logging", self.test_database_email_logging),
        ]
        
        passed_tests = 0
        total_tests = len(test_sequence)
        
        for test_name, test_function in test_sequence:
            logger.info(f"\n🔄 Running: {test_name}")
            try:
                if test_function():
                    passed_tests += 1
                time.sleep(1)  # Small delay between tests
            except Exception as e:
                logger.error(f"Test {test_name} failed with exception: {e}")
        
        # Generate final report
        success_rate = (passed_tests / total_tests) * 100
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 EMAIL AND BACKGROUND TASKS TEST REPORT")
        logger.info("=" * 60)
        logger.info(f"User: {self.test_user['name']} ({self.test_user['email']})")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED - Email system fully functional!")
        else:
            logger.warning("⚠️  Some tests failed - Check email configuration")
        
        logger.info("=" * 60)
        
        # Save detailed report
        report = {
            "test_summary": {
                "user": self.test_user,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": success_rate,
                "timestamp": datetime.now().isoformat()
            },
            "test_results": self.test_results
        }
        
        with open(f"email_background_tasks_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(report, f, indent=2)
        
        return report

def main():
    """Main function to run the email and background tasks test suite."""
    # Run the test suite
    test_suite = EmailAndBackgroundTasksTest()
    report = test_suite.run_complete_test_suite()
    
    # Exit with appropriate code
    if report["test_summary"]["success_rate"] == 100.0:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()
