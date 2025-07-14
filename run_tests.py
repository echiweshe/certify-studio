"""
Test runner script for Certify Studio.

Provides convenient commands for running different test suites.
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run a command and return exit code."""
    print(f"Running: {cmd}")
    return subprocess.call(cmd, shell=True)


def main():
    """Main test runner."""
    if len(sys.argv) < 2:
        print("""
Certify Studio Test Runner

Usage: python run_tests.py [command]

Commands:
  all              Run all tests
  unit             Run unit tests only
  integration      Run integration tests only
  e2e              Run end-to-end tests only
  coverage         Run with coverage report
  fast             Run fast tests only (no e2e)
  specific <path>  Run specific test file
  watch            Run tests in watch mode
  simple           Run simple test to verify setup

Examples:
  python run_tests.py unit
  python run_tests.py coverage
  python run_tests.py specific tests/unit/test_models.py
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Base pytest command
    base_cmd = "python -m pytest"
    
    if command == "all":
        # Run all tests
        cmd = f"{base_cmd} -v"
        
    elif command == "unit":
        # Run unit tests only
        cmd = f"{base_cmd} -v -m unit"
        
    elif command == "integration":
        # Run integration tests only
        cmd = f"{base_cmd} -v -m integration"
        
    elif command == "e2e":
        # Run e2e tests only
        cmd = f"{base_cmd} -v -m e2e"
        
    elif command == "coverage":
        # Run with coverage
        cmd = f"{base_cmd} -v --cov=certify_studio --cov-report=html --cov-report=term"
        
    elif command == "fast":
        # Run all except slow tests
        cmd = f"{base_cmd} -v -m 'not slow'"
        
    elif command == "specific":
        # Run specific test file
        if len(sys.argv) < 3:
            print("Error: Please specify test file path")
            sys.exit(1)
        test_path = sys.argv[2]
        cmd = f"{base_cmd} -v {test_path}"
        
    elif command == "watch":
        # Run in watch mode (requires pytest-watch)
        cmd = "ptw -- -v"
        
    elif command == "simple":
        # Run simple test to verify setup
        cmd = f"{base_cmd} -v tests/unit/test_simple.py"
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    # Run the command
    exit_code = run_command(cmd)
    
    # Show coverage report location if coverage was run
    if command == "coverage" and exit_code == 0:
        print("\n✅ Coverage report generated!")
        print("📊 View HTML report: open htmlcov/index.html")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
