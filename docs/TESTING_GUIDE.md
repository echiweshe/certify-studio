# Certify Studio Testing Guide

## Overview

This guide provides comprehensive documentation for testing Certify Studio, covering unit tests, integration tests, and end-to-end tests.

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── unit/                # Unit tests for individual components
│   ├── test_models.py   # Database model tests
│   ├── test_services.py # Service layer tests
│   ├── test_events.py   # Event system tests
│   └── agents/          # Agent-specific tests
├── integration/         # Integration tests with database
│   └── test_api.py      # API endpoint tests
├── e2e/                 # End-to-end workflow tests
│   └── test_workflows.py # Complete user journeys
└── fixtures/            # Test data and mocks
```

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py all

# Run specific test types
python run_tests.py unit
python run_tests.py integration
python run_tests.py e2e

# Run with coverage
python run_tests.py coverage

# Run fast tests only (exclude slow/e2e)
python run_tests.py fast

# Run specific test file
python run_tests.py specific tests/unit/test_models.py

# Watch mode for development
python run_tests.py watch
```

### Test Markers

Tests are marked with pytest markers for easy filtering:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (with database)
- `@pytest.mark.e2e` - End-to-end tests (complete workflows)
- `@pytest.mark.slow` - Slow tests (can be excluded)

## Test Categories

### 1. Unit Tests

Unit tests verify individual components in isolation.

#### Model Tests (`test_models.py`)
- User model creation and validation
- Content generation models
- Domain knowledge models
- Quality assurance models
- Analytics models
- Model relationships and methods

Example:
```python
async def test_user_creation(self, db):
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed",
        full_name="Test User"
    )
    db.add(user)
    await db.commit()
    
    assert user.id is not None
    assert user.is_active is True
```

#### Service Tests (`test_services.py`)
- Content generation service workflows
- User authentication and management
- Quality assurance processes
- Domain extraction logic
- Analytics calculations

Example:
```python
async def test_start_generation(self, service, test_user):
    generation = await service.start_generation(
        user=test_user,
        file_path="/test.pdf",
        title="Test Course",
        content_type=ContentType.MINI_COURSE
    )
    
    assert generation.status == GenerationStatus.PENDING
```

#### Event Tests (`test_events.py`)
- Event bus functionality
- Event handler registration
- Event emission and propagation
- Default handlers (logging, metrics)

Example:
```python
async def test_emit_event(self, event_bus):
    handler = AsyncMock()
    event_bus.register(EventType.GENERATION_STARTED, handler)
    
    event = ContentGenerationStartedEvent(...)
    await event_bus.emit(EventType.GENERATION_STARTED, event)
    
    handler.assert_called_once()
```

### 2. Integration Tests

Integration tests verify API endpoints with database integration.

#### API Tests (`test_api.py`)
- Authentication endpoints (register, login, refresh)
- Content generation endpoints
- Quality assurance endpoints
- Analytics endpoints
- Admin endpoints
- Error handling

Example:
```python
async def test_start_generation(self, client, auth_headers):
    response = await client.post(
        "/api/v1/content/generate",
        headers=auth_headers,
        files={"file": ("test.pdf", file_data, "application/pdf")},
        data={"title": "Test", "content_type": "mini_course"}
    )
    
    assert response.status_code == 201
```

### 3. End-to-End Tests

E2E tests verify complete user workflows.

#### Workflow Tests (`test_workflows.py`)
- Complete content generation flow
- User journey from registration
- Concurrent operations
- Error recovery scenarios
- Data consistency checks

Example:
```python
async def test_full_certification_generation(self, services):
    # Create user
    user = await services["user"].create_user(...)
    
    # Upload file and start generation
    generation = await services["content"].start_generation(...)
    
    # Process generation
    await services["content"].process_generation(generation.id)
    
    # Run quality checks
    quality = await services["quality"].run_quality_check(...)
    
    # Export content
    export = await services["content"].export_content(...)
    
    # Verify complete workflow
    assert generation.status == GenerationStatus.COMPLETED
```

## Test Fixtures

### Database Fixtures
- `db` - Async database session
- `engine` - Test database engine
- `test_user` - Pre-created test user
- `admin_user` - Admin user with permissions

### Authentication Fixtures
- `auth_headers` - JWT auth headers for test user
- `admin_headers` - JWT auth headers for admin

### Mock Fixtures
- `event_bus` - Event bus instance
- `mock_orchestrator` - Mocked agent orchestrator
- `mock_celery` - Mocked Celery for background tasks

### Helper Fixtures
- `helpers` - Test helper utilities
- `sample_pdf_file` - Sample PDF for testing
- `tmp_path` - Temporary directory (pytest builtin)

## Writing New Tests

### Unit Test Template

```python
@pytest.mark.unit
class TestNewComponent:
    """Test new component functionality."""
    
    @pytest.fixture
    def component(self):
        """Create component instance."""
        return NewComponent()
    
    async def test_component_method(self, component):
        """Test specific method."""
        result = await component.method(param="value")
        assert result.success is True
```

### Integration Test Template

```python
@pytest.mark.integration
class TestNewEndpoint:
    """Test new API endpoint."""
    
    async def test_endpoint_success(self, client, auth_headers):
        """Test successful request."""
        response = await client.post(
            "/api/v1/new/endpoint",
            headers=auth_headers,
            json={"param": "value"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
```

### E2E Test Template

```python
@pytest.mark.e2e
@pytest.mark.slow
class TestNewWorkflow:
    """Test complete workflow."""
    
    async def test_workflow(self, services):
        """Test end-to-end workflow."""
        # Setup
        user = await services["user"].create_user(...)
        
        # Execute workflow steps
        result = await services["content"].process_workflow(...)
        
        # Verify outcomes
        assert result.completed is True
```

## Best Practices

### 1. Test Isolation
- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order

### 2. Async Testing
- Use `pytest-asyncio` for async tests
- Always await async operations
- Use `AsyncMock` for mocking async functions

### 3. Database Testing
- Tests use transactions that auto-rollback
- Create test data in fixtures
- Don't modify shared test data

### 4. Mocking
- Mock external services (APIs, file systems)
- Use `mocker` fixture from pytest-mock
- Verify mock calls with assertions

### 5. Performance
- Mark slow tests with `@pytest.mark.slow`
- Keep unit tests fast (<1 second)
- Use fixtures to avoid repeated setup

## Coverage Goals

### Target Coverage
- Overall: 80%+
- Unit tests: 90%+
- Integration tests: 70%+
- Critical paths: 100%

### Viewing Coverage

```bash
# Generate coverage report
python run_tests.py coverage

# View HTML report
open htmlcov/index.html
```

### Coverage Configuration

```ini
# pytest.ini
[coverage:run]
source = certify_studio
omit = 
    */tests/*
    */migrations/*
    */__pycache__/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

## Continuous Integration

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
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/certify_studio_test
        REDIS_URL: redis://localhost:6379
      run: |
        python run_tests.py coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Ensure PostgreSQL is running
   docker-compose up -d postgres
   
   # Check connection
   psql postgresql://postgres:postgres@localhost/certify_studio_test
   ```

2. **Async Test Failures**
   ```python
   # Ensure proper async handling
   @pytest.mark.asyncio  # Don't forget this
   async def test_async():
       result = await async_function()  # Don't forget await
   ```

3. **Import Errors**
   ```bash
   # Ensure project is in PYTHONPATH
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   
   # Or install in development mode
   pip install -e .
   ```

4. **Slow Tests**
   ```bash
   # Skip slow tests during development
   pytest -m "not slow"
   
   # Run only fast unit tests
   python run_tests.py fast
   ```

## Test Data Management

### Creating Test Data

```python
# Use factories for complex objects
class GenerationFactory:
    @staticmethod
    async def create(
        user: User,
        status: GenerationStatus = GenerationStatus.PENDING,
        **kwargs
    ) -> ContentGeneration:
        generation = ContentGeneration(
            user_id=user.id,
            source_file_path=kwargs.get("file_path", "/test.pdf"),
            title=kwargs.get("title", "Test Generation"),
            content_type=kwargs.get("content_type", ContentType.MINI_COURSE),
            status=status
        )
        db.add(generation)
        await db.commit()
        return generation
```

### Test Data Cleanup

Tests automatically rollback transactions, but for file operations:

```python
@pytest.fixture
def cleanup_files():
    """Clean up test files after test."""
    files = []
    
    def register(filepath):
        files.append(filepath)
    
    yield register
    
    # Cleanup
    for filepath in files:
        if Path(filepath).exists():
            Path(filepath).unlink()
```

## Performance Testing

### Load Testing Example

```python
@pytest.mark.slow
async def test_concurrent_load(services):
    """Test system under load."""
    async def create_generation(index):
        return await services["content"].start_generation(
            user=test_user,
            file_path=f"/test{index}.pdf",
            title=f"Load Test {index}",
            content_type=ContentType.QUICK_REVIEW
        )
    
    # Create 50 concurrent generations
    tasks = [create_generation(i) for i in range(50)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify success rate
    successful = [r for r in results if not isinstance(r, Exception)]
    assert len(successful) / len(results) > 0.9  # 90% success rate
```

## Security Testing

### Authentication Tests

```python
async def test_unauthorized_access(client):
    """Test endpoints require authentication."""
    response = await client.get("/api/v1/content/generations")
    assert response.status_code == 401

async def test_invalid_token(client):
    """Test invalid JWT tokens are rejected."""
    headers = {"Authorization": "Bearer invalid.token.here"}
    response = await client.get("/api/v1/content/generations", headers=headers)
    assert response.status_code == 401
```

### Permission Tests

```python
async def test_user_cannot_access_others_content(client, auth_headers, other_user_generation):
    """Test users cannot access other users' content."""
    response = await client.get(
        f"/api/v1/content/generations/{other_user_generation.id}",
        headers=auth_headers
    )
    assert response.status_code == 403
```

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain or improve coverage
4. Update this documentation

Happy testing! 🧪✨
