#!/usr/bin/env python3
"""
Complete Test Suite for Sahil Saurav Registration Flow
=====================================================

This is the master test runner that executes all tests for Sahil's
complete user journey from registration to rank improvement.

Test Coverage:
1. API Health and Connectivity
2. User Registration (Sahil Saurav, sahilsaurav2507@gmail.com)
3. Email System and Background Tasks
4. Authentication and JWT Tokens
5. Social Media Sharing (All Platforms)
6. Points Accumulation and Calculation
7. Rank Improvement and Leaderboard
8. Analytics and Reporting
9. Complete User Journey Validation

Usage:
    python run_sahil_complete_test.py --url http://localhost:8000
    python run_sahil_complete_test.py --url https://www.lawvriksh.com/api --production
"""

import argparse
import logging
import json
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SahilCompleteTestRunner:
    """Master test runner for Sahil's complete registration flow."""
    
    def __init__(self, api_url: str, production_mode: bool = False):
        self.api_url = api_url
        self.production_mode = production_mode
        self.test_results = {}
        self.start_time = datetime.now()
        
        self.test_user = {
            "name": "Sahil Saurav",
            "email": "sahilsaurav2507@gmail.com",
            "password": "SecurePassword123!"
        }
    
    def run_subprocess_test(self, script_name: str, args: List[str] = None) -> Dict[str, Any]:
        """Run a test script as subprocess and capture results."""
        cmd = [sys.executable, script_name]
        if args:
            cmd.extend(args)
        
        logger.info(f"🔄 Running: {script_name}")
        
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            end_time = time.time()
            
            execution_time = end_time - start_time
            success = result.returncode == 0
            
            return {
                "script": script_name,
                "success": success,
                "return_code": result.returncode,
                "execution_time": execution_time,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "script": script_name,
                "success": False,
                "return_code": -1,
                "execution_time": 300,
                "stdout": "",
                "stderr": "Test timed out after 5 minutes"
            }
        except Exception as e:
            return {
                "script": script_name,
                "success": False,
                "return_code": -1,
                "execution_time": 0,
                "stdout": "",
                "stderr": str(e)
            }
    
    def run_registration_flow_test(self) -> Dict[str, Any]:
        """Run the main registration flow test."""
        logger.info("🚀 Running Sahil Registration Flow Test")
        
        args = ["--url", self.api_url]
        result = self.run_subprocess_test("test_sahil_registration_flow.py", args)
        
        # Log results
        if result["success"]:
            logger.info("✅ Registration Flow Test: PASSED")
        else:
            logger.error("❌ Registration Flow Test: FAILED")
            if result["stderr"]:
                logger.error(f"Error: {result['stderr']}")
        
        return result
    
    def run_email_background_test(self) -> Dict[str, Any]:
        """Run the email and background tasks test."""
        logger.info("📧 Running Email and Background Tasks Test")
        
        result = self.run_subprocess_test("test_email_and_background_tasks.py")
        
        # Log results
        if result["success"]:
            logger.info("✅ Email and Background Tasks Test: PASSED")
        else:
            logger.error("❌ Email and Background Tasks Test: FAILED")
            if result["stderr"]:
                logger.error(f"Error: {result['stderr']}")
        
        return result
    
    def run_api_comprehensive_test(self) -> Dict[str, Any]:
        """Run the comprehensive API test suite."""
        logger.info("🔧 Running Comprehensive API Test")
        
        args = ["--url", self.api_url]
        result = self.run_subprocess_test("test_all_apis.py", args)
        
        # Log results
        if result["success"]:
            logger.info("✅ Comprehensive API Test: PASSED")
        else:
            logger.error("❌ Comprehensive API Test: FAILED")
            if result["stderr"]:
                logger.error(f"Error: {result['stderr']}")
        
        return result
    
    def validate_test_environment(self) -> bool:
        """Validate that the test environment is ready."""
        logger.info("🔍 Validating Test Environment")
        
        # Check if required test files exist
        required_files = [
            "test_sahil_registration_flow.py",
            "test_email_and_background_tasks.py",
            "test_all_apis.py"
        ]
        
        missing_files = []
        for file in required_files:
            try:
                with open(file, 'r'):
                    pass
            except FileNotFoundError:
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"❌ Missing test files: {missing_files}")
            return False
        
        logger.info("✅ All test files found")
        
        # Test API connectivity
        try:
            import requests
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ API is accessible")
                return True
            else:
                logger.error(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to API: {e}")
            return False
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive test report."""
        end_time = datetime.now()
        total_execution_time = (end_time - self.start_time).total_seconds()
        
        # Calculate overall statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "test_summary": {
                "user": self.test_user,
                "api_url": self.api_url,
                "production_mode": self.production_mode,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_execution_time": total_execution_time,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": success_rate
            },
            "test_results": self.test_results,
            "recommendations": self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check individual test results
        for test_name, result in self.test_results.items():
            if not result["success"]:
                if "registration" in test_name.lower():
                    recommendations.append("Check database connectivity and user service configuration")
                elif "email" in test_name.lower():
                    recommendations.append("Verify SMTP configuration and Celery worker status")
                elif "api" in test_name.lower():
                    recommendations.append("Review API endpoints and authentication configuration")
        
        # General recommendations
        if len(recommendations) == 0:
            recommendations.append("All tests passed! System is ready for production")
        else:
            recommendations.append("Review failed tests and check system logs for detailed error information")
            recommendations.append("Ensure all required services (MySQL, RabbitMQ, Redis) are running")
        
        return recommendations
    
    def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run the complete test suite for Sahil's registration flow."""
        logger.info("🎯 SAHIL SAURAV COMPLETE TEST SUITE")
        logger.info("=" * 70)
        logger.info(f"User: {self.test_user['name']} ({self.test_user['email']})")
        logger.info(f"API URL: {self.api_url}")
        logger.info(f"Production Mode: {self.production_mode}")
        logger.info(f"Start Time: {self.start_time}")
        logger.info("=" * 70)
        
        # Validate environment
        if not self.validate_test_environment():
            logger.error("❌ Test environment validation failed")
            return {"error": "Environment validation failed"}
        
        # Run test sequence
        test_sequence = [
            ("Registration Flow Test", self.run_registration_flow_test),
            ("Email and Background Tasks Test", self.run_email_background_test),
            ("Comprehensive API Test", self.run_api_comprehensive_test),
        ]
        
        for test_name, test_function in test_sequence:
            logger.info(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_function()
                self.test_results[test_name] = result
                
                # Brief summary
                status = "✅ PASSED" if result["success"] else "❌ FAILED"
                logger.info(f"{status} - Execution Time: {result['execution_time']:.2f}s")
                
                time.sleep(2)  # Brief pause between major test suites
                
            except Exception as e:
                logger.error(f"❌ {test_name} failed with exception: {e}")
                self.test_results[test_name] = {
                    "success": False,
                    "error": str(e),
                    "execution_time": 0
                }
        
        # Generate comprehensive report
        report = self.generate_comprehensive_report()
        
        # Display final results
        logger.info("\n" + "=" * 70)
        logger.info("📊 FINAL TEST RESULTS")
        logger.info("=" * 70)
        logger.info(f"Total Execution Time: {report['test_summary']['total_execution_time']:.2f}s")
        logger.info(f"Total Test Suites: {report['test_summary']['total_tests']}")
        logger.info(f"Passed: {report['test_summary']['passed_tests']}")
        logger.info(f"Failed: {report['test_summary']['failed_tests']}")
        logger.info(f"Success Rate: {report['test_summary']['success_rate']:.1f}%")
        
        # Show recommendations
        logger.info("\n📋 RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            logger.info(f"{i}. {rec}")
        
        # Final status
        if report['test_summary']['success_rate'] == 100.0:
            logger.info("\n🎉 ALL TESTS PASSED!")
            logger.info("✅ Sahil's complete registration flow is working perfectly!")
            logger.info("✅ Email system is functional")
            logger.info("✅ Social sharing and rank improvement working")
            logger.info("✅ System is ready for production!")
        else:
            logger.warning("\n⚠️  SOME TESTS FAILED")
            logger.warning("Please review the failed tests and fix issues before production deployment")
        
        logger.info("=" * 70)
        
        # Save comprehensive report
        report_filename = f"sahil_complete_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Detailed report saved to: {report_filename}")
        
        return report

def main():
    """Main function to run the complete test suite."""
    parser = argparse.ArgumentParser(description="Complete Test Suite for Sahil Saurav Registration Flow")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--production", action="store_true", help="Production mode testing")
    args = parser.parse_args()
    
    # Run the complete test suite
    test_runner = SahilCompleteTestRunner(args.url, args.production)
    report = test_runner.run_complete_test_suite()
    
    # Exit with appropriate code
    if "error" in report:
        exit(2)
    elif report["test_summary"]["success_rate"] == 100.0:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()
