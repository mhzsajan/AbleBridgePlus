# Enhanced AbletonBridge Tests

This directory contains tests for Enhanced AbletonBridge.

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_validation.py

# Run with verbose output
pytest -v
```

## Test Structure

- `test_validation.py` - Input validation tests
- `test_tools.py` - Tool function tests
- `test_connections.py` - Connection tests

## Writing Tests

When adding new features, add corresponding tests:

1. Create a new test file: `test_<feature>.py`
2. Write test functions using pytest
3. Run tests to verify functionality

## Test Guidelines

- Test both success and error cases
- Use descriptive test names
- Mock external dependencies (Ableton, M4L)
- Aim for high coverage of critical paths
