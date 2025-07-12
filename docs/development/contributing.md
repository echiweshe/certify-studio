# Contributing to Certify Studio

Thank you for your interest in contributing to Certify Studio! This guide will help you get started with contributing to our mission of democratizing technical education.

## 🤝 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- **Be Respectful**: Treat everyone with respect and kindness
- **Be Inclusive**: Welcome newcomers and help them get started
- **Be Professional**: Focus on what is best for the community
- **Be Collaborative**: Work together to resolve conflicts

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Docker and Docker Compose
- Git

### Development Setup

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/certify-studio.git
   cd certify-studio
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Setup Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

5. **Start Development Environment**
   ```bash
   docker-compose up -d postgres redis
   cp .env.example .env
   # Edit .env with your configuration
   python -m uvicorn src.certify_studio.main:app --reload
   ```

## 📝 Development Workflow

### 1. Create a Feature Branch

```bash
# For features
git checkout -b feature/your-feature-name

# For bug fixes
git checkout -b bugfix/issue-description

# For documentation
git checkout -b docs/what-you-are-documenting
```

### 2. Make Your Changes

- Write clean, readable code
- Follow the existing code style
- Add type hints to all functions
- Write docstrings for all public methods
- Keep commits focused and atomic

### 3. Write Tests

- Every new feature needs tests
- Maintain or increase code coverage
- Test edge cases and error conditions

```bash
# Run tests
pytest tests/

# Run specific test
pytest tests/unit/test_specific.py::test_function

# Check coverage
pytest --cov=certify_studio tests/
```

### 4. Code Quality Checks

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/

# All checks at once
make lint
```

### 5. Update Documentation

- Update README if needed
- Add/update docstrings
- Update API documentation
- Add examples for new features

### 6. Commit Your Changes

```bash
# Use conventional commits
git commit -m "feat: add new animation pattern for AWS Lambda"
git commit -m "fix: resolve database connection timeout"
git commit -m "docs: update installation instructions"
git commit -m "test: add unit tests for diagram generator"
```

Commit Message Format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Test additions or modifications
- `chore:` Maintenance tasks

### 7. Push and Create Pull Request

```bash
git push origin your-branch-name
```

Then create a Pull Request on GitHub with:
- Clear title describing the change
- Detailed description of what and why
- Reference any related issues
- Screenshots for UI changes
- Test results

## 🏗️ Architecture Guidelines

### Agent Development

When creating new AI agents:

```python
# src/certify_studio/agents/your_agent.py
from typing import Dict, Any, List
from ..base_agent import BaseAgent

class YourAgent(BaseAgent):
    """
    Clear description of what this agent does.
    
    This agent is responsible for...
    """
    
    async def initialize(self) -> None:
        """Initialize agent resources."""
        await super().initialize()
        # Your initialization code
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and return results.
        
        Args:
            input_data: Dictionary containing...
            
        Returns:
            Dictionary containing...
            
        Raises:
            ValueError: If input is invalid
        """
        # Validate input
        self._validate_input(input_data)
        
        # Process
        result = await self._do_processing(input_data)
        
        # Validate output
        self._validate_output(result)
        
        return result
```

### Manim Extensions

When adding new animations:

```python
# src/certify_studio/manim_extensions/animations/your_animation.py
from manim import *
from ..constants import YOUR_PROVIDER_COLORS

class YourAnimation:
    """Animation patterns for specific provider/service."""
    
    @staticmethod
    def create_service_animation(config: Dict) -> AnimationGroup:
        """
        Create animation for service.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            AnimationGroup with all animations
        """
        animations = []
        
        # Create your animations
        # ...
        
        return AnimationGroup(*animations, lag_ratio=0.2)
```

### API Endpoints

When adding new endpoints:

```python
# src/certify_studio/api/v1/endpoints/your_endpoint.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ....core.dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/your-endpoint")
async def your_endpoint(
    data: YourRequestModel,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> YourResponseModel:
    """
    Clear description of endpoint.
    
    Args:
        data: Request data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Response model
        
    Raises:
        HTTPException: On errors
    """
    try:
        # Your logic here
        result = await process_data(data, db)
        return YourResponseModel.from_orm(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## 🧪 Testing Guidelines

### Unit Tests

```python
# tests/unit/test_your_feature.py
import pytest
from certify_studio.your_module import your_function

class TestYourFeature:
    """Test suite for your feature."""
    
    def test_normal_operation(self):
        """Test normal operation."""
        result = your_function("input")
        assert result == "expected"
        
    def test_edge_case(self):
        """Test edge cases."""
        with pytest.raises(ValueError):
            your_function("")
            
    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Test async operations."""
        result = await async_function()
        assert result is not None
```

### Integration Tests

```python
# tests/integration/test_your_integration.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_full_flow(client: AsyncClient):
    """Test complete user flow."""
    # Create resource
    response = await client.post("/api/v1/resource", json={...})
    assert response.status_code == 201
    
    # Verify creation
    resource_id = response.json()["id"]
    response = await client.get(f"/api/v1/resource/{resource_id}")
    assert response.status_code == 200
```

## 📚 Documentation Standards

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int = None) -> Dict[str, Any]:
    """
    Brief description of function.
    
    Longer description if needed, explaining the purpose
    and any important details about the function.
    
    Args:
        param1: Description of param1
        param2: Description of param2. Defaults to None.
        
    Returns:
        Dictionary containing:
            - key1: Description
            - key2: Description
            
    Raises:
        ValueError: When input is invalid
        RuntimeError: When processing fails
        
    Example:
        >>> result = function_name("test", 42)
        >>> print(result["key1"])
        "value1"
    """
```

### API Documentation

- Use FastAPI's automatic documentation
- Add detailed descriptions to endpoints
- Include example requests/responses
- Document all status codes

## 🎯 What We're Looking For

### High Priority Contributions

1. **AI Agent Implementations**
   - Domain extraction from PDFs
   - Content structure planning
   - Animation choreography
   - Quality validation agents

2. **Manim Animation Patterns**
   - Cloud service animations
   - Network flow visualizations
   - Security demonstrations
   - Database operations

3. **Frontend Components**
   - Upload interfaces
   - Progress tracking
   - Content preview
   - Export management

4. **Test Coverage**
   - Unit tests for agents
   - Integration tests for API
   - E2E tests for workflows

### Good First Issues

Look for issues labeled `good first issue`:
- Documentation improvements
- Simple bug fixes
- Test additions
- Code cleanup

## 🤔 Getting Help

### Resources

- **Documentation**: Start with `/docs`
- **Discord**: Join our community (link in README)
- **Issues**: Check existing issues
- **Discussions**: GitHub Discussions for questions

### Communication Channels

1. **GitHub Issues**: Bug reports and feature requests
2. **Pull Requests**: Code contributions
3. **Discussions**: General questions and ideas
4. **Discord**: Real-time help and community

## 🎉 Recognition

We value all contributions:
- Code contributions
- Documentation improvements
- Bug reports
- Feature suggestions
- Community help

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Invited to contributor meetings
- Given early access to new features

## 📋 Pull Request Checklist

Before submitting your PR, ensure:

- [ ] Code follows project style guide
- [ ] All tests pass locally
- [ ] New code has tests
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] PR description is detailed
- [ ] Related issues are referenced
- [ ] No merge conflicts

## 🚫 What Not to Do

- Don't commit sensitive data
- Don't break existing tests
- Don't ignore CI failures
- Don't submit huge PRs (split them up)
- Don't skip documentation
- Don't forget about backwards compatibility

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Certify Studio! Together, we're democratizing technical education and making a real difference in people's careers. 🚀
