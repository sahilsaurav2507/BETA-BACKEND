#!/usr/bin/env python3
"""
Comprehensive API Testing Script for Lawvriksh Backend
This script tests all API endpoints with proper error handling and reporting.
"""

import os
import sys
import json
import time
import requests
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('api_test_results.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Data class to store test results."""
    name: str
    status_code: int
    success: bool
    response_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time: float

class APITester:
    """Comprehensive API testing class with proper error handling."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("API_BASE", "http://localhost:8000")
        self.session = requests.Session()
        self.session.timeout = 30  # 30 second timeout
        self.results: List[TestResult] = []
        self.access_token: Optional[str] = None
        self.admin_token: Optional[str] = None

        # Test data
        self.test_user = {
            "name": "API Test User",
            "email": f"apitest_{int(time.time())}@example.com",
            "password": "SecureTestPass123!"
        }

        logger.info(f"Initialized API Tester for {self.base_url}")

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with proper error handling."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {method} {endpoint}: {e}")
            raise

    def test_endpoint(self, name: str, method: str, endpoint: str,
                     expected_status: int = 200, **kwargs) -> TestResult:
        """Test a single endpoint and record results."""
        start_time = time.time()

        try:
            response = self.make_request(method, endpoint, **kwargs)
            execution_time = time.time() - start_time

            # Try to parse JSON response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text[:500]}

            success = response.status_code == expected_status
            error_message = None if success else f"Expected {expected_status}, got {response.status_code}"

            result = TestResult(
                name=name,
                status_code=response.status_code,
                success=success,
                response_data=response_data,
                error_message=error_message,
                execution_time=execution_time
            )

            self.results.append(result)
            self._log_result(result)
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            result = TestResult(
                name=name,
                status_code=0,
                success=False,
                response_data=None,
                error_message=str(e),
                execution_time=execution_time
            )
            self.results.append(result)
            self._log_result(result)
            return result

    def _log_result(self, result: TestResult):
        """Log test result."""
        status = "[PASS]" if result.success else "[FAIL]"
        logger.info(f"{status} {result.name} [{result.status_code}] ({result.execution_time:.2f}s)")

        if not result.success:
            logger.error(f"   Error: {result.error_message}")

        if result.response_data and isinstance(result.response_data, dict):
            if 'detail' in result.response_data:
                logger.info(f"   Detail: {result.response_data['detail']}")

    def test_health_check(self):
        """Test health check endpoint."""
        return self.test_endpoint("Health Check", "GET", "/health")


    def test_user_signup(self):
        """Test user signup endpoint."""
        return self.test_endpoint(
            "User Signup",
            "POST",
            "/auth/signup",
            expected_status=201,
            json=self.test_user
        )

    def test_user_login(self):
        """Test user login endpoint."""
        login_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        }
        result = self.test_endpoint(
            "User Login",
            "POST",
            "/auth/login",
            json=login_data
        )

        # Extract access token if login successful
        if result.success and result.response_data:
            self.access_token = result.response_data.get("access_token")
            if self.access_token:
                logger.info("[SUCCESS] Access token obtained successfully")
            else:
                logger.warning("[WARNING] No access token in login response")

        return result

    def test_get_current_user(self):
        """Test get current user endpoint."""
        if not self.access_token:
            logger.warning("[WARNING] Skipping current user test - no access token")
            return None

        headers = {"Authorization": f"Bearer {self.access_token}"}
        return self.test_endpoint(
            "Get Current User",
            "GET",
            "/auth/me",
            headers=headers
        )

    def test_share_endpoints(self):
        """Test all sharing endpoints."""
        if not self.access_token:
            logger.warning("[WARNING] Skipping share tests - no access token")
            return []

        headers = {"Authorization": f"Bearer {self.access_token}"}
        results = []

        # Test sharing on different platforms
        platforms = ["twitter", "facebook", "linkedin", "instagram"]
        for platform in platforms:
            result = self.test_endpoint(
                f"Share on {platform.title()}",
                "POST",
                f"/shares/{platform}",
                expected_status=201,
                headers=headers
            )
            results.append(result)
            time.sleep(0.5)  # Small delay between requests

        # Test share history
        result = self.test_endpoint(
            "Share History",
            "GET",
            "/shares/history",
            headers=headers
        )
        results.append(result)

        # Test share analytics
        result = self.test_endpoint(
            "Share Analytics",
            "GET",
            "/shares/analytics",
            headers=headers
        )
        results.append(result)

        return results

    def test_leaderboard_endpoints(self):
        """Test leaderboard endpoints."""
        results = []

        # Test main leaderboard
        result = self.test_endpoint("Leaderboard", "GET", "/leaderboard")
        results.append(result)

        # Test leaderboard with pagination
        result = self.test_endpoint(
            "Leaderboard (Page 1)",
            "GET",
            "/leaderboard?page=1&limit=10"
        )
        results.append(result)

        return results

    def test_admin_endpoints(self):
        """Test admin endpoints."""
        admin_email = os.getenv("ADMIN_EMAIL", "admin@lawvriksh.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "password123")

        results = []

        # Test admin login
        admin_login_data = {
            "email": admin_email,
            "password": admin_password
        }

        result = self.test_endpoint(
            "Admin Login",
            "POST",
            "/admin/login",
            json=admin_login_data
        )
        results.append(result)

        # Extract admin token if login successful
        if result.success and result.response_data:
            self.admin_token = result.response_data.get("access_token")

        if not self.admin_token:
            logger.warning("[WARNING] Skipping admin tests - no admin token")
            return results

        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

        # Test admin dashboard
        result = self.test_endpoint(
            "Admin Dashboard",
            "GET",
            "/admin/dashboard",
            headers=admin_headers
        )
        results.append(result)

        # Test admin users list
        result = self.test_endpoint(
            "Admin Users List",
            "GET",
            "/admin/users",
            headers=admin_headers
        )
        results.append(result)

        return results

    def run_all_tests(self):
        """Run all API tests in sequence."""
        logger.info("[START] Starting comprehensive API testing...")
        logger.info(f"Target API: {self.base_url}")

        # Test sequence
        test_methods = [
            self.test_health_check,
            self.test_user_signup,
            self.test_user_login,
            self.test_get_current_user,
            self.test_share_endpoints,
            self.test_leaderboard_endpoints,
            self.test_admin_endpoints,
        ]

        for test_method in test_methods:
            try:
                result = test_method()
                if isinstance(result, list):
                    # Handle methods that return multiple results
                    continue
                time.sleep(0.5)  # Small delay between test groups
            except Exception as e:
                logger.error(f"Test method {test_method.__name__} failed: {e}")

        self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests

        logger.info("\n" + "="*60)
        logger.info("[REPORT] API TEST REPORT")
        logger.info("="*60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            logger.info("\n[FAILED TESTS]:")
            for result in self.results:
                if not result.success:
                    logger.info(f"  - {result.name}: {result.error_message}")

        # Performance summary
        avg_time = sum(r.execution_time for r in self.results) / total_tests
        logger.info(f"\n[PERFORMANCE] Average Response Time: {avg_time:.2f}s")

        # Slowest endpoints
        slowest = sorted(self.results, key=lambda x: x.execution_time, reverse=True)[:3]
        logger.info("\n[SLOWEST ENDPOINTS]:")
        for result in slowest:
            logger.info(f"  - {result.name}: {result.execution_time:.2f}s")

        logger.info("="*60)

        # Save detailed report to file
        self.save_detailed_report()

    def save_detailed_report(self):
        """Save detailed test report to JSON file."""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "summary": {
                "total_tests": len(self.results),
                "passed": sum(1 for r in self.results if r.success),
                "failed": sum(1 for r in self.results if not r.success),
                "average_response_time": sum(r.execution_time for r in self.results) / len(self.results)
            },
            "results": [
                {
                    "name": r.name,
                    "status_code": r.status_code,
                    "success": r.success,
                    "error_message": r.error_message,
                    "execution_time": r.execution_time,
                    "response_data": r.response_data
                }
                for r in self.results
            ]
        }

        with open("api_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info("[REPORT] Detailed report saved to api_test_report.json")

def main():
    """Main function to run API tests."""
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive API Testing for Lawvriksh Backend")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check if API is accessible
    try:
        response = requests.get(f"{args.url}/health", timeout=10)
        if response.status_code != 200:
            logger.error(f"[ERROR] API health check failed: {response.status_code}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logger.error(f"[ERROR] Cannot connect to API at {args.url}: {e}")
        logger.info("[INFO] Make sure the API server is running:")
        logger.info("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)

    # Run tests
    tester = APITester(args.url)
    tester.run_all_tests()

    # Exit with error code if any tests failed
    failed_count = sum(1 for r in tester.results if not r.success)
    sys.exit(1 if failed_count > 0 else 0)

if __name__ == "__main__":
    main()