@echo off
echo ========================================
echo Running Comprehensive Test Suite
echo ========================================
echo.

cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio

echo Starting comprehensive test runner...
echo This will run all test categories:
echo - Unit Tests
echo - Integration Tests
echo - End-to-End Tests
echo - Performance Tests
echo.

uv run python tests\run_comprehensive_tests.py

echo.
echo ========================================
echo All Tests Complete!
echo Check tests\outputs\ for detailed reports
echo ========================================
pause
