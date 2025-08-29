# Contributing to Mountain Ash Expressions

This document outlines the process for contributing to the project and provides guidelines to ensure a smooth collaboration.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Branching Strategy](#branching-strategy)
3. [Making Changes](#making-changes)
4. [Submitting a Pull Request](#submitting-a-pull-request)
5. [Code Review Process](#code-review-process)
6. [Coding Standards](#coding-standards)
7. [Testing](#testing)
8. [Documentation](#documentation)

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally: `git clone https://github.com/your-username/mountainash-expressions.git`
3. Add the original repository as a remote: `git remote add upstream https://github.com/mountainash-io/mountainash-expressions.git`
4. Install development dependencies: `hatch shell`
5. Create a new branch for your contribution (see [Branching Strategy](#branching-strategy)).

## Branching Strategy

We follow a git-flow branching methodology. The following branch naming conventions are allowed:

- `main`: The main production branch
- `develop`: The main development branch
- `feature/*`: For new features
- `chore/*`: For maintenance tasks
- `release/*`: For release preparation
- `hotfix/*`: For critical bug fixes in production
- `bugfix/*`: For non-critical bug fixes
- `renovate/*`: For dependency updates (automated)

### Protected Branches

The following branches are strictly protected and require code owner review and repository owner approval for pull requests:

- `main`
- `develop`
- `release/*`

## Making Changes

1. Ensure you're working on the correct branch (e.g., `feature/new-expression-logic` for a new feature).
2. Make your changes in small, logical commits.
3. Follow the [Coding Standards](#coding-standards) of the project.
4. Add or update tests as necessary (see [Testing](#testing)).
5. Update documentation if required (see [Documentation](#documentation)).

### Expression System Guidelines

When working on the expression system:

- **Logic Type Consistency**: Ensure Boolean and Ternary logic systems maintain orthogonality
- **Backend Compatibility**: Test changes across all supported backends (Polars, Ibis, Pandas, PyArrow)
- **Visitor Pattern**: Follow the established visitor pattern for backend-specific implementations
- **Mathematical Foundation**: Maintain the ternary logic mathematical properties (-1/0/1 system)

## Submitting a Pull Request

1. Push your changes to your fork on GitHub.
2. Open a pull request against the appropriate branch:
   - For features, chores, and bugfixes, target the `develop` branch.
   - For hotfixes, target the `main` branch.
3. Provide a clear title and description for your pull request.
4. Reference any related issues in the pull request description.
5. Ensure all checks (tests, linting, etc.) pass successfully.

### Pull Request Template

Please include the following information in your pull request:

- **Type of Change**: Feature, Bug fix, Performance improvement, Documentation, etc.
- **Backend Impact**: Which DataFrame backends are affected
- **Logic Type**: Boolean, Ternary, or Both
- **Breaking Changes**: Any breaking changes to the API
- **Testing**: Description of tests added or modified

## Code Review Process

1. All pull requests require at least one review from a code owner.
2. For protected branches (`main`, `develop`, `release/*`), additional approval from a repository owner is required.
3. Expression system changes require validation across multiple backends.
4. Address any feedback or comments provided during the review process.
5. Once approved, a maintainer will merge your pull request.

## Coding Standards

- Follow PEP 8 style guide for Python code.
- Use type hints for all public functions and methods.
- Write clear, self-documenting code with meaningful variable and function names.
- Keep functions and methods focused and concise.
- Use comments sparingly, only when necessary to explain complex logic.

### Expression-Specific Standards

- **Node Classes**: Inherit from appropriate base classes (`ExpressionNode`, `ColumnExpressionNode`, etc.)
- **Visitor Classes**: Implement all required visitor methods for backend compatibility
- **Builder Classes**: Use fluent interface patterns for expression construction
- **Logic Operations**: Maintain mathematical correctness for ternary operations
- **Backend Detection**: Use `ExpressionVisitorFactory` for automatic visitor selection

### Import Organization

```python
# Standard library imports
from abc import ABC, abstractmethod
from typing import Any, List, Union, Callable

# Third-party imports
import pandas as pd
import polars as pl

# Mountain Ash imports
from mountainash_constants import BaseValueConstant
from mountainash_expressions.constants import CONST_EXPRESSION_LOGIC_OPERATORS
```

## Testing

- Write unit tests for all new functionality.
- Ensure all existing tests pass before submitting a pull request.
- Aim for high test coverage, especially for critical parts of the expression system.
- Use pytest for writing and running tests.
- Test across multiple DataFrame backends when applicable.

### Expression Testing Requirements

- **Cross-Backend Testing**: Validate expressions work with Polars, Pandas, Ibis, and PyArrow
- **Logic Validation**: Test both Boolean and Ternary logic correctness
- **Edge Cases**: Test UNKNOWN value handling and edge cases
- **Performance**: Include performance tests for mathematical operations
- **Gold Standard**: Use the gold standard API tests for comprehensive validation

### Test Commands

```bash
# Full test suite with coverage
hatch run test:test

# Quick iteration testing
hatch run test:test-quick

# Target specific expression tests
hatch run test:test-target tests/ternary/test_gold_standard_api.py

# Cross-backend validation
hatch run test:test-integration

# Performance benchmarks
hatch run test:test-performance
```

## Documentation

- Update the README.md file if your changes affect the project's setup or usage.
- Document new features or changes in behavior in the appropriate documentation files.
- Keep docstrings up-to-date for all public functions, classes, and modules.
- Use Google-style docstrings.

### Documentation Requirements

- **API Documentation**: Document all public methods with examples
- **Usage Patterns**: Provide real-world usage examples
- **Backend Compatibility**: Note backend-specific behavior if applicable
- **Logic System**: Document mathematical properties and truth tables
- **Performance Notes**: Include performance characteristics for new operations

### Example Documentation

```python
def eval_is_true(self) -> Callable:
    """
    Evaluate expression for TRUE values only.
    
    Works with both Boolean and Ternary expressions through automatic
    visitor selection and backend detection.
    
    Returns:
        Callable: Function that takes a DataFrame and returns backend-specific
                 expression filtering for TRUE values only.
    
    Examples:
        >>> expr = BooleanColumnExpressionNode("age", ">", 18)
        >>> df_filtered = df.filter(expr.eval_is_true()(df))
        
        >>> ternary_expr = TernaryColumnExpressionNode("status", "==", "active")
        >>> df_active = df.filter(ternary_expr.eval_is_true()(df))
    """
```

## Development Environment

### Setup

```bash
# Clone and setup
git clone https://github.com/mountainash-io/mountainash-expressions.git
cd mountainash-expressions
hatch shell

# Install in development mode
hatch run pip install -e .
```

### Code Quality Tools

```bash
# Linting and formatting
hatch run ruff:check        # Check code style
hatch run ruff:fix          # Auto-fix issues

# Type checking
hatch run mypy:check        # Validate type annotations

# Complexity analysis
hatch run radon:radon-cc    # Cyclomatic complexity
hatch run radon:radon-mi    # Maintainability index
```

### Pre-commit Checklist

Before submitting a pull request, ensure:

- [ ] All tests pass (`hatch run test:test`)
- [ ] Code style is correct (`hatch run ruff:check`)
- [ ] Type annotations are valid (`hatch run mypy:check`)
- [ ] Documentation is updated
- [ ] Expression logic is tested across backends
- [ ] Performance impact is considered
- [ ] CHANGELOG.md is updated (if applicable)

## Community Guidelines

- Be respectful and inclusive in all interactions.
- Provide constructive feedback during code reviews.
- Help newcomers get started with the codebase.
- Follow the established architecture patterns.
- Prioritize code clarity and maintainability.

## Getting Help

If you need help or have questions:

- Check existing [Issues](https://github.com/mountainash-io/mountainash-expressions/issues)
- Review the [documentation](README.md) and [CLAUDE.md](CLAUDE.md)
- Ask questions in pull request discussions
- Contact the maintainers directly

Thank you for contributing to Mountain Ash Expressions! 🏔️