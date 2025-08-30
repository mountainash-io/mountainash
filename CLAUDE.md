# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mountainash-expressions** is a Python package that provides a sophisticated dual-logic expression system for building cross-backend DataFrame operations. The package supports both Boolean (TRUE/FALSE) and Ternary (TRUE/FALSE/UNKNOWN) logic systems with automatic backend detection across pandas, polars, Ibis, PyArrow, and other DataFrame libraries.

The package is designed as a foundation for cross-backend DataFrame filtering, mutations, and other operations that need consistent expression evaluation regardless of the underlying DataFrame implementation.

## Recent Architecture Refactoring

**IMPORTANT**: The package underwent a major architectural refactoring that consolidated the modular file structure into a more cohesive organization:
- Core logic and visitor implementations are now in `core/` module
- Backend-specific implementations moved to `backends/` module  
- Old paths in `logic/`, `visitors/`, and `helpers/` directories are being phased out
- Some imports may still reference old paths and need updating

## Core Architecture

### New Package Structure (After Refactoring)

```
src/mountainash_expressions/
├── __init__.py                       # Main exports (needs import path updates)
├── __version__.py                    # Package version
├── core/                            # Core consolidated modules
│   ├── constants.py                 # Shared constants and enums
│   ├── logic/                       # Logic implementations
│   │   ├── __init__.py             # Core logic exports
│   │   ├── expression_nodes.py     # Base node classes
│   │   ├── expression_builder.py   # Base builder
│   │   ├── expression_converter.py # Base converter
│   │   ├── conversion_matrix.py    # Cross-logic conversion
│   │   ├── boolean/                # Boolean logic
│   │   │   ├── boolean_nodes.py
│   │   │   ├── boolean_builder.py
│   │   │   └── boolean_converter.py
│   │   └── ternary/                # Ternary logic
│   │       ├── ternary_nodes.py
│   │       ├── ternary_builder.py
│   │       ├── ternary_converter.py
│   │       └── ternary_value_mappings.py
│   └── visitor/                     # Visitor patterns
│       ├── __init__.py
│       ├── expression_visitor.py   # Base visitor
│       ├── visitor_factory.py      # Factory for visitor creation
│       ├── logic/                   # Logic-specific visitors
│       │   ├── boolean_visitor.py
│       │   └── ternary_visitor.py
│       └── backends/                # Backend mixins
│           └── backend_visitor_mixin.py
├── backends/                        # Backend implementations
│   ├── __init__.py
│   ├── ibis/
│   │   ├── ibis_visitor.py
│   │   ├── boolean_visitor_ibis.py
│   │   └── ternary_visitor_ibis.py
│   ├── pandas/
│   │   ├── pandas_visitor.py
│   │   ├── boolean_visitor_pandas.py
│   │   └── ternary_visitor_pandas.py
│   ├── polars/
│   │   ├── polars_visitor.py
│   │   ├── boolean_visitor_polars.py
│   │   └── ternary_visitor_polars.py
│   └── pyarrow/
│       ├── pyarrow_visitor.py
│       ├── boolean_visitor_pyarrow.py
│       └── ternary_visitor_pyarrow.py
├── logic/                          # Legacy paths (being phased out)
│   ├── core/                       # Empty/remnants
│   └── ternary/
│       └── ternary_nodes.py       # Still has some code
└── visitors/                       # Legacy paths (empty)
    ├── boolean/
    ├── ternary/
    └── core/
        └── backends/
```

### Import Path Updates Needed

The main `__init__.py` file still references old import paths that need to be updated:
- `from .logic.boolean` → `from .core.logic.boolean`
- `from .logic.ternary` → `from .core.logic.ternary`  
- `from .helpers` → `from .core.visitor`
- Backend visitor imports need updating to `backends/` module

## Development Commands

### Essential Daily Commands
- **Tests**: `hatch run test:test` (full test suite with coverage) or `hatch run test:test-quick` (fast iteration)
- **Single test**: `hatch run test:test-target tests/path/to/test_file.py::TestClass::test_function`
- **Lint**: `hatch run ruff:check` or `hatch run ruff:fix` to auto-fix
- **Type check**: `hatch run mypy:check`
- **Build**: `hatch build`

### Test Categories
- `hatch run test:test-unit` - Unit tests only
- `hatch run test:test-integration` - Integration tests only
- `hatch run test:test-performance` - Performance benchmarks
- `hatch run test:test-changed` - Only changed files (useful after refactoring)
- `hatch run test:test-changed-quick` - Changed files without coverage

### Targeted Testing (For Debugging)
- `hatch run test:test-target <path>` - Test specific files with coverage
- `hatch run test:test-target-quick <path>` - Test specific files without coverage (fastest)
- `hatch run test:test-perf` - Run performance benchmarks only

## Core Concepts

### Dual Logic Systems
- **Boolean Logic**: Traditional binary logic (TRUE/FALSE) in `core/logic/boolean/`
- **Ternary Logic**: Three-valued logic (TRUE/FALSE/UNKNOWN) in `core/logic/ternary/`

### Expression Node Hierarchy
All expressions inherit from `ExpressionNode` (in `core/logic/expression_nodes.py`):
- `eval()`: Core evaluation returning backend-specific expressions
- `eval_is_true()`: Boolean TRUE check (works for both Boolean and Ternary)
- `eval_is_false()`: Boolean FALSE check (works for both Boolean and Ternary)
- For Ternary: `eval_is_unknown()`, `eval_maybe_true()`, `eval_maybe_false()`, `eval_is_known()`

### Ternary Logic System
Mathematical optimization using integer values:
- **-1 = FALSE**
- **1 = TRUE**
- **0 = UNKNOWN**

UNKNOWN value mappings (configurable):
- String: `"<NA>"` (default)
- Numeric: `-999999999` (default)
- None/null values automatically handled

### Visitor Pattern Implementation
The visitor factory (`core/visitor/visitor_factory.py`) automatically selects the appropriate visitor based on DataFrame type:

```python
# Automatic visitor selection (recommended)
result = expression.eval_is_true()(dataframe)

# Manual visitor creation (if needed)
from mountainash_expressions.core.visitor import ExpressionVisitorFactory
visitor = ExpressionVisitorFactory.create_boolean_visitor_for_backend(df)
```

### Backend Detection
The factory identifies backends through `_identify_backend()` method:
- Ibis tables → `CONST_VISITOR_BACKENDS.IBIS`
- Pandas DataFrames → `CONST_VISITOR_BACKENDS.PANDAS`
- Polars DataFrames/LazyFrames → `CONST_VISITOR_BACKENDS.POLARS`
- PyArrow Tables/RecordBatches → `CONST_VISITOR_BACKENDS.PYARROW`

## Usage Patterns

### Import Paths (Current - May Need Updates)

```python
# Boolean expressions (current imports - may need path updates)
from mountainash_expressions.logic.boolean import (
    BooleanColumnExpressionNode, BooleanLogicalExpressionNode, BooleanExpressionBuilder
)

# Ternary expressions (current imports - may need path updates)
from mountainash_expressions.logic.ternary import (
    TernaryColumnExpressionNode, TernaryLogicalExpressionNode, TernaryExpressionBuilder
)

# Visitor factory (current import - may need path update)
from mountainash_expressions.helpers import ExpressionVisitorFactory
```

### Correct Import Paths (After Full Migration)

```python
# Boolean expressions
from mountainash_expressions.core.logic.boolean import (
    BooleanColumnExpressionNode, BooleanLogicalExpressionNode, BooleanExpressionBuilder
)

# Ternary expressions  
from mountainash_expressions.core.logic.ternary import (
    TernaryColumnExpressionNode, TernaryLogicalExpressionNode, TernaryExpressionBuilder
)

# Visitor factory
from mountainash_expressions.core.visitor import ExpressionVisitorFactory
```

## Dependencies

### Core Dependencies
- **ibis-framework[pandas,sqlite,duckdb]** == 10.4.0 - DataFrame framework support
- **numpy** >=1.23.2,<3 - Numerical computing
- **pandas** >=2.2.0 - DataFrame operations
- **polars** ==1.16.0 - Fast DataFrame library
- **pyarrow** ==17.0.0 - Columnar operations
- **narwhals** - Cross-DataFrame compatibility layer

### Mountain Ash Ecosystem
- **mountainash-constants** - Shared constants and enums (local dev path: `../mountainash-constants`)
- **mountainash-settings** - Configuration management (local dev path: `../mountainash-settings`)
- **mountainash-utils-files** - File utilities (local dev path: `../mountainash-utils-files`)
- **mountainash-utils-os** - OS utilities (local dev path: `../mountainash-utils-os`)

## Design Patterns

### Visitor Pattern
Backend-specific expression generation with automatic visitor selection through `ExpressionVisitorFactory` in `core/visitor/visitor_factory.py`.

### Builder Pattern
Fluent interface for complex expression construction with helper methods for common operations in `core/logic/*/builder.py` files.

### Protocol Pattern
Type-safe interfaces using Python protocols in `core/logic/expression_node_protocol.py` and `core/visitor/expression_visitor_protocol.py`.

### Conversion Matrix
Cross-logic type conversion matrix in `core/logic/conversion_matrix.py` enables seamless Boolean ↔ Ternary transformations.

## Architecture Principles

### Consolidation Over Fragmentation
The refactoring moved from many small files to fewer, more cohesive modules that group related functionality.

### Protocol-Based Design
Using Python protocols for type safety and clear interfaces between components.

### Backend Isolation
Each backend has its own module in `backends/` with complete visitor implementations, allowing backend-specific optimizations.

### Logic Type Orthogonality
Any expression can work with any visitor through automatic conversion, enabling seamless cross-logic operations.

## Common Development Tasks

### After Refactoring Checklist
1. Run all tests to ensure nothing broke: `hatch run test:test`
2. Check for import errors: `hatch run test:test-quick`
3. Update imports in any code using old paths
4. Run linter to catch issues: `hatch run ruff:check`
5. Type check for consistency: `hatch run mypy:check`

### Adding a New Backend
1. Create new directory in `backends/<backend_name>/`
2. Implement visitor classes inheriting from base visitors in `core/visitor/logic/`
3. Register in `ExpressionVisitorFactory._visitors_registry`
4. Add backend detection in `ExpressionVisitorFactory._identify_backend()`

### Testing Specific Logic Types
- Boolean tests: `hatch run test:test-target tests/boolean/`
- Ternary tests: `hatch run test:test-target tests/ternary/`
- Gold standard API: `hatch run test:test-target tests/ternary/test_gold_standard_api.py`

## Important Notes

### Ongoing Migration
The codebase is in transition from the old modular structure to the new consolidated architecture. Some imports and references may still point to old paths.

### Import Resolution Priority
When fixing imports, prioritize the `core/` module paths over legacy `logic/`, `visitors/`, and `helpers/` paths.

### Test Coverage
After the refactoring, ensure comprehensive test coverage by running: `hatch run test:test` and checking the coverage report.

### Type Safety
The new architecture emphasizes protocols and type annotations. Always run `hatch run mypy:check` after making changes.