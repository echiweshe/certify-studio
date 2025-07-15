"""
Master Test Runner for Certify Studio
====================================
Orchestrates all testing workflows from organized test directories.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
import json
import os
from typing import List, Dict, Any

class MasterTestRunner:
    """Orchestrates all test suites"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        self.results = {
            "start_time": datetime.now().isoformat(),
            "tests_run": [],
            "summary": {}
        }
        
    def print_header(self, title: str):
        """Print formatted header"""
        print("\n" + "="*70)
        print(f" {title} ".center(70))
        print("="*70)
        
    def ensure_backend_running(self) -> bool:
        """Check if backend is running, start if needed"""
        import requests
        
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✅ Backend is already running")
                return True
        except:
            pass
            
        print("🚀 Starting backend server...")
        
        # Try different startup scripts
        startup_scripts = [
            self.project_root / "start_backend_test.bat",
            self.project_root / "start.bat",
            self.project_root / "start_server.bat"
        ]
        
        for script in startup_scripts:
            if script.exists():
                subprocess.Popen(
                    ["cmd", "/c", str(script)],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                break
        else:
            print("❌ No startup script found")
            return False
            
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        for i in range(30):  # 30 seconds timeout
            try:
                response = requests.get("http://localhost:8000/health", timeout=1)
                if response.status_code == 200:
                    print("✅ Backend started successfully!")
                    return True
            except:
                pass
            time.sleep(1)
            
        print("❌ Failed to start backend server")
        return False
        
    async def run_unit_tests(self) -> Dict[str, Any]:
        """Run all unit tests"""
        self.print_header("UNIT TESTS")
        
        unit_test_dir = self.test_dir / "unit"
        test_files = list(unit_test_dir.glob("test_*.py"))
        
        if not test_files:
            print("❌ No unit test files found")
            return {"success": False, "tests": 0}
            
        print(f"Found {len(test_files)} unit test files")
        
        # Run pytest on unit test directory
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(unit_test_dir), 
             "-v", "--tb=short", "--asyncio-mode=auto"],
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")
            
        success = result.returncode == 0
        
        # Parse test count from output
        test_count = 0
        if "passed" in result.stdout:
            import re
            match = re.search(r'(\d+) passed', result.stdout)
            if match:
                test_count = int(match.group(1))
                
        return {
            "success": success,
            "tests": test_count,
            "output": result.stdout
        }
        
    async def run_integration_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        self.print_header("INTEGRATION TESTS")
        
        integration_test_dir = self.test_dir / "integration"
        test_files = list(integration_test_dir.glob("test_*.py"))
        
        if not test_files:
            print("❌ No integration test files found")
            return {"success": False, "tests": 0}
            
        print(f"Found {len(test_files)} integration test files")
        
        # Run pytest on integration test directory
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(integration_test_dir),
             "-v", "--tb=short", "--asyncio-mode=auto"],
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")
            
        success = result.returncode == 0
        
        # Parse test count
        test_count = 0
        if "passed" in result.stdout:
            import re
            match = re.search(r'(\d+) passed', result.stdout)
            if match:
                test_count = int(match.group(1))
                
        return {
            "success": success,
            "tests": test_count,
            "output": result.stdout
        }
        
    async def run_e2e_tests(self) -> Dict[str, Any]:
        """Run all end-to-end tests"""
        self.print_header("END-TO-END TESTS")
        
        e2e_test_dir = self.test_dir / "e2e"
        test_files = list(e2e_test_dir.glob("test_*.py"))
        
        if not test_files:
            print("❌ No e2e test files found")
            return {"success": False, "tests": 0}
            
        print(f"Found {len(test_files)} e2e test files")
        
        # Run pytest on e2e test directory
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(e2e_test_dir),
             "-v", "--tb=short", "--asyncio-mode=auto", "-s"],
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")
            
        success = result.returncode == 0
        
        # Parse test count
        test_count = 0
        if "passed" in result.stdout:
            import re
            match = re.search(r'(\d+) passed', result.stdout)
            if match:
                test_count = int(match.group(1))
                
        return {
            "success": success,
            "tests": test_count,
            "output": result.stdout
        }
        
    async def run_specific_test_file(self, test_file: Path) -> Dict[str, Any]:
        """Run a specific test file"""
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return {"success": False, "tests": 0}
            
        print(f"Running {test_file.name}...")
        
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_file),
             "-v", "--tb=short", "--asyncio-mode=auto"],
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")
            
        return {
            "success": result.returncode == 0,
            "output": result.stdout
        }
        
    def generate_report(self):
        """Generate comprehensive test report"""
        self.print_header("TEST REPORT")
        
        # Calculate totals
        total_suites = len(self.results["tests_run"])
        passed_suites = sum(1 for t in self.results["tests_run"] if t["success"])
        failed_suites = total_suites - passed_suites
        
        total_tests = sum(t.get("test_count", 0) for t in self.results["tests_run"])
        
        self.results["summary"] = {
            "total_suites": total_suites,
            "passed_suites": passed_suites,
            "failed_suites": failed_suites,
            "total_tests": total_tests,
            "success_rate": (passed_suites / total_suites * 100) if total_suites > 0 else 0,
            "end_time": datetime.now().isoformat()
        }
        
        print(f"\n📊 SUMMARY:")
        print(f"  Test Suites Run: {total_suites}")
        print(f"  Suites Passed: {passed_suites} ✅")
        print(f"  Suites Failed: {failed_suites} ❌")
        print(f"  Total Tests: {total_tests}")
        print(f"  Success Rate: {self.results['summary']['success_rate']:.1f}%")
        
        # Show failed tests
        if failed_suites > 0:
            print(f"\n❌ FAILED SUITES:")
            for test in self.results["tests_run"]:
                if not test["success"]:
                    print(f"  - {test['name']}")
        
        # Save detailed report
        report_file = self.test_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Overall verdict
        if passed_suites == total_suites:
            print("\n🎉 ALL TEST SUITES PASSED! System is production-ready!")
        elif self.results['summary']['success_rate'] >= 80:
            print("\n✅ Most tests passed. System is mostly functional.")
        else:
            print("\n❌ Many tests failed. System needs attention.")
            
    async def run_all_tests(self):
        """Run all test suites in order"""
        self.print_header("CERTIFY STUDIO - COMPLETE TEST SUITE")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Directory: {self.test_dir}")
        
        # Ensure pytest is installed
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"], 
                      capture_output=True)
        
        # Ensure backend is running
        if not self.ensure_backend_running():
            print("❌ Cannot proceed without backend. Please start it manually.")
            return
            
        # Give backend time to fully initialize
        print("\n⏳ Waiting for backend to fully initialize...")
        await asyncio.sleep(5)
        
        # Run test suites in order
        test_suites = [
            ("Unit Tests", self.run_unit_tests),
            ("Integration Tests", self.run_integration_tests),
            ("End-to-End Tests", self.run_e2e_tests)
        ]
        
        for name, test_func in test_suites:
            try:
                result = await test_func()
                self.results["tests_run"].append({
                    "name": name,
                    "success": result["success"],
                    "test_count": result.get("tests", 0),
                    "output": result.get("output", "")
                })
            except Exception as e:
                print(f"❌ Error in {name}: {e}")
                self.results["tests_run"].append({
                    "name": name,
                    "success": False,
                    "test_count": 0,
                    "error": str(e)
                })
                
        # Generate report
        self.generate_report()

async def main():
    """Main entry point"""
    runner = MasterTestRunner()
    
    print("🧪 CERTIFY STUDIO TEST RUNNER")
    print("\nSelect test option:")
    print("1. Run ALL tests (Unit + Integration + E2E)")
    print("2. Run Unit tests only")
    print("3. Run Integration tests only")
    print("4. Run E2E tests only")
    print("5. Run AWS Certification workflow test")
    print("6. Run Agent monitoring test")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    if choice == "1":
        await runner.run_all_tests()
    elif choice == "2":
        if runner.ensure_backend_running():
            result = await runner.run_unit_tests()
            runner.results["tests_run"].append({
                "name": "Unit Tests",
                "success": result["success"],
                "test_count": result.get("tests", 0)
            })
            runner.generate_report()
    elif choice == "3":
        if runner.ensure_backend_running():
            result = await runner.run_integration_tests()
            runner.results["tests_run"].append({
                "name": "Integration Tests",
                "success": result["success"],
                "test_count": result.get("tests", 0)
            })
            runner.generate_report()
    elif choice == "4":
        if runner.ensure_backend_running():
            result = await runner.run_e2e_tests()
            runner.results["tests_run"].append({
                "name": "E2E Tests",
                "success": result["success"],
                "test_count": result.get("tests", 0)
            })
            runner.generate_report()
    elif choice == "5":
        if runner.ensure_backend_running():
            test_file = runner.test_dir / "e2e" / "test_aws_ai_practitioner_workflow.py"
            result = await runner.run_specific_test_file(test_file)
            runner.results["tests_run"].append({
                "name": "AWS Certification Workflow",
                "success": result["success"]
            })
            runner.generate_report()
    elif choice == "6":
        if runner.ensure_backend_running():
            test_file = runner.test_dir / "integration" / "test_agent_monitoring.py"
            # Run with interaction
            proc = subprocess.Popen(
                [sys.executable, str(test_file)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = proc.communicate(input="2\n")  # Select visualization
            print(stdout)
            if stderr:
                print(f"Errors: {stderr}")
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    asyncio.run(main())
