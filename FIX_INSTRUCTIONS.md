# Fix Import Issues and Run Tests

## Problem
The tests are failing due to missing langchain dependencies. The error shows:
```
ModuleNotFoundError: No module named 'langchain_community'
```

## Solution Steps

### 1. Install Missing Dependencies
Run this command to install all missing langchain packages:
```bash
uv add langchain-anthropic langchain-openai langchain-core langchain-community anthropic
```

### 2. Sync Dependencies
After adding packages, sync all dependencies:
```bash
uv sync
```

### 3. Run Tests
Now run the tests:
```bash
uv run pytest tests/unit/test_simple.py -v
```

## Alternative: Run the Fix Script
We've created a script that does all of this automatically:
```bash
python fix_deps_and_run.py
```

## Debugging
If tests still fail, run the import test script to see which specific imports are failing:
```bash
python test_imports.py
```

## What We Fixed
1. Updated imports in `multimodal_llm.py` to use the new langchain package structure
2. Fixed the __init__.py file in the integration module
3. Added all necessary langchain packages to pyproject.toml
4. Updated API key parameter names for langchain models

## Next Steps After Tests Pass
1. Run all unit tests: `uv run pytest tests/unit/ -v`
2. Run integration tests: `uv run pytest tests/integration/ -v`
3. Run end-to-end tests: `uv run pytest tests/e2e/ -v`
4. Generate coverage report: `uv run pytest --cov=certify_studio --cov-report=html`

## Expected Output
When everything is working correctly, you should see:
```
tests/unit/test_simple.py::test_simple PASSED
tests/unit/test_simple.py::test_import PASSED
======================= 2 passed in X.XXs =======================
```
