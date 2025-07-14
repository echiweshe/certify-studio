#!/usr/bin/env python
"""
Test Runner for Certify Studio

This script provides a convenient way to run tests with various options.
"""

import sys
import subprocess
import argparse
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


def run_command(cmd: list, check: bool = True) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run tests for Certify Studio")
    parser.add_argument(
        "type",
        choices=["all", "unit", "integration", "e2e", "coverage", "quick"],
        default="all",
        nargs="?",
        help="Type of tests to run"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-x", "--exitfirst",
        action="store_true",
        help="Exit on first failure"
    )
    parser.add_argument(
        "-k", "--keyword",
        help="Run tests matching keyword"
    )
    parser.add_argument(
        "-n", "--numprocesses",
        type=int,
        default=4,
        help="Number of parallel processes"
    )
    parser.add_argument(
        "--no-cov",
        action="store_true",
        help="Disable coverage"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run tests in watch mode (rerun on file changes)"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")
    
    # Exit on first failure
    if args.exitfirst:
        cmd.append("-x")
    
    # Keyword filter
    if args.keyword:
        cmd.extend(["-k", args.keyword])
    
    # Coverage options
    if not args.no_cov:
        cmd.extend([
            "--cov=certify_studio",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
        if args.html:
            cmd.append("--cov-report=html")
    
    # Test type selection
    if args.type == "unit":
        cmd.extend(["-m", "unit", "tests/unit"])
    elif args.type == "integration":
        cmd.extend(["-m", "integration", "tests/integration"])
    elif args.type == "e2e":
        cmd.extend(["-m", "e2e", "tests/e2e"])
    elif args.type == "quick":
        # Quick tests - unit tests only, no slow tests
        cmd.extend(["-m", "unit and not slow", "tests/unit"])
        args.numprocesses = 8  # More parallel for quick tests
    elif args.type == "coverage":
        # Full coverage run
        cmd.extend([
            "--cov=certify_studio",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
            "--cov-fail-under=80"  # Fail if coverage < 80%
        ])
    
    # Parallel execution (not for e2e tests)
    if args.numprocesses > 1 and args.type not in ["e2e", "integration"]:
        cmd.extend(["-n", str(args.numprocesses)])
    
    # Watch mode
    if args.watch:
        # Use pytest-watch if available
        watch_cmd = ["ptw", "--"] + cmd[1:]  # Remove 'pytest' from cmd
        result = run_command(["which", "ptw"], check=False)
        if result == 0:
            run_command(watch_cmd)
        else:
            print("pytest-watch not installed. Install with: pip install pytest-watch")
            sys.exit(1)
    else:
        run_command(cmd)


if __name__ == "__main__":
    main()
