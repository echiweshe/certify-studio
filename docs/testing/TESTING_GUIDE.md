# Certify Studio Testing Guide

## Overview

This guide covers the comprehensive testing strategy for Certify Studio, including unit tests, integration tests, and end-to-end tests using real AWS AI Practitioner certification materials.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   └── test_agents.py      # Tests for all agent functionality
├── integration/            # Integration tests for agent collaboration
│   ├── test_agent_collaboration.py
│   └── test_agent_monitoring.py
├── e2e/                    # End-to-end workflow tests
│   ├── test_aws_ai_practitioner_workflow.py
│   └── test_aws_certification_complete.py
├── fixtures/               # Test data and fixtures
├── conftest.py            # Pytest configuration
└── run_all_tests.py       # Master test runner
```

## Running Tests

### Quick Start

Run the complete test suite:
```bash
# From project root
run_complete_tests.bat
```

### Running Specific Test Categories

```bash
# Run only unit tests
cd tests
python run_all_tests.py
# Select option 2

# Run only integration tests
python run_all_tests.py
# Select option 3

# Run only e2e tests
python run_all_tests.py
# Select option 4
```

### Running Individual Test Files

```bash
# Run a specific test file
cd tests
pytest unit/test_agents.py -v

# Run with specific test function
pytest unit/test_agents.py::TestContentGenerationAgent::test_content_generation_simple -v
```

## Test Categories

### 1. Unit Tests (`unit/test_agents.py`)

Tests individual agent functionality in isolation:

- **ContentGenerationAgent Tests**
  - Agent initialization
  - Simple content generation
  - Cognitive load calculation
  - Response time validation

- **QualityAssuranceAgent Tests**
  - Content validation logic
  - Accessibility checking
  - Scoring algorithms

- **DomainExtractionAgent Tests**
  - Domain extraction from text
  - Concept identification
  - Weight calculation

- **ExportAgent Tests**
  - PDF export functionality
  - HTML export with markdown
  - SCORM package generation

### 2. Integration Tests

#### Agent Collaboration (`integration/test_agent_collaboration.py`)
- Content generation → QA validation pipeline
- Domain extraction → Content generation flow
- Full pipeline with export
- Error handling between agents
- GraphRAG integration

#### Agent Monitoring (`integration/test_agent_monitoring.py`)
- Real-time WebSocket monitoring
- Agent status visualization
- Collaboration event tracking
- Performance metrics dashboard

### 3. End-to-End Tests

#### AWS Certification Workflow (`e2e/test_aws_ai_practitioner_workflow.py`)
Complete workflow using actual AWS materials:
1. Server health check
2. User authentication
3. PDF upload (AWS Exam Guide)
4. Domain extraction
5. Content generation
6. Progress monitoring
7. Quality assurance
8. Multi-format export
9. WebSocket real-time updates

#### Comprehensive E2E (`e2e/test_aws_certification_complete.py`)
- Full certification workflow
- Course material processing
- Concurrent workflow handling
- Performance testing
- Throughput validation

## Test Data

### AWS Certification Materials
Located in `downloads/aws/AIF-C01/`:
- `AWS-Certified-AI-Practitioner_Exam-Guide.pdf`
- `Secitons-1-to-7-AI1-C01-Official-Course.pdf`

These real materials are used for realistic testing of:
- PDF processing capabilities
- Domain extraction accuracy
- Content generation quality
- Export formatting

## Test Configuration

### Environment Variables
Set in `.env` for testing:
```env
TESTING=true
LOG_LEVEL=DEBUG
TEST_TIMEOUT=300
```

### Pytest Configuration
In `pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

## Writing New Tests

### Unit Test Template
```python
class TestNewAgent:
    @pytest.fixture
    async def agent(self):
        settings = Settings()
        agent = NewAgent(settings)
        await agent.initialize()
        yield agent
        await agent.shutdown()
    
    @pytest.mark.asyncio
    async def test_agent_function(self, agent):
        result = await agent.some_function()
        assert result is not None
```

### Integration Test Template
```python
@pytest.mark.asyncio
async def test_agent_integration(agents):
    # Test multiple agents working together
    result1 = await agents["agent1"].process()
    result2 = await agents["agent2"].validate(result1)
    assert result2["success"]
```

### E2E Test Template
```python
@pytest.mark.asyncio
async def test_complete_workflow(session, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Upload
    # Process
    # Validate
    # Export
    assert all_steps_successful
```

## Performance Benchmarks

Expected performance metrics:
- Unit tests: < 5 seconds per test
- Integration tests: < 30 seconds per test
- E2E tests: < 5 minutes per workflow
- API response time: < 1 second for queries
- Generation time: < 2 minutes for standard PDF
- Throughput: > 10 requests/second

## Continuous Integration

Tests are run automatically on:
- Every commit to main branch
- Pull request creation
- Nightly builds
- Release candidates

## Troubleshooting

### Common Issues

1. **Backend not starting**
   - Check if port 8000 is free
   - Verify Python environment is activated
   - Check logs in `logs/` directory

2. **Test timeouts**
   - Increase timeout in test configuration
   - Check if agents are initializing properly
   - Verify database connections

3. **Import errors**
   - Ensure project root is in PYTHONPATH
   - Check virtual environment activation
   - Verify all dependencies installed

### Debug Mode

Run tests with verbose output:
```bash
pytest -vvs --log-cli-level=DEBUG
```

## Test Reports

Test results are saved to:
- `tests/test_report_YYYYMMDD_HHMMSS.json`
- Contains detailed results for each test
- Includes timing information
- Success/failure summary

## Contributing

When adding new features:
1. Write unit tests first (TDD)
2. Add integration tests for agent interactions
3. Create E2E test for complete workflow
4. Ensure all tests pass before committing
5. Update test documentation

## Coverage Requirements

Minimum coverage targets:
- Unit tests: 80% code coverage
- Integration tests: 60% coverage
- E2E tests: Critical paths covered

Run coverage report:
```bash
pytest --cov=certify_studio --cov-report=html
```

## Test Priorities

### P0 - Critical (Must Pass)
- Authentication flow
- PDF upload and processing
- Content generation pipeline
- Export functionality

### P1 - Important
- Agent collaboration
- Quality validation
- Real-time updates
- Performance metrics

### P2 - Nice to Have
- Advanced visualizations
- Edge case handling
- Stress testing

## Monitoring Tests in Production

### Health Checks
- `/health` endpoint monitoring
- Agent status validation
- Database connectivity
- External service availability

### Performance Monitoring
- Response time tracking
- Memory usage monitoring
- CPU utilization
- Queue depths

### Error Tracking
- Failed generation tracking
- Agent error rates
- API error responses
- System exceptions

## Best Practices

1. **Test Isolation**
   - Each test should be independent
   - Clean up test data after execution
   - Use fixtures for common setup

2. **Meaningful Assertions**
   - Test behavior, not implementation
   - Use descriptive assertion messages
   - Verify both positive and negative cases

3. **Performance Considerations**
   - Mock external services when possible
   - Use test databases
   - Parallelize independent tests

4. **Documentation**
   - Document test purpose
   - Include examples in docstrings
   - Update when behavior changes

## Future Enhancements

1. **Visual Regression Testing**
   - Screenshot comparisons
   - Animation validation
   - UI consistency checks

2. **Load Testing**
   - Concurrent user simulation
   - Stress test scenarios
   - Performance profiling

3. **Security Testing**
   - Penetration testing
   - Authentication bypass attempts
   - Input validation testing

4. **Accessibility Testing**
   - WCAG compliance validation
   - Screen reader compatibility
   - Keyboard navigation testing
