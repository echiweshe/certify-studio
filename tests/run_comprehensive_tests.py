"""
Comprehensive Test Runner for Certify Studio

This script runs all tests (unit, integration, e2e) with colored output
and generates a comprehensive test report.
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestRunner:
    """Comprehensive test runner with reporting"""
    
    def __init__(self):
        self.results = {
            "start_time": datetime.now().isoformat(),
            "test_suites": [],
            "summary": {
                "total_suites": 0,
                "passed_suites": 0,
                "failed_suites": 0,
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "skipped_tests": 0,
                "total_time": 0
            }
        }
        self.output_dir = Path("tests/outputs/test_reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}\n")
    
    def print_section(self, text: str):
        """Print a section header"""
        print(f"\n{Colors.OKCYAN}{'-' * 60}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}{text}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}{'-' * 60}{Colors.ENDC}")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")
    
    def print_failure(self, text: str):
        """Print failure message"""
        print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")
    
    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")
    
    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")
    
    async def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        self.print_section("Checking Prerequisites")
        
        all_good = True
        
        # Check if backend is running
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    self.print_success("Backend is running")
                else:
                    self.print_failure("Backend returned non-200 status")
                    all_good = False
        except Exception as e:
            self.print_failure(f"Backend is not accessible: {e}")
            all_good = False
        
        # Check if test files exist
        test_files = [
            Path("downloads/aws/AIF-C01/AWS-Certified-AI-Practitioner_Exam-Guide.pdf"),
            Path("downloads/aws/AIF-C01/Sections-1-to-7-AI1-C01-Official-Course.pdf")
        ]
        
        for file in test_files:
            if file.exists():
                self.print_success(f"Test file exists: {file.name}")
            else:
                self.print_warning(f"Test file missing: {file}")
                all_good = False
        
        # Check Python packages
        required_packages = ["pytest", "httpx", "websockets", "aiofiles"]
        for package in required_packages:
            try:
                __import__(package)
                self.print_success(f"Package installed: {package}")
            except ImportError:
                self.print_failure(f"Package missing: {package}")
                all_good = False
        
        return all_good
    
    def run_test_suite(self, suite_name: str, test_path: str, pytest_args: List[str] = None) -> Dict[str, Any]:
        """Run a test suite using pytest"""
        self.print_section(f"Running {suite_name}")
        
        start_time = time.time()
        
        # Prepare pytest command
        cmd = ["python", "-m", "pytest", test_path]
        if pytest_args:
            cmd.extend(pytest_args)
        else:
            cmd.extend(["-v", "--tb=short", "--color=yes"])
        
        # Add JSON report output
        report_file = self.output_dir / f"{suite_name.lower().replace(' ', '_')}_report.json"
        cmd.extend([f"--json-report", f"--json-report-file={report_file}"])
        
        # Run tests
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        duration = time.time() - start_time
        
        # Parse results
        suite_result = {
            "name": suite_name,
            "path": test_path,
            "duration": duration,
            "return_code": result.returncode,
            "passed": result.returncode == 0
        }
        
        # Try to parse JSON report if available
        if report_file.exists():
            try:
                with open(report_file) as f:
                    json_report = json.load(f)
                    suite_result["details"] = {
                        "total": json_report["summary"]["total"],
                        "passed": json_report["summary"]["passed"],
                        "failed": json_report["summary"]["failed"],
                        "skipped": json_report["summary"]["skipped"]
                    }
            except:
                # Fallback to parsing output
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if "passed" in line and "failed" in line:
                        # Try to extract test counts from pytest output
                        parts = line.split()
                        suite_result["details"] = {"parsed_from_output": line.strip()}
        
        # Print results
        if suite_result["passed"]:
            self.print_success(f"{suite_name} completed in {duration:.2f}s")
        else:
            self.print_failure(f"{suite_name} failed after {duration:.2f}s")
            if result.stderr:
                print(f"\nErrors:\n{result.stderr}")
        
        return suite_result
    
    async def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests"""
        return self.run_test_suite(
            "Unit Tests",
            "tests/unit",
            ["-v", "-k", "not integration and not e2e"]
        )
    
    async def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        return self.run_test_suite(
            "Integration Tests",
            "tests/integration",
            ["-v"]
        )
    
    async def run_e2e_tests(self) -> Dict[str, Any]:
        """Run end-to-end tests"""
        return self.run_test_suite(
            "E2E Tests",
            "tests/e2e",
            ["-v", "-s", "--timeout=600"]
        )
    
    async def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        self.print_section("Running Performance Tests")
        
        start_time = time.time()
        perf_results = {
            "name": "Performance Tests",
            "duration": 0,
            "passed": True,
            "metrics": {}
        }
        
        try:
            import httpx
            
            # Test API response times
            async with httpx.AsyncClient() as client:
                endpoints = ["/", "/health", "/api/v1/info"]
                
                for endpoint in endpoints:
                    times = []
                    for _ in range(10):
                        start = time.time()
                        response = await client.get(f"http://localhost:8000{endpoint}")
                        times.append(time.time() - start)
                    
                    avg_time = sum(times) / len(times)
                    perf_results["metrics"][endpoint] = {
                        "avg_response_time": avg_time,
                        "min_response_time": min(times),
                        "max_response_time": max(times)
                    }
                    
                    if avg_time < 0.1:  # 100ms threshold
                        self.print_success(f"{endpoint}: {avg_time*1000:.2f}ms average")
                    else:
                        self.print_warning(f"{endpoint}: {avg_time*1000:.2f}ms average (slow)")
            
        except Exception as e:
            self.print_failure(f"Performance tests failed: {e}")
            perf_results["passed"] = False
            perf_results["error"] = str(e)
        
        perf_results["duration"] = time.time() - start_time
        return perf_results
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self.print_header("Test Report")
        
        # Calculate summary
        total_duration = sum(suite.get("duration", 0) for suite in self.results["test_suites"])
        self.results["summary"]["total_time"] = total_duration
        self.results["summary"]["total_suites"] = len(self.results["test_suites"])
        self.results["summary"]["passed_suites"] = sum(1 for s in self.results["test_suites"] if s.get("passed", False))
        self.results["summary"]["failed_suites"] = self.results["summary"]["total_suites"] - self.results["summary"]["passed_suites"]
        
        # Print summary
        print(f"Total Test Suites: {self.results['summary']['total_suites']}")
        print(f"Passed Suites: {Colors.OKGREEN}{self.results['summary']['passed_suites']}{Colors.ENDC}")
        print(f"Failed Suites: {Colors.FAIL}{self.results['summary']['failed_suites']}{Colors.ENDC}")
        print(f"Total Duration: {total_duration:.2f}s")
        
        # Detailed results per suite
        print("\nDetailed Results:")
        for suite in self.results["test_suites"]:
            status = f"{Colors.OKGREEN}PASSED{Colors.ENDC}" if suite.get("passed", False) else f"{Colors.FAIL}FAILED{Colors.ENDC}"
            print(f"\n  {suite['name']}: {status} ({suite['duration']:.2f}s)")
            if "details" in suite:
                details = suite["details"]
                if isinstance(details, dict) and "total" in details:
                    print(f"    Tests: {details['total']} total, {details['passed']} passed, {details['failed']} failed")
        
        # Save report
        report_file = self.output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        # Create HTML report
        self.generate_html_report(report_file)
    
    def generate_html_report(self, json_report_path: Path):
        """Generate an HTML report from the JSON data"""
        html_path = json_report_path.with_suffix('.html')
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Certify Studio Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .passed {{ color: #27ae60; font-weight: bold; }}
        .failed {{ color: #e74c3c; font-weight: bold; }}
        .suite {{ background-color: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Certify Studio Test Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <table>
            <tr><td>Total Test Suites:</td><td>{self.results['summary']['total_suites']}</td></tr>
            <tr><td>Passed:</td><td class="passed">{self.results['summary']['passed_suites']}</td></tr>
            <tr><td>Failed:</td><td class="failed">{self.results['summary']['failed_suites']}</td></tr>
            <tr><td>Total Duration:</td><td>{self.results['summary']['total_time']:.2f}s</td></tr>
        </table>
    </div>
    
    <h2>Test Suites</h2>
    {"".join(self._generate_suite_html(suite) for suite in self.results['test_suites'])}
</body>
</html>
"""
        
        with open(html_path, "w") as f:
            f.write(html_content)
        
        print(f"HTML report saved to: {html_path}")
    
    def _generate_suite_html(self, suite: Dict[str, Any]) -> str:
        """Generate HTML for a test suite"""
        status_class = "passed" if suite.get("passed", False) else "failed"
        status_text = "PASSED" if suite.get("passed", False) else "FAILED"
        
        details_html = ""
        if "details" in suite and isinstance(suite["details"], dict):
            details = suite["details"]
            if "total" in details:
                details_html = f"""
                <p>Total: {details['total']}, 
                   Passed: <span class="passed">{details['passed']}</span>, 
                   Failed: <span class="failed">{details['failed']}</span>,
                   Skipped: {details.get('skipped', 0)}</p>
                """
        
        return f"""
        <div class="suite">
            <h3>{suite['name']} - <span class="{status_class}">{status_text}</span></h3>
            <p>Duration: {suite['duration']:.2f}s</p>
            {details_html}
        </div>
        """
    
    async def run_all_tests(self):
        """Run all test suites"""
        self.print_header("CERTIFY STUDIO - COMPREHENSIVE TEST SUITE")
        
        # Check prerequisites
        if not await self.check_prerequisites():
            self.print_warning("\nSome prerequisites are not met. Tests may fail.")
            response = input("\nContinue anyway? (y/n): ")
            if response.lower() != 'y':
                print("Test run cancelled.")
                return
        
        # Run test suites
        test_suites = [
            ("Unit Tests", self.run_unit_tests),
            ("Integration Tests", self.run_integration_tests),
            ("Performance Tests", self.run_performance_tests),
            ("E2E Tests", self.run_e2e_tests),
        ]
        
        for suite_name, suite_func in test_suites:
            try:
                result = await suite_func()
                self.results["test_suites"].append(result)
            except Exception as e:
                self.print_failure(f"{suite_name} crashed: {e}")
                self.results["test_suites"].append({
                    "name": suite_name,
                    "passed": False,
                    "error": str(e),
                    "duration": 0
                })
        
        # Generate report
        self.generate_report()
        
        # Return exit code
        return 0 if self.results["summary"]["failed_suites"] == 0 else 1


async def main():
    """Main entry point"""
    runner = TestRunner()
    exit_code = await runner.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
