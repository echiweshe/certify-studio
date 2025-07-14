# Testing Guide for Certify Studio

## Overview

Certify Studio uses a comprehensive testing strategy with multiple layers:
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions with real database
- **End-to-End Tests**: Test complete user workflows

## Setup

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Database Setup

Tests use a separate test database. Set the environment variable:

```bash
export TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost/certify_studio_test"
```

### Running Tests

#### Using the Test Runner

```bash
# Run all tests
python run_tests.py all

# Run specific test types
python run_tests.py unit
python run_tests.py integration
python run_tests.py e2e

# Run with coverage
python run_tests.py coverage

# Run fast tests only (excludes slow e2e tests)
python run_tests.py fast

# Run specific test file
python run_tests.py specific tests/unit/test_models.py

# Watch mode (auto-rerun on changes)
python run_tests.py watch
```

#### Using pytest directly

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific markers
pytest -m unit
pytest -m integration
pytest -m e2e

# Run with coverage
pytest --cov=certify_studio --cov-report=html

# Run in parallel
pytest -n auto

# Run specific test
pytest tests/unit/test_models.py::TestUserModels::test_user_creation
```

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── unit/                # Unit tests
│   ├── test_models.py   # Database model tests
│   ├── test_services.py # Service layer tests
│   └── test_events.py   # Event system tests
├── integration/         # Integration tests
│   └── test_api.py      # API endpoint tests
└── e2e/                 # End-to-end tests
    └── test_workflows.py # Complete workflow tests
```

## Key Testing Concepts

### Fixtures

Common fixtures available in all tests:

- `db`: Database session for tests
- `test_user`: Regular user account
- `admin_user`: Admin user account
- `auth_headers`: Authorization headers for API requests
- `event_bus`: Event bus instance
- `mock_orchestrator`: Mocked agent orchestrator
- `sample_pdf_file`: Sample PDF for upload tests

### Markers

Tests are marked for easy filtering:

- `@pytest.mark.unit`: Unit tests (fast, isolated)
- `@pytest.mark.integration`: Integration tests (uses database)
- `@pytest.mark.e2e`: End-to-end tests (full workflows)
- `@pytest.mark.slow`: Slow running tests

### Mocking

We use `pytest-mock` for mocking:

```python
async def test_with_mock(mocker):
    # Mock external service
    mock_service = mocker.AsyncMock()
    mock_service.process.return_value = {"result": "success"}
    
    # Use in test
    result = await mock_service.process()
    assert result["result"] == "success"
```

## Writing Tests

### Unit Test Example

```python
@pytest.mark.unit
async def test_user_creation(db):
    """Test creating a user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed"
    )
    db.add(user)
    await db.commit()
    
    assert user.id is not None
    assert user.email == "test@example.com"
```

### Integration Test Example

```python
@pytest.mark.integration
async def test_api_endpoint(client, auth_headers):
    """Test API endpoint with database."""
    response = await client.get(
        "/api/v1/content/generations",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

### E2E Test Example

```python
@pytest.mark.e2e
@pytest.mark.slow
async def test_complete_workflow(client, auth_headers, sample_pdf):
    """Test complete generation workflow."""
    # Start generation
    response = await client.post(
        "/api/v1/content/generate",
        headers=auth_headers,
        files={"file": open(sample_pdf, "rb")},
        data={"title": "Test", "content_type": "full_certification"}
    )
    assert response.status_code == 200
    
    # Check status
    generation_id = response.json()["id"]
    response = await client.get(
        f"/api/v1/content/generations/{generation_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
```

## Test Data

### Using Factories

Create test data consistently:

```python
from tests.factories import UserFactory, GenerationFactory

# In tests
user = await UserFactory.create()
generation = await GenerationFactory.create(user=user)
```

### Database Transactions

Tests run in transactions that are rolled back:

```python
async def test_with_db(db):
    # All changes here are rolled back after test
    user = User(email="test@example.com")
    db.add(user)
    await db.commit()
    # User is removed after test completes
```

## Coverage

### Viewing Coverage Reports

After running tests with coverage:

```bash
# Generate HTML report
pytest --cov=certify_studio --cov-report=html

# View report
open htmlcov/index.html
```

### Coverage Goals

- Unit tests: >90% coverage
- Integration tests: >80% coverage
- Overall: >85% coverage

## Performance Testing

### Load Testing with Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class CertifyStudioUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def list_generations(self):
        self.client.get("/api/v1/content/generations")
    
    @task(3)
    def create_generation(self):
        self.client.post("/api/v1/content/generate", ...)
```

Run load tests:

```bash
locust -f locustfile.py --host=http://localhost:8000
```

## Debugging Tests

### Using pytest-pdb

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure
pytest -x --pdb
```

### Viewing SQL Queries

```python
# In conftest.py, set echo=True on engine
engine = create_async_engine(url, echo=True)
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      env:
        TEST_DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost/test
      run: |
        pytest --cov=certify_studio --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Use Fixtures**: Don't repeat setup code
3. **Mock External Services**: Tests shouldn't depend on external APIs
4. **Test One Thing**: Each test should verify one behavior
5. **Descriptive Names**: Test names should describe what they test
6. **Arrange-Act-Assert**: Structure tests clearly
7. **Clean Up**: Use fixtures that auto-cleanup

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure PostgreSQL is running
   - Check TEST_DATABASE_URL is set correctly
   - Verify database exists

2. **Async Test Errors**
   - Use `@pytest.mark.asyncio` or configure `asyncio_mode = auto`
   - Use `async def` for async tests

3. **Import Errors**
   - Ensure project is installed: `pip install -e .`
   - Check PYTHONPATH includes project root

4. **Slow Tests**
   - Use `@pytest.mark.slow` for slow tests
   - Run fast tests with `pytest -m "not slow"`
   - Consider using test database fixtures

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain >85% coverage
4. Add appropriate markers
5. Update this documentation

Happy Testing! 🧪✨
