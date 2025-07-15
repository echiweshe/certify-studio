# Certify Studio Testing Documentation

## Overview

This document outlines the comprehensive testing strategy for Certify Studio, including unit tests, integration tests, and end-to-end (E2E) tests. Our testing approach ensures the platform's reliability, performance, and quality.

## Test Structure

```
tests/
├── unit/               # Unit tests for individual components
│   ├── agents/        # Agent-specific tests
│   ├── api/           # API endpoint tests
│   └── core/          # Core functionality tests
├── integration/        # Integration tests
│   ├── test_agent_collaboration.py
│   ├── test_api_endpoints.py
│   └── test_agent_monitoring.py
├── e2e/               # End-to-end tests
│   ├── test_aws_ai_practitioner_complete.py
│   ├── test_complete_workflows.py
│   └── test_aws_certification_complete.py
├── fixtures/          # Test fixtures and data
├── test_backend_connectivity.py
└── run_comprehensive_tests.py
```

## Testing AWS AI Practitioner Certification

### Test Files
- **Exam Guide**: `downloads/aws/AIF-C01/AWS-Certified-AI-Practitioner_Exam-Guide.pdf`
- **Course Materials**: `downloads/aws/AIF-C01/Secitons-1-to-7-AI1-C01-Official-Course.pdf`
- **AWS Icons**: `downloads/aws/icons/Asset-Package_02072025.dee42cd0a6eaacc3da1ad9519579357fb546f803.zip`

### Test Workflow

1. **PDF Upload Test**
   - Upload exam guide PDF
   - Verify file processing
   - Check file metadata extraction

2. **Domain Extraction Test**
   - Extract certification domains
   - Validate domain weights
   - Verify concept relationships

3. **Content Generation Test**
   - Generate interactive content
   - Monitor agent collaboration
   - Track generation progress

4. **Quality Assurance Test**
   - Run pedagogical checks
   - Verify technical accuracy
   - Check accessibility compliance

5. **Export Test**
   - Export to multiple formats (PDF, SCORM, Video)
   - Verify export integrity
   - Check file downloads

## Running Tests

### Quick Start

```bash
# Test backend connectivity
python tests/test_backend_connectivity.py

# Run AWS AI Practitioner workflow test
test_aws_workflow.bat

# Run comprehensive test suite
run_comprehensive_tests.bat

# Run specific test category
python tests/run_comprehensive_tests.py --aws
```

### Prerequisites

1. **Backend Running**
   ```bash
   uv run uvicorn certify_studio.main:app --reload
   ```

2. **Database Connected**
   - SQLite database should be initialized
   - Run `init_database.bat` if needed

3. **Test Dependencies**
   ```bash
   uv pip install pytest pytest-asyncio httpx websocket-client
   ```

## Test Categories

### 1. Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Fast execution (< 1 second per test)
- Coverage target: 80%

### 2. Integration Tests
- Test component interactions
- Use real database connections
- Test API endpoints with authentication
- Verify agent communication

### 3. End-to-End Tests
- Complete workflow testing
- Real file uploads and processing
- Full agent orchestration
- Performance benchmarking

## Real-time Agent Data Connection

The `frontend_connector.py` module provides:

### WebSocket Endpoints
- `/ws/agents` - Real-time agent updates
- Agent state changes
- Generation progress
- Collaboration events

### REST Endpoints
- `/api/v1/frontend/dashboard` - Dashboard data
- `/api/v1/frontend/agents/collaboration` - Collaboration visualization
- `/api/v1/frontend/knowledge-graph` - Knowledge graph data

### Event Types
- `agent_update` - Agent state changes
- `generation_progress` - Generation progress updates
- `collaboration_event` - Agent collaboration events
- `task_completed` - Task completion notifications

## Performance Testing

### Load Testing
```python
# Run performance tests
python tests/run_comprehensive_tests.py --performance
```

### Metrics Tracked
- Response time (avg, min, max)
- Throughput (requests/second)
- Error rate
- Resource utilization

### Performance Targets
- API response time: < 200ms (p95)
- Generation completion: < 5 minutes
- Concurrent users: 100+
- Uptime: 99.9%

## Coverage Reports

Test coverage reports are generated in:
- HTML Report: `coverage_html_report/index.html`
- JSON Report: `test_reports/test_report_[timestamp].json`

## CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -r requirements.txt
          uv pip install -r requirements-test.txt
      - name: Run tests
        run: python tests/run_comprehensive_tests.py
```

## Debugging Tests

### Common Issues

1. **Backend Not Running**
   ```
   Error: Connection refused to localhost:8000
   Solution: Start backend with uv run uvicorn certify_studio.main:app --reload
   ```

2. **Database Not Initialized**
   ```
   Error: Database connection failed
   Solution: Run init_database.bat
   ```

3. **Missing Test Files**
   ```
   Error: Test PDF not found
   Solution: Ensure test PDFs are in downloads/aws/AIF-C01/
   ```

### Debug Mode

Run tests with verbose output:
```bash
pytest tests/e2e/test_aws_ai_practitioner_complete.py -v -s --log-cli-level=DEBUG
```

## Best Practices

1. **Test Isolation**
   - Each test should be independent
   - Clean up test data after execution
   - Use fixtures for setup/teardown

2. **Async Testing**
   - Use `pytest.mark.asyncio` for async tests
   - Properly await all async operations
   - Handle timeouts appropriately

3. **Mocking**
   - Mock external services (LLMs, etc.)
   - Use real implementations in E2E tests
   - Provide realistic mock data

4. **Assertions**
   - Be specific in assertions
   - Check both positive and negative cases
   - Verify error handling

## Test Data Management

### Fixtures
- User credentials: `test@certifystudio.com` / `TestPassword123!`
- Test PDFs: AWS certification materials
- Mock responses: Stored in `tests/fixtures/`

### Cleanup
- Tests automatically clean up created data
- Temporary files removed after tests
- Database rolled back for isolation

## Monitoring Test Health

### Metrics Dashboard
- Test pass rate
- Average execution time
- Coverage trends
- Flaky test detection

### Alerts
- Failed tests in main branch
- Coverage drops below threshold
- Performance regression
- Long-running tests

## Future Improvements

1. **Visual Regression Testing**
   - Screenshot comparisons
   - Animation validation
   - PDF rendering checks

2. **Chaos Engineering**
   - Random failure injection
   - Network latency simulation
   - Resource constraints

3. **Security Testing**
   - Penetration testing
   - OWASP compliance
   - Authentication bypass attempts

4. **Accessibility Testing**
   - WCAG 2.1 AA compliance
   - Screen reader compatibility
   - Keyboard navigation testing
   - Color contrast validation

5. **Mobile Testing**
   - Responsive design validation
   - Touch interaction testing
   - Mobile performance benchmarks

## Continuous Improvement

### Weekly Reviews
- Test failure analysis
- Performance trend review
- Coverage gap identification
- Test optimization opportunities

### Monthly Goals
- Increase coverage by 5%
- Reduce test execution time by 10%
- Zero flaky tests
- 100% critical path coverage

## Testing Commands Reference

```bash
# Backend connectivity test
python tests/test_backend_connectivity.py

# Run specific test file
pytest tests/e2e/test_aws_ai_practitioner_complete.py -v

# Run with coverage
pytest --cov=certify_studio --cov-report=html

# Run only unit tests
pytest tests/unit -v

# Run integration tests
pytest tests/integration -v

# Run E2E tests
pytest tests/e2e -v

# Run with specific marker
pytest -m "not slow" -v

# Run in parallel
pytest -n 4 -v

# Generate test report
pytest --json-report --json-report-file=report.json
```

## Test Markers

```python
@pytest.mark.slow  # Long-running tests
@pytest.mark.integration  # Integration tests
@pytest.mark.e2e  # End-to-end tests
@pytest.mark.unit  # Unit tests
@pytest.mark.asyncio  # Async tests
@pytest.mark.skip  # Skip test
@pytest.mark.xfail  # Expected failure
```

## Contributing to Tests

1. **Writing New Tests**
   - Follow existing patterns
   - Add docstrings
   - Use meaningful test names
   - Include both positive and negative cases

2. **Test Review Checklist**
   - ✓ Test is isolated
   - ✓ Assertions are specific
   - ✓ Error cases handled
   - ✓ Performance acceptable
   - ✓ Documentation updated

3. **Submitting Test PRs**
   - Run full test suite locally
   - Include test output in PR
   - Update coverage report
   - Document any new fixtures

---

**Last Updated**: January 2025
**Maintainer**: Certify Studio Team
**Version**: 1.0.0
