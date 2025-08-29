# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mountainash-expressions** is a Python package that provides a sophisticated dual-logic expression system for building cross-backend DataFrame operations. The package supports both Boolean (TRUE/FALSE) and Ternary (TRUE/FALSE/UNKNOWN) logic systems with automatic backend detection across pandas, polars, Ibis, PyArrow, and other DataFrame libraries.

The package is designed as a foundation for cross-backend DataFrame filtering, mutations, and other operations that need consistent expression evaluation regardless of the underlying DataFrame implementation.

## Core Architecture

### Dual Expression System
The package provides two complete logic systems:

- **Boolean Logic** (`logic/boolean/`): Traditional binary logic (TRUE/FALSE) for standard operations
- **Ternary Logic** (`logic/ternary/`): Three-valued logic (TRUE/FALSE/UNKNOWN) for real-world data with missing values

### Cross-Backend Compatibility
Expression builders work seamlessly across different DataFrame backends through the visitor pattern:
- **Polars**: Native polars expression generation
- **Ibis**: Universal SQL-like expressions
- **Pandas**: DataFrame filtering and computed columns
- **PyArrow**: Table/RecordBatch operations

### Automatic Backend Detection
`ExpressionVisitorFactory` automatically selects the appropriate visitor based on DataFrame type, eliminating manual visitor instantiation.

## Package Structure

```
src/mountainash_expressions/
├── __init__.py                    # Main package exports
├── constants.py                   # Expression constants and enums
├── logic/                         # Core expression logic
│   ├── core/                     # Shared base classes
│   │   ├── base_nodes.py         # Abstract expression nodes
│   │   ├── base_visitor.py       # Abstract visitor interface
│   │   ├── base_builder.py       # Builder pattern base
│   │   └── base_converter.py     # Logic type conversion
│   ├── boolean/                  # Boolean logic (TRUE/FALSE)
│   │   ├── boolean_nodes.py      # Boolean expression nodes
│   │   ├── boolean_builder.py    # Boolean expression builder
│   │   └── boolean_converter.py  # Boolean→Ternary conversion
│   └── ternary/                  # Ternary logic (TRUE/FALSE/UNKNOWN)
│       ├── ternary_nodes.py      # Ternary expression nodes
│       ├── ternary_builder.py    # Ternary expression builder
│       ├── ternary_converter.py  # Ternary→Boolean conversion
│       ├── constants.py          # Ternary constants (-1=FALSE, 1=TRUE, 0=UNKNOWN)
│       └── value_mappings.py     # UNKNOWN value mapping configuration
├── visitors/                      # Backend-specific implementations
│   ├── core/                     # Shared visitor infrastructure
│   │   ├── base_backend_visitor.py  # Base backend visitor
│   │   ├── ibis_visitor.py          # Ibis implementation
│   │   ├── pandas_visitor.py        # Pandas implementation
│   │   ├── polars_visitor.py        # Polars implementation
│   │   └── pyarrow_visitor.py       # PyArrow implementation
│   ├── boolean/                  # Boolean-specific visitors
│   │   ├── boolean_visitor.py       # Base boolean visitor
│   │   └── boolean_visitor_*.py     # Backend implementations
│   └── ternary/                  # Ternary-specific visitors
│       ├── ternary_visitor.py       # Base ternary visitor
│       └── ternary_visitor_*.py     # Backend implementations
└── helpers/                      # Utilities
    ├── visitor_factory.py        # Automatic visitor selection
    └── __init__.py
```

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
- `hatch run test:test-changed` - Only changed files

### Expression Testing
- **Gold standard API**: `hatch run test:test-target tests/ternary/test_gold_standard_api.py` (comprehensive API validation)
- **All tests**: `hatch run test:test-target tests/`

## Core Concepts

### Expression Node Hierarchy
All expressions inherit from `ExpressionNode` with standardized evaluation methods:
- `eval()`: Core evaluation returning backend-specific expressions
- `eval_is_true()`: Boolean TRUE check (works for both Boolean and Ternary)
- `eval_is_false()`: Boolean FALSE check (works for both Boolean and Ternary)
- For Ternary: `eval_is_unknown()`, `eval_maybe_true()`, `eval_maybe_false()`, `eval_is_known()`

### Ternary Logic System
The ternary system handles real-world data with UNKNOWN values using mathematical optimization:
- **-1 = FALSE**
- **1 = TRUE**
- **0 = UNKNOWN**

#### Logical Operations
- **AND**: FALSE dominates over TRUE and UNKNOWN
- **OR**: TRUE dominates over FALSE and UNKNOWN
- **XOR**: "Exactly one TRUE" semantics, supports multiple operands
- **NOT**: Logical negation (FALSE↔TRUE, UNKNOWN→UNKNOWN)

#### UNKNOWN Value Mapping
Configurable mappings for real-world UNKNOWN indicators:
- String UNKNOWN: `"<NA>"` (default), customizable
- Numeric UNKNOWN: `-999999999` (default), customizable
- None/null values automatically handled

### Visitor Pattern Implementation
Backend-specific expression generation through visitor pattern:
```python
# Manual visitor (traditional approach)
visitor = PolarsTernaryExpressionVisitor()
result = condition.accept(visitor)(df)

# Automatic visitor (modern approach)
result = condition.eval_is_true()(df)  # Auto-detects backend
```

## Usage Patterns

### Boolean Expressions
```python
from mountainash_expressions.logic.boolean import (
    BooleanColumnExpressionNode, BooleanLogicalExpressionNode, BooleanExpressionBuilder
)

# Build expressions with automatic backend detection
age_condition = BooleanColumnExpressionNode("age", ">", 18)
status_condition = BooleanColumnExpressionNode("status", "==", "active")
combined = BooleanLogicalExpressionNode("AND", [age_condition, status_condition])

# Multiple evaluation contexts
true_expr = combined.eval_is_true()       # TRUE filtering
false_expr = combined.eval_is_false()     # FALSE filtering
```

### Ternary Expressions
```python
from mountainash_expressions.logic.ternary import (
    TernaryColumnExpressionNode, TernaryLogicalExpressionNode, TernaryExpressionBuilder
)

# Business rules with UNKNOWN handling
high_value_rule = TernaryLogicalExpressionNode("AND", [
    TernaryColumnExpressionNode("status", "==", "active"),      # "<NA>" → UNKNOWN
    TernaryColumnExpressionNode("score", ">", 700),             # -999999999 → UNKNOWN
    TernaryColumnExpressionNode("premium", "==", True)          # None → UNKNOWN
])

# Multiple evaluation modes
true_expr = high_value_rule.eval_is_true()        # TRUE values only
unknown_expr = high_value_rule.eval_is_unknown()  # UNKNOWN values only
maybe_true_expr = high_value_rule.eval_maybe_true()  # TRUE or UNKNOWN
```

### Builder Pattern Usage
```python
# Boolean builder
bool_expr = BooleanExpressionBuilder.and_(
    BooleanExpressionBuilder.eq("age", 25),
    BooleanExpressionBuilder.ne("status", "inactive")
)

# Ternary builder with XOR (mutual exclusion)
payment_validation = TernaryExpressionBuilder.xor(
    TernaryExpressionBuilder.eq("credit_card", "active"),
    TernaryExpressionBuilder.eq("bank_transfer", "active"),
    TernaryExpressionBuilder.eq("digital_wallet", "active")
)
```

## Dependencies

### Core Dependencies
- **ibis-framework[pandas,sqlite,duckdb]** == 10.4.0 - DataFrame framework support
- **numpy** >=1.23.2,<3 - Numerical computing
- **pandas** >=2.2.0 - DataFrame operations
- **polars** ==1.16.0 - Fast DataFrame library
- **pyarrow** ==17.0.0 - Columnar operations
- **narwhals** - Cross-DataFrame compatibility layer

### Optional Dependencies (extras)
- **xarray**: N-dimensional array support
- **pyspark**: Apache Spark distributed processing
- **Database backends**: mssql, snowflake, postgres, bigquery, trino

### Mountain Ash Ecosystem
- **mountainash-constants** - Shared constants and enums
- **mountainash-settings** - Configuration management (dev/test environments)

## Code Style Guidelines
- Formatting: Uses ruff for formatting and linting
- Imports: Standard lib first, third-party next, project imports last
- Types: Use typing annotations for all functions
- Naming: CamelCase for classes, snake_case for functions/variables, UPPER_CASE for constants
- Documentation: Use Google-style docstrings
- Testing: Unit tests with pytest markers (unit, integration, performance)

## Design Patterns

### Visitor Pattern
Backend-specific expression generation with automatic visitor selection through `ExpressionVisitorFactory`.

### Builder Pattern
Fluent interface for complex expression construction with helper methods for common operations.

### Strategy Pattern
Different evaluation strategies (TRUE/FALSE/UNKNOWN) through unified eval methods.

### Conversion Pattern
Bidirectional logic type conversion (Boolean ↔ Ternary) with just-in-time transformation.

## Real-World Use Cases

### Customer Segmentation
```python
# E-commerce segmentation with UNKNOWN handling
high_value_customer = TernaryLogicalExpressionNode("AND", [
    TernaryColumnExpressionNode("status", "==", "active"),      # Handles "<NA>"
    TernaryColumnExpressionNode("income", ">", 80000),          # Handles -999999999
    TernaryColumnExpressionNode("premium", "==", True)          # Handles None
])
```

### Payment Validation (XOR Logic)
```python
# Exactly one payment method should be active
single_payment = TernaryExpressionBuilder.xor(
    TernaryExpressionBuilder.eq("credit_card", "active"),
    TernaryExpressionBuilder.eq("bank_transfer", "active"),
    TernaryExpressionBuilder.eq("wallet", "active")
)
```

### Data Quality Rules
```python
# Range operations with strict boundaries
age_eligible = TernaryExpressionBuilder.between("age", 18, 65)  # UNKNOWN if boundary unknown
```

## Architecture Principles

### Logic Type Orthogonality
Any expression can work with any visitor through automatic conversion, enabling seamless cross-logic operations.

### Backend Agnostic Design
Expressions work identically across all supported DataFrame backends without user intervention.

### Mathematical Foundation
Ternary logic uses integer arithmetic (-1/0/1) for efficient bulk operations and clear semantics.

### Extensible Framework
New backends can be added by implementing visitor interfaces without changing core expression logic.