# Testing Mountain Ash Expressions

This document outlines the testing procedures for the Mountain Ash Expressions project, including how to run tests locally and via GitHub Actions.

## Table of Contents

1. [Local Testing](#local-testing)
2. [Test Commands Reference](#test-commands-reference)
3. [Expression System Testing](#expression-system-testing)
4. [Coverage Reports](#coverage-reports)
5. [GitHub Actions Testing](#github-actions-testing)
6. [Testing Dependencies](#testing-dependencies)

## Local Testing

We use [Hatch](https://hatch.pypa.io/) to manage our development environment and run tests. To run tests locally:

1. Ensure you have Hatch installed:
   ```bash
   pip install hatch
   ```

2. Run the comprehensive test suite (recommended for daily use):
   ```bash
   hatch run test:test
   ```
   This command runs tests with coverage and generates all coverage reports (JSON, XML, HTML) plus a terminal summary.

## Test Commands Reference

### Core Testing Commands (Use these daily)

- **Full test suite with coverage:**
  ```bash
  hatch run test:test
  ```
  Runs pytest with coverage, generates JSON/XML/HTML reports, and shows missing coverage.

- **GitHub Actions test with coverage:**
  ```bash
  hatch run test_github:test-cov
  ```
  Runs tests with coverage and generates XML output for CI.

- **Quick testing (no coverage overhead):**
  ```bash
  hatch run test:test-quick
  ```
  Fast iteration testing without coverage collection.

### Targeted Testing (For debugging specific issues)

- **Test specific files/tests with coverage:**
  ```bash
  hatch run test:test-target tests/ternary/test_gold_standard_api.py::test_ternary_builder_complete_api
  ```

- **Test specific files/tests without coverage (fastest):**
  ```bash
  hatch run test:test-target-quick tests/boolean/test_boolean_nodes.py
  ```

- **Test only changed files with coverage:**
  ```bash
  hatch run test:test-changed
  ```

- **Test only changed files without coverage:**
  ```bash
  hatch run test:test-changed-quick
  ```

### Specialized Testing

- **Performance benchmarks only:**
  ```bash
  hatch run test:test-perf
  ```

- **Test by markers:**
  ```bash
  hatch run test:test-unit        # Unit tests only
  hatch run test:test-integration # Integration tests only
  hatch run test:test-performance # Performance tests only
  ```

### CI/Reporting Commands

- **Full CI suite with structured reports:**
  ```bash
  hatch run test:test-ci
  ```
  Generates JSON test reports, JUnit XML, and all coverage formats.

## Expression System Testing

The expression system has specialized testing approaches to ensure correctness across different logic types and backends.

### Gold Standard API Testing

The most comprehensive test is our Gold Standard API test suite:

```bash
# Run the complete API validation
hatch run test:test-target tests/ternary/test_gold_standard_api.py

# Run specific gold standard test methods
hatch run test:test-target tests/ternary/test_gold_standard_api.py::test_ternary_builder_complete_api
```

This test validates:
- Complete TernaryExpressionBuilder API across all backends
- All evaluation methods (`eval_is_true`, `eval_is_false`, `eval_is_unknown`, etc.)
- Cross-backend compatibility (Polars, Ibis, Pandas, PyArrow)
- Mathematical correctness of ternary logic operations

### Logic Type Testing

#### Boolean Logic Tests
```bash
# Test Boolean expression functionality
hatch run test:test-target tests/boolean/

# Specific Boolean components
hatch run test:test-target tests/boolean/test_boolean_nodes.py
hatch run test:test-target tests/boolean/test_boolean_builder.py
```

#### Ternary Logic Tests
```bash
# Test Ternary expression functionality
hatch run test:test-target tests/ternary/

# Specific Ternary components
hatch run test:test-target tests/ternary/test_ternary_nodes.py
hatch run test:test-target tests/ternary/test_ternary_builder.py
hatch run test:test-target tests/ternary/test_ternary_logic_operations.py
```

### Backend-Specific Testing

Test expression compatibility across different DataFrame backends:

```bash
# Test Polars backend integration
hatch run test:test-target tests/visitors/test_polars_visitors.py

# Test Ibis backend integration  
hatch run test:test-target tests/visitors/test_ibis_visitors.py

# Test Pandas backend integration
hatch run test:test-target tests/visitors/test_pandas_visitors.py

# Test PyArrow backend integration
hatch run test:test-target tests/visitors/test_pyarrow_visitors.py
```

### Mathematical Correctness Testing

Verify the mathematical foundation of the ternary logic system:

```bash
# Test ternary arithmetic and truth tables
hatch run test:test-target tests/ternary/test_ternary_mathematics.py

# Test UNKNOWN value handling
hatch run test:test-target tests/ternary/test_unknown_value_mapping.py

# Test logical operation correctness
hatch run test:test-target tests/ternary/test_logical_operations.py
```

## Coverage Reports

When you run tests with coverage, several output formats are generated:

### Local Coverage Files Generated

After running `hatch run test:test` or any coverage-enabled command, you'll find:

- **`coverage.json`** - Machine-readable coverage data in JSON format
- **`coverage.xml`** - Coverage data in XML format (for CI tools)
- **`htmlcov/`** - Complete HTML coverage report directory
  - Open `htmlcov/index.html` in your browser for interactive coverage exploration
- **`junit.xml`** - JUnit test results format
- **`pytest_report.json`** - Structured pytest results (when using `test-ci`)

### Inspecting Coverage Results

1. **Terminal Summary:** Coverage percentage and missing lines displayed after test completion

2. **HTML Report:** Open `htmlcov/index.html` in your browser for:
   - File-by-file coverage breakdown
   - Line-by-line highlighting of covered/uncovered code
   - Interactive navigation through your codebase

3. **JSON Analysis:** Use `coverage.json` for programmatic analysis:
   ```bash
   python -c "import json; print(json.load(open('coverage.json'))['totals']['percent_covered'])"
   ```

4. **Missing Coverage:** The terminal report shows specific line numbers that lack coverage

### Coverage Targets

We aim for high coverage across all expression system components:

- **Core Logic**: >95% coverage for expression nodes and builders
- **Visitor Implementations**: >90% coverage for all backend visitors
- **Mathematical Operations**: 100% coverage for ternary logic operations
- **API Methods**: 100% coverage for all public eval methods

## GitHub Actions Testing

Our GitHub Actions workflow automatically runs tests on pull requests and pushes to specific branches. The workflow is defined in `.github/workflows/python-run-pytest.yml`.

Key points:
- Tests are run on Ubuntu 24.04 with Python 3.12
- The workflow is triggered on pull requests that modify `src/mountainash/**` files
- Uses the `test_github` environment defined in `hatch.toml`
- Automatically uploads coverage to Codecov

To manually trigger the tests in GitHub Actions:
1. Go to the "Actions" tab in the GitHub repository
2. Select the "Pytest Runner" workflow
3. Click "Run workflow" and select the branch you want to test
4. Choose the fallback branch for dependencies:
   - `develop` (default)
   - `main`
5. Click "Run workflow" to execute

## Testing Dependencies

One of the key features of our testing setup is the ability to test changes across multiple Mountain Ash repositories simultaneously. This is particularly useful when making changes that affect multiple packages.

To test dependency changes:
1. Create branches with identical names across all relevant Mountain Ash repositories.
2. Push your changes to these branches.
3. When you create a pull request or push to the branch in this repository, the GitHub Actions workflow will automatically use the matching branches from the dependency repositories.
4. If a matching branch doesn't exist for a dependency, the workflow falls back to using the branch specified in the workflow dispatch (either main or develop).

This allows you to test integrated changes across multiple packages before merging, with the flexibility to choose which version of dependencies to fall back on.

## Online Coverage Tracking

We use [Codecov](https://codecov.io/) to track code coverage across commits and pull requests. Coverage reports are automatically uploaded after successful test runs in GitHub Actions.

To view online coverage reports:
1. Go to the [Codecov dashboard](https://codecov.io/github/mountainash-io/mountainash) for this repository
2. Navigate through files to see detailed coverage information
3. View coverage trends over time and across branches
4. Review coverage changes in pull requests

We strive to maintain high code coverage. Please ensure that your contributions include appropriate test coverage.

## Test Organization

### Test Directory Structure

```
tests/
├── boolean/                    # Boolean logic tests
│   ├── test_boolean_nodes.py
│   ├── test_boolean_builder.py
│   └── test_boolean_visitors.py
├── ternary/                    # Ternary logic tests
│   ├── test_ternary_nodes.py
│   ├── test_ternary_builder.py
│   ├── test_ternary_visitors.py
│   ├── test_gold_standard_api.py  # Comprehensive API validation
│   └── test_ternary_mathematics.py
├── visitors/                   # Backend visitor tests
│   ├── test_polars_visitors.py
│   ├── test_ibis_visitors.py
│   ├── test_pandas_visitors.py
│   └── test_pyarrow_visitors.py
├── core/                      # Core functionality tests
│   ├── test_base_nodes.py
│   ├── test_visitor_factory.py
│   └── test_expression_evaluation.py
└── integration/               # Cross-system integration tests
    ├── test_cross_backend_compatibility.py
    └── test_logic_type_conversion.py
```

### Test Markers

We use pytest markers to categorize tests:

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests across components
- `@pytest.mark.performance` - Performance and benchmark tests
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.backend("polars")` - Backend-specific tests

### Writing New Tests

When adding new tests:

1. **Choose appropriate markers** based on test type
2. **Test both Boolean and Ternary logic** if applicable
3. **Include cross-backend validation** for visitor changes
4. **Test edge cases** especially for UNKNOWN value handling
5. **Add performance tests** for mathematical operations
6. **Update gold standard tests** for API changes

Example test structure:

```python
import pytest
from mountainash.logic.ternary import TernaryExpressionBuilder

class TestTernaryExpressionBuilder:
    
    @pytest.mark.unit
    def test_and_operation_basic(self):
        """Test basic AND operation correctness."""
        # Test implementation
    
    @pytest.mark.integration    
    @pytest.mark.backend("polars")
    def test_and_operation_polars_backend(self):
        """Test AND operation with Polars backend."""
        # Backend-specific test
    
    @pytest.mark.performance
    def test_and_operation_performance(self):
        """Benchmark AND operation performance."""
        # Performance test
```

## Debugging Failed Tests

### Common Issues and Solutions

1. **Import Errors**: Ensure all dependencies are installed in the test environment
2. **Backend Unavailable**: Some tests may skip if optional backends aren't available
3. **Mathematical Errors**: Check ternary logic truth tables for correctness
4. **Cross-Backend Inconsistency**: Verify visitor implementations match expected behavior

### Debug Commands

```bash
# Run tests with verbose output
hatch run test:test-target -v tests/ternary/test_gold_standard_api.py

# Run tests with detailed failure information
hatch run test:test-target --tb=long tests/

# Run tests and drop into debugger on failure
hatch run test:test-target --pdb tests/ternary/

# Show print statements during test execution
hatch run test:test-target -s tests/
```

## Performance Testing

We include performance benchmarks for critical operations:

```bash
# Run all performance tests
hatch run test:test-performance

# Run specific benchmark
hatch run test:test-perf tests/ternary/test_ternary_performance.py

# Generate performance reports
hatch run test:test-perf --benchmark-json=performance_results.json
```

Performance tests validate:
- Expression construction speed
- Backend visitor selection overhead
- Mathematical operation efficiency
- Cross-backend performance consistency

## Continuous Integration

Our CI pipeline ensures:
- All tests pass across supported Python versions
- Code coverage meets minimum thresholds
- Performance regressions are detected
- Cross-backend compatibility is maintained
- Documentation examples work correctly

The pipeline runs on:
- Pull request creation/updates
- Pushes to main/develop branches
- Scheduled nightly runs for stability verification