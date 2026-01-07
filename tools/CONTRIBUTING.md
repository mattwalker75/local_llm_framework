# Contributing to Local LLM Framework

Thank you for your interest in contributing to the Local LLM Framework (LLF)! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [How to Contribute](#how-to-contribute)
5. [Coding Standards](#coding-standards)
6. [Testing Requirements](#testing-requirements)
7. [Documentation](#documentation)
8. [Pull Request Process](#pull-request-process)
9. [Tool Development Guidelines](#tool-development-guidelines)
10. [Release Process](#release-process)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of:
- Experience level
- Background
- Identity
- Technology preferences

### Expected Behavior

- Be respectful and considerate in communication
- Provide constructive feedback
- Accept constructive criticism gracefully
- Focus on what's best for the project and community
- Show empathy towards other contributors

### Unacceptable Behavior

- Harassment, discrimination, or intimidation
- Trolling, insulting comments, or personal attacks
- Publishing others' private information
- Other conduct considered inappropriate in a professional setting

## Getting Started

### Prerequisites

Before contributing, ensure you have:

```bash
# Python 3.8 or higher
python --version

# Git
git --version

# pip (package manager)
pip --version
```

### Fork and Clone

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/local_llm_framework.git
   cd local_llm_framework
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/local_llm_framework.git
   ```

4. **Verify remotes**:
   ```bash
   git remote -v
   ```

## Development Setup

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 2. Install Development Dependencies

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Or install requirements manually
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Install Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

### 4. Verify Installation

```bash
# Run tests to verify setup
pytest

# Check coverage
pytest --cov=llf --cov-report=html

# Run linter
flake8 llf tests

# Run type checker
mypy llf
```

## How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Use the bug report template** when creating an issue
3. **Include**:
   - Clear description of the bug
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details (OS, Python version, LLF version)
   - Error messages and stack traces
   - Minimal reproducible example

### Suggesting Enhancements

1. **Check existing issues** for similar suggestions
2. **Use the feature request template**
3. **Explain**:
   - The problem you're trying to solve
   - Your proposed solution
   - Alternative solutions considered
   - Potential impact on existing features

### Contributing Code

1. **Find or create an issue** for what you want to work on
2. **Comment on the issue** to let others know you're working on it
3. **Create a feature branch** from `main`
4. **Make your changes**
5. **Write tests** for your changes
6. **Update documentation** as needed
7. **Submit a pull request**

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

```python
# Line length: 100 characters (not 79)
MAX_LINE_LENGTH = 100

# Use double quotes for strings (unless single quotes avoid escaping)
name = "example"
message = 'He said "hello"'

# Use type hints
def process_data(input_data: dict) -> dict:
    """Process input data and return result."""
    return {"result": input_data}

# Use descriptive variable names
# Good
user_authentication_token = "abc123"

# Bad
uat = "abc123"
```

### Code Organization

```python
"""
Module docstring describing purpose.

Longer description if needed.
"""

# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import pytest
import requests

# Local imports
from llf.core import LLMClient
from llf.tools_manager import ToolsManager


# Constants
DEFAULT_TIMEOUT = 60
MAX_RETRIES = 3


# Classes
class MyClass:
    """Class docstring."""

    def __init__(self, param: str):
        """Initialize with param."""
        self.param = param

    def method(self) -> str:
        """Method docstring."""
        return self.param


# Functions
def my_function(arg: int) -> int:
    """Function docstring."""
    return arg * 2


# Main execution
if __name__ == "__main__":
    main()
```

### Docstring Format

Use Google-style docstrings:

```python
def complex_function(param1: str, param2: int, param3: bool = False) -> dict:
    """
    Brief description of function.

    Longer description with more details about what the function does,
    how it works, and any important considerations.

    Args:
        param1: Description of param1
        param2: Description of param2
        param3: Description of param3. Defaults to False.

    Returns:
        Dictionary containing:
            - 'result': The result value
            - 'status': Status code
            - 'message': Status message

    Raises:
        ValueError: If param2 is negative
        TypeError: If param1 is not a string

    Example:
        >>> result = complex_function("test", 42, True)
        >>> print(result['status'])
        200
    """
    if param2 < 0:
        raise ValueError("param2 must be non-negative")

    return {
        'result': f"{param1}_{param2}",
        'status': 200,
        'message': "Success"
    }
```

### Error Handling

```python
# Use specific exceptions
try:
    result = risky_operation()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    return {'success': False, 'error': str(e)}
except PermissionError as e:
    logger.error(f"Permission denied: {e}")
    return {'success': False, 'error': str(e)}

# Always return structured error responses
def execute(params: dict) -> dict:
    """Execute operation."""
    try:
        # ... operation logic ...
        return {'success': True, 'data': result}
    except Exception as e:
        logger.exception("Unexpected error")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }
```

## Testing Requirements

### Test Coverage

- **Minimum coverage**: 80% for new code
- **Target coverage**: 90%+
- **Critical paths**: 100% coverage required

### Writing Tests

```python
"""
Test module docstring.
"""

import pytest
from llf.module import function_to_test


class TestFeatureName:
    """Test suite for feature."""

    def test_normal_case(self):
        """Test normal operation."""
        result = function_to_test("input")
        assert result == "expected"

    def test_edge_case(self):
        """Test edge case."""
        result = function_to_test("")
        assert result is None

    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            function_to_test(None)

    @pytest.mark.parametrize("input,expected", [
        ("test1", "result1"),
        ("test2", "result2"),
        ("test3", "result3"),
    ])
    def test_multiple_inputs(self, input, expected):
        """Test multiple input cases."""
        assert function_to_test(input) == expected
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=llf --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_specific.py

# Run specific test
pytest tests/test_specific.py::TestClass::test_method

# Run tests matching pattern
pytest -k "test_pattern"

# Run with verbose output
pytest -v

# Run and stop at first failure
pytest -x
```

### Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_core.py             # Core functionality tests
├── test_datastore.py        # Datastore tests
├── test_memory.py           # Memory tests
├── test_modules.py          # Module tests
├── test_tools_manager.py    # Tools manager tests
├── test_file_access.py      # File access tool tests
├── test_command_exec.py     # Command exec tool tests
└── integration/             # Integration tests
    ├── __init__.py
    └── test_full_flow.py
```

## Documentation

### Updating Documentation

Documentation must be updated for:

- New features
- Changed behavior
- New configuration options
- New tools
- Breaking changes

### Documentation Types

1. **Code Comments**: Explain "why", not "what"
   ```python
   # Good: Explains reasoning
   # Use binary mode to preserve file encoding
   with open(path, 'rb') as f:
       content = f.read()

   # Bad: Restates code
   # Open file
   with open(path, 'rb') as f:
       content = f.read()
   ```

2. **Docstrings**: Required for all public functions/classes

3. **README Updates**: Update main README.md for user-facing changes

4. **Tool Documentation**: Update tools/README.md for tool changes

5. **Changelog**: Add entry to CHANGELOG.md

## Pull Request Process

### 1. Create Feature Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

```bash
# Make your changes
# ... edit files ...

# Run tests frequently
pytest

# Check coverage
pytest --cov=llf --cov-report=term

# Run linter
flake8 llf tests

# Run type checker
mypy llf
```

### 3. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new feature X

- Implement feature X functionality
- Add tests for feature X
- Update documentation

Fixes #123"
```

**Commit Message Format**:
```
<type>: <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding/updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

### 4. Push Changes

```bash
# Push to your fork
git push origin feature/your-feature-name
```

### 5. Create Pull Request

1. Go to GitHub and create a pull request
2. Fill out the pull request template
3. Link related issues
4. Request review from maintainers

### 6. Address Review Comments

```bash
# Make requested changes
# ... edit files ...

# Commit changes
git add .
git commit -m "address review comments"

# Push updates
git push origin feature/your-feature-name
```

### 7. Merge

Once approved:
- Maintainer will merge your PR
- Delete your feature branch
- Update your local main branch

## Tool Development Guidelines

### Creating a New Tool

See [tools/README.md](README.md#creating-new-tools) for complete guide.

**Quick checklist**:

- [ ] Create tool directory in `tools/`
- [ ] Create `config.json` with all required fields
- [ ] Implement `execute()` function
- [ ] Add OpenAI-compatible tool definition
- [ ] Implement security checks (whitelist, dangerous paths/commands)
- [ ] Write comprehensive tests (80%+ coverage)
- [ ] Document tool in README.md
- [ ] Add example usage
- [ ] Test import/export functionality

### Tool Security Requirements

All tools must implement:

1. **Input validation**
   ```python
   if 'required_param' not in params:
       return {'success': False, 'error': 'Missing required_param'}
   ```

2. **Whitelist checking** (if applicable)
   ```python
   if not manager.check_whitelist('tool_name', path):
       return {'success': False, 'error': 'Path not whitelisted'}
   ```

3. **Dangerous operation detection**
   ```python
   if is_dangerous_operation(params):
       if not tool_info['metadata'].get('requires_approval'):
           return {'success': False, 'error': 'Requires approval'}
   ```

4. **Error handling**
   ```python
   try:
       result = operation()
       return {'success': True, 'data': result}
   except Exception as e:
       return {'success': False, 'error': str(e)}
   ```

### Tool Testing Requirements

Minimum test coverage for tools:

- [ ] Normal operation tests
- [ ] Error case tests
- [ ] Edge case tests
- [ ] Security feature tests (whitelist, dangerous paths, etc.)
- [ ] Integration tests
- [ ] Config validation tests

Example:
```python
class TestMyTool:
    """Comprehensive tests for my_tool."""

    def test_normal_operation(self):
        """Test normal tool execution."""
        # ... test code ...

    def test_missing_parameter(self):
        """Test error when parameter missing."""
        # ... test code ...

    def test_whitelist_enforcement(self):
        """Test whitelist checking."""
        # ... test code ...

    def test_dangerous_operation_detection(self):
        """Test dangerous operation requires approval."""
        # ... test code ...
```

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

Example: `1.2.3` = Major 1, Minor 2, Patch 3

### Release Checklist

- [ ] All tests passing
- [ ] Coverage meets requirements (80%+)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version number bumped
- [ ] Git tag created
- [ ] Release notes written
- [ ] Package published to PyPI

### Creating a Release

```bash
# Update version in setup.py
vim setup.py

# Update CHANGELOG.md
vim CHANGELOG.md

# Commit version bump
git add setup.py CHANGELOG.md
git commit -m "chore: bump version to 1.2.3"

# Create tag
git tag -a v1.2.3 -m "Release version 1.2.3"

# Push tag
git push origin v1.2.3
```

## Development Workflow

### Typical Development Cycle

```bash
# 1. Start with updated main
git checkout main
git pull upstream main

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes iteratively
while not done:
    # Edit files
    vim llf/module.py

    # Run tests
    pytest tests/test_module.py

    # Check coverage
    pytest --cov=llf.module --cov-report=term

    # Commit progress
    git add llf/module.py tests/test_module.py
    git commit -m "work in progress: implement X"

# 4. Final checks before PR
pytest --cov=llf --cov-report=html
flake8 llf tests
mypy llf

# 5. Update documentation
vim docs/README.md
git add docs/README.md
git commit -m "docs: update README for feature X"

# 6. Push and create PR
git push origin feature/my-feature
# Create PR on GitHub
```

### Working with Multiple Issues

```bash
# Work on multiple features in parallel
git checkout -b feature/feature-1
# ... work on feature 1 ...

git checkout main
git checkout -b feature/feature-2
# ... work on feature 2 ...

# Switch between branches
git checkout feature/feature-1
# ... continue feature 1 ...

git checkout feature/feature-2
# ... continue feature 2 ...
```

## Getting Help

### Resources

- **Documentation**: [README.md](../README.md), [tools/README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/local_llm_framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/local_llm_framework/discussions)

### Questions

If you have questions:

1. Check existing documentation
2. Search existing issues
3. Ask in GitHub Discussions
4. Create a new issue with the "question" label

### Stuck?

If you're stuck:

1. Review this contributing guide
2. Look at similar merged PRs for examples
3. Ask for help in your PR or issue
4. Reach out to maintainers

## Recognition

Contributors are recognized:

- In release notes
- In the contributors list
- In commit history
- Through GitHub contributor stats

## License

By contributing to Local LLM Framework, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing to Local LLM Framework!**

We appreciate your time and effort in making this project better for everyone.

---

**Last Updated**: 2025-01-06
**Version**: 1.0
