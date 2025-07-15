"""
Comprehensive Test Runner for Certify Studio
Executes unit, integration, and e2e tests with detailed reporting
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import subprocess
import pytest
import coverage
from typing import Dict, List, Any, Optional
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestRunner:
    """Comprehensive test runner with reporting"""
    
    def __init__(self):
        self.results = {
            "start_time": None,
            "end_time": None,
            "duration": None,
            "summary": {},
            "details": {},
            "coverage": {}
        }
        self.test_categories = {
            "unit": "tests/unit",
            "integration": "tests/integration", 
            "e2e": "tests/e2e"
        }
        
    def print_banner(self, text: str, color=Fore.CYAN):
        """Print a colored banner"""
        width = 80
        print(f"\n{color}{'=' * width}")
        print(f"{text.center(width)}")
        print(f"{'=' * width}{Style.RESET_ALL}\n")
        
    def print_section(self, text: str, color=Fore.YELLOW):
        """Print a section header"""
        print(f"\n{color}>>> {text}{Style.RESET_ALL}")
        
    def run_all_tests(self):
        """Run all test categories"""
        self.print_banner("CERTIFY STUDIO - COMPREHENSIVE TEST SUITE", Fore.GREEN)
        self.results["start_time"] = datetime.now().isoformat()
        
        # Start coverage
        cov = coverage.Coverage()
        cov.start()
        
        try:
            # 1. Check backend health
            if not self._check_backend_health():
                print(f"{Fore.RED}✗ Backend is not running!{Style.RESET_ALL}")
                print(f"Please start the backend with: {Fore.YELLOW}uv run uvicorn certify_studio.main:app --reload{Style.RESET_ALL}")
                return False
                
            # 2. Run unit tests
            self.print_section("Running Unit Tests")
            unit_results = self._run_test_category("unit")
            
            # 3. Run integration tests
            self.print_section("Running Integration Tests")
            integration_results = self._run_test_category("integration")
            
            # 4. Run E2E tests
            self.print_section("Running End-to-End Tests")
            e2e_results = self._run_test_category("e2e")
            
            # 5. Run specific AWS AI Practitioner test
            self.print_section("Running AWS AI Practitioner Workflow Test")
            aws_results = self._run_specific_test(
                "tests/e2e/test_aws_ai_practitioner_complete.py::TestAWSAIPractitioner::test_pdf_upload_workflow"
            )
            
            # Stop coverage and generate report
            cov.stop()
            cov.save()
            
            # Generate coverage report
            self.print_section("Generating Coverage Report")
            coverage_stats = self._generate_coverage_report(cov)
            
            # Compile results
            self._compile_results(unit_results, integration_results, e2e_results, aws_results, coverage_stats)
            
            # Print summary
            self._print_summary()
            
            # Save detailed report
            self._save_report()
            
            return self.results["summary"]["all_passed"]
            
        except Exception as e:
            print(f"{Fore.RED}✗ Test runner error: {e}{Style.RESET_ALL}")
            return False
            
        finally:
            self.results["end_time"] = datetime.now().isoformat()
            if self.results["start_time"]:
                start = datetime.fromisoformat(self.results["start_time"])
                end = datetime.fromisoformat(self.results["end_time"])
                self.results["duration"] = (end - start).total_seconds()
                
    def _check_backend_health(self) -> bool:
        """Check if backend is running"""
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            return response.status_code == 200
        except:
            return False
            
    def _run_test_category(self, category: str) -> Dict[str, Any]:
        """Run a specific category of tests"""
        test_path = self.test_categories[category]
        
        # Run pytest with JSON report
        report_file = f"test_report_{category}.json"
        
        result = pytest.main([
            test_path,
            "-v",
            "--tb=short",
            f"--json-report",
            f"--json-report-file={report_file}",
            "--json-report-indent=2"
        ])
        
        # Parse results
        if os.path.exists(report_file):
            with open(report_file, 'r') as f:
                report_data = json.load(f)
            os.remove(report_file)
            
            return {
                "passed": report_data["summary"]["passed"],
                "failed": report_data["summary"]["failed"],
                "skipped": report_data["summary"].get("skipped", 0),
                "total": report_data["summary"]["total"],
                "duration": report_data["duration"],
                "tests": report_data["tests"]
            }
        else:
            # Fallback if JSON report fails
            return {
                "passed": 0 if result != 0 else 1,
                "failed": 1 if result != 0 else 0,
                "skipped": 0,
                "total": 1,
                "duration": 0,
                "tests": []
            }
            
    def _run_specific_test(self, test_path: str) -> Dict[str, Any]:
        """Run a specific test"""
        result = pytest.main([
            test_path,
            "-v",
            "-s",  # Show print statements
            "--tb=short"
        ])
        
        return {
            "passed": 1 if result == 0 else 0,
            "failed": 0 if result == 0 else 1,
            "skipped": 0,
            "total": 1,
            "duration": 0
        }
        
    def _generate_coverage_report(self, cov) -> Dict[str, Any]:
        """Generate coverage report"""
        try:
            # Generate HTML report
            html_dir = "coverage_html_report"
            cov.html_report(directory=html_dir)
            
            # Get coverage stats
            total_coverage = cov.report()
            
            return {
                "total_coverage": total_coverage,
                "html_report": html_dir
            }
        except Exception as e:
            print(f"{Fore.YELLOW}⚠ Coverage report generation failed: {e}{Style.RESET_ALL}")
            return {"total_coverage": 0, "html_report": None}
            
    def _compile_results(self, unit, integration, e2e, aws, coverage):
        """Compile all test results"""
        self.results["details"] = {
            "unit": unit,
            "integration": integration,
            "e2e": e2e,
            "aws_practitioner": aws
        }
        
        self.results["coverage"] = coverage
        
        # Calculate summary
        total_passed = sum(r.get("passed", 0) for r in self.results["details"].values())
        total_failed = sum(r.get("failed", 0) for r in self.results["details"].values())
        total_skipped = sum(r.get("skipped", 0) for r in self.results["details"].values())
        total_tests = sum(r.get("total", 0) for r in self.results["details"].values())
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
            "all_passed": total_failed == 0,
            "pass_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0
        }
        
    def _print_summary(self):
        """Print test summary"""
        self.print_banner("TEST RESULTS SUMMARY", Fore.CYAN)
        
        summary = self.results["summary"]
        
        # Overall results
        status_color = Fore.GREEN if summary["all_passed"] else Fore.RED
        status_text = "PASSED" if summary["all_passed"] else "FAILED"
        
        print(f"Overall Status: {status_color}{status_text}{Style.RESET_ALL}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {Fore.GREEN}{summary['passed']}{Style.RESET_ALL}")
        print(f"Failed: {Fore.RED}{summary['failed']}{Style.RESET_ALL}")
        print(f"Skipped: {Fore.YELLOW}{summary['skipped']}{Style.RESET_ALL}")
        print(f"Pass Rate: {summary['pass_rate']:.1f}%")
        
        # Duration
        if self.results["duration"]:
            print(f"Duration: {self.results['duration']:.2f} seconds")
            
        # Coverage
        if self.results["coverage"].get("total_coverage"):
            print(f"\nCode Coverage: {self.results['coverage']['total_coverage']:.1f}%")
            if self.results["coverage"].get("html_report"):
                print(f"HTML Report: {self.results['coverage']['html_report']}/index.html")
                
        # Category breakdown
        print("\n" + "-" * 50)
        print("Category Breakdown:")
        for category, details in self.results["details"].items():
            status = "✓" if details.get("failed", 0) == 0 else "✗"
            color = Fore.GREEN if status == "✓" else Fore.RED
            print(f"{color}{status} {category.upper()}: {details.get('passed', 0)}/{details.get('total', 0)} passed{Style.RESET_ALL}")
            
    def _save_report(self):
        """Save detailed test report"""
        report_path = Path("test_reports")
        report_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_path / f"test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        print(f"\nDetailed report saved to: {report_file}")


class PerformanceTestRunner:
    """Run performance and load tests"""
    
    def __init__(self):
        self.results = {}
        
    def run_load_test(self):
        """Run load testing on API endpoints"""
        print(f"\n{Fore.YELLOW}Running Load Tests...{Style.RESET_ALL}")
        
        # This would use locust or similar tool
        # For now, we'll do a simple concurrent request test
        import asyncio
        import aiohttp
        
        async def make_request(session, url):
            try:
                start = time.time()
                async with session.get(url) as response:
                    await response.text()
                    return time.time() - start, response.status
            except Exception as e:
                return None, str(e)
                
        async def run_concurrent_requests(url, count):
            async with aiohttp.ClientSession() as session:
                tasks = [make_request(session, url) for _ in range(count)]
                results = await asyncio.gather(*tasks)
                return results
                
        # Test endpoints
        endpoints = [
            ("Health Check", "http://localhost:8000/health", 100),
            ("API Info", "http://localhost:8000/api/v1/info", 50),
        ]
        
        for name, url, count in endpoints:
            print(f"\nTesting {name} with {count} concurrent requests...")
            results = asyncio.run(run_concurrent_requests(url, count))
            
            successful = [r for r in results if r[0] is not None]
            failed = len(results) - len(successful)
            
            if successful:
                response_times = [r[0] for r in successful]
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)
                min_time = min(response_times)
                
                print(f"  Success: {len(successful)}/{count}")
                print(f"  Failed: {failed}")
                print(f"  Avg Response Time: {avg_time*1000:.2f}ms")
                print(f"  Min/Max: {min_time*1000:.2f}ms / {max_time*1000:.2f}ms")
            else:
                print(f"  {Fore.RED}All requests failed!{Style.RESET_ALL}")


def main():
    """Main test execution"""
    runner = TestRunner()
    
    # Check if we should run specific tests
    if len(sys.argv) > 1:
        if sys.argv[1] == "--performance":
            perf_runner = PerformanceTestRunner()
            perf_runner.run_load_test()
        elif sys.argv[1] == "--aws":
            # Run only AWS tests
            runner.print_banner("AWS AI PRACTITIONER TEST", Fore.YELLOW)
            pytest.main([
                "tests/e2e/test_aws_ai_practitioner_complete.py",
                "-v", "-s"
            ])
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Usage: python run_comprehensive_tests.py [--performance|--aws]")
    else:
        # Run all tests
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
