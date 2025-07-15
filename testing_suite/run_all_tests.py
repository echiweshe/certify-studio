"""
Master Test Runner for Certify Studio
====================================
Orchestrates all testing workflows and provides comprehensive reports.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
import json
import os

class MasterTestRunner:
    """Orchestrates all test suites"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent
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
        
        # Start backend in a new process
        backend_script = self.project_root / "start_backend_test.bat"
        if backend_script.exists():
            subprocess.Popen(
                ["cmd", "/c", str(backend_script)],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
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
        
    async def run_aws_workflow_test(self):
        """Run AWS AI Practitioner workflow test"""
        self.print_header("AWS AI PRACTITIONER WORKFLOW TEST")
        
        test_file = self.test_dir / "test_aws_ai_practitioner_workflow.py"
        
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return False
            
        try:
            # Run the test
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            if result.stderr:
                print(f"Errors: {result.stderr}")
                
            success = result.returncode == 0
            self.results["tests_run"].append({
                "name": "AWS Workflow Test",
                "success": success,
                "output": result.stdout
            })
            
            return success
            
        except Exception as e:
            print(f"❌ Error running AWS workflow test: {e}")
            return False
            
    async def run_agent_monitoring(self):
        """Run agent monitoring tests"""
        self.print_header("AGENT MONITORING AND COLLABORATION TEST")
        
        test_file = self.test_dir / "monitor_agent_data.py"
        
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return False
            
        try:
            # Run agent visualization (option 2)
            proc = subprocess.Popen(
                [sys.executable, str(test_file)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Select option 2 (visualization)
            stdout, stderr = proc.communicate(input="2\n", timeout=10)
            
            print(stdout)
            if stderr:
                print(f"Errors: {stderr}")
                
            success = proc.returncode == 0
            self.results["tests_run"].append({
                "name": "Agent Monitoring",
                "success": success,
                "output": stdout
            })
            
            return success
            
        except Exception as e:
            print(f"❌ Error running agent monitoring: {e}")
            return False
            
    async def run_comprehensive_tests(self):
        """Run comprehensive test suite"""
        self.print_header("COMPREHENSIVE TEST SUITE")
        
        test_file = self.test_dir / "comprehensive_tests.py"
        
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return False
            
        try:
            # Run pytest
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            print(result.stdout)
            if result.stderr:
                print(f"Errors: {result.stderr}")
                
            success = result.returncode == 0
            self.results["tests_run"].append({
                "name": "Comprehensive Tests",
                "success": success,
                "output": result.stdout
            })
            
            return success
            
        except Exception as e:
            print(f"❌ Error running comprehensive tests: {e}")
            return False
            
    def generate_report(self):
        """Generate test report"""
        self.print_header("TEST REPORT")
        
        total_tests = len(self.results["tests_run"])
        passed_tests = sum(1 for t in self.results["tests_run"] if t["success"])
        failed_tests = total_tests - passed_tests
        
        self.results["summary"] = {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "end_time": datetime.now().isoformat()
        }
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total Test Suites: {total_tests}")
        print(f"  Passed: {passed_tests} ✅")
        print(f"  Failed: {failed_tests} ❌")
        print(f"  Success Rate: {self.results['summary']['success_rate']:.1f}%")
        
        # Save detailed report
        report_file = self.test_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Overall verdict
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! System is production-ready!")
        elif self.results['summary']['success_rate'] >= 80:
            print("\n✅ Most tests passed. System is mostly functional.")
        else:
            print("\n❌ Many tests failed. System needs attention.")
            
    async def run_all_tests(self):
        """Run all test suites"""
        self.print_header("CERTIFY STUDIO - MASTER TEST RUNNER")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Ensure backend is running
        if not self.ensure_backend_running():
            print("❌ Cannot proceed without backend. Please start it manually.")
            return
            
        # Give backend time to fully initialize
        print("\n⏳ Waiting for backend to fully initialize...")
        await asyncio.sleep(5)
        
        # Run test suites
        test_suites = [
            ("AWS Workflow Test", self.run_aws_workflow_test),
            ("Agent Monitoring", self.run_agent_monitoring),
            ("Comprehensive Tests", self.run_comprehensive_tests)
        ]
        
        for name, test_func in test_suites:
            try:
                await test_func()
            except Exception as e:
                print(f"❌ Error in {name}: {e}")
                self.results["tests_run"].append({
                    "name": name,
                    "success": False,
                    "output": str(e)
                })
                
        # Generate report
        self.generate_report()

async def main():
    """Main entry point"""
    runner = MasterTestRunner()
    
    print("🧪 CERTIFY STUDIO TEST SUITE")
    print("\nSelect test option:")
    print("1. Run ALL tests (recommended)")
    print("2. AWS Workflow Test only")
    print("3. Agent Monitoring only")
    print("4. Comprehensive Tests only")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        await runner.run_all_tests()
    elif choice == "2":
        if runner.ensure_backend_running():
            await runner.run_aws_workflow_test()
            runner.generate_report()
    elif choice == "3":
        if runner.ensure_backend_running():
            await runner.run_agent_monitoring()
            runner.generate_report()
    elif choice == "4":
        if runner.ensure_backend_running():
            await runner.run_comprehensive_tests()
            runner.generate_report()
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    asyncio.run(main())
