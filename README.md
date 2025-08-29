# Mountain Ash Expressions

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
[![codecov](https://codecov.io/gh/mountainash-io/mountainash-expressions/branch/main/graph/badge.svg)](https://codecov.io/gh/mountainash-io/mountainash-expressions)

A sophisticated dual-logic expression system for building cross-backend DataFrame operations with Boolean (TRUE/FALSE) and Ternary (TRUE/FALSE/UNKNOWN) logic support.

## 🚀 Features

- **Dual Logic Systems**: Complete Boolean and Ternary logic implementations
- **Cross-Backend Compatibility**: Works seamlessly with pandas, polars, Ibis, PyArrow, and more
- **Automatic Backend Detection**: No manual visitor selection required
- **Real-World Data Handling**: Built-in support for missing/UNKNOWN values
- **Mathematical Foundation**: Efficient ternary arithmetic using integer optimization
- **Visitor Pattern**: Clean separation of expression logic from backend implementation
- **Type-Safe**: Full typing support with comprehensive type annotations

## 📦 Installation

```bash
pip install mountainash-expressions
```

### Optional Dependencies

```bash
# For extended DataFrame support
pip install mountainash-expressions[xarray]

# For distributed processing
pip install mountainash-expressions[pyspark]

# For database backends
pip install mountainash-expressions[databases]

# Install everything
pip install mountainash-expressions[all]
```

## 🔧 Quick Start

### Boolean Expressions

```python
from mountainash_expressions.logic.boolean import (
    BooleanColumnExpressionNode, BooleanLogicalExpressionNode
)

# Create expressions with automatic backend detection
age_condition = BooleanColumnExpressionNode("age", ">", 18)
status_condition = BooleanColumnExpressionNode("status", "==", "active")
combined = BooleanLogicalExpressionNode("AND", [age_condition, status_condition])

# Use with any DataFrame backend
import polars as pl
df = pl.DataFrame({"age": [25, 17, 30], "status": ["active", "inactive", "active"]})

# Automatic backend detection and expression generation
filtered = df.filter(combined.eval_is_true()(df))
```

### Ternary Expressions (Real-World Data)

```python
from mountainash_expressions.logic.ternary import (
    TernaryColumnExpressionNode, TernaryLogicalExpressionNode, TernaryExpressionBuilder
)

# Handle missing data with three-valued logic
customer_rule = TernaryLogicalExpressionNode("AND", [
    TernaryColumnExpressionNode("status", "==", "premium"),     # "<NA>" → UNKNOWN
    TernaryColumnExpressionNode("score", ">", 700),             # -999999999 → UNKNOWN
    TernaryColumnExpressionNode("verified", "==", True)         # None → UNKNOWN
])

# Multiple evaluation modes
df_qualified = df.filter(customer_rule.eval_is_true()(df))      # Only TRUE cases
df_uncertain = df.filter(customer_rule.eval_is_unknown()(df))   # UNKNOWN cases
df_potential = df.filter(customer_rule.eval_maybe_true()(df))   # TRUE or UNKNOWN
```

### Builder Pattern

```python
# Boolean builder for standard operations
bool_expr = BooleanExpressionBuilder.and_(
    BooleanExpressionBuilder.eq("department", "engineering"),
    BooleanExpressionBuilder.gt("salary", 75000)
)

# Ternary builder with XOR (mutual exclusion)
payment_validation = TernaryExpressionBuilder.xor(
    TernaryExpressionBuilder.eq("credit_card", "active"),
    TernaryExpressionBuilder.eq("bank_transfer", "active"),
    TernaryExpressionBuilder.eq("digital_wallet", "active")
)
```

## 🧮 Ternary Logic System

The ternary system uses mathematical optimization for efficient operations:

- **-1 = FALSE**
- **1 = TRUE** 
- **0 = UNKNOWN**

### Logical Operations

| A | B | AND | OR | XOR | NOT A |
|---|---|-----|----|----|-------|
| F | F | F   | F  | F   | T     |
| F | T | F   | T  | T   | T     |
| F | U | F   | U  | U   | T     |
| T | F | F   | T  | T   | F     |
| T | T | T   | T  | F   | F     |
| T | U | U   | T  | U   | F     |
| U | F | U   | U  | U   | U     |
| U | T | U   | T  | U   | U     |
| U | U | U   | U  | U   | U     |

### Real-World Applications

#### Customer Segmentation
```python
# E-commerce customer analysis with missing data
high_value_customer = TernaryLogicalExpressionNode("AND", [
    TernaryColumnExpressionNode("account_status", "==", "active"),
    TernaryColumnExpressionNode("annual_spend", ">", 10000),
    TernaryColumnExpressionNode("loyalty_tier", "==", "gold")
])

# Results:
# - All conditions TRUE → Definitely high-value
# - Any condition FALSE → Definitely not high-value  
# - UNKNOWN conditions with no FALSE → Uncertain (requires follow-up)
```

#### Payment Method Validation
```python
# Exactly one payment method should be active (XOR logic)
valid_payment_setup = TernaryExpressionBuilder.xor(
    TernaryExpressionBuilder.eq("credit_card", "active"),
    TernaryExpressionBuilder.eq("bank_account", "active"),
    TernaryExpressionBuilder.eq("digital_wallet", "active")
)

# TRUE: Exactly one method active
# FALSE: Zero or multiple methods active  
# UNKNOWN: Cannot determine due to missing data
```

## 🏗️ Architecture

### Expression Node Hierarchy

```python
ExpressionNode (Abstract)
├── LiteralExpressionNode
├── ColumnExpressionNode  
└── LogicalExpressionNode
    ├── BooleanLogicalExpressionNode
    └── TernaryLogicalExpressionNode
```

### Visitor Pattern

Backend-specific implementations through the visitor pattern:

```python
# Automatic visitor selection (recommended)
result = expression.eval_is_true()(dataframe)

# Manual visitor selection (traditional approach)
from mountainash_expressions.visitors.ternary import PolarsTernaryExpressionVisitor
visitor = PolarsTernaryExpressionVisitor()
result = expression.accept(visitor)(dataframe)
```

### Supported Backends

- **Polars**: Native polars expressions
- **Ibis**: Universal SQL-like expressions
- **Pandas**: DataFrame operations
- **PyArrow**: Table/RecordBatch operations
- **NumPy**: Array operations (planned)
- **Xarray**: N-dimensional arrays (planned)
- **PySpark**: Distributed processing (planned)

## 🧪 Development

### Prerequisites

- Python 3.10+
- [Hatch](https://hatch.pypa.io/) for environment management

### Setup

```bash
git clone https://github.com/mountainash-io/mountainash-expressions.git
cd mountainash-expressions
hatch shell
```

### Running Tests

```bash
# Full test suite with coverage
hatch run test:test

# Quick tests (no coverage)
hatch run test:test-quick

# Target specific tests
hatch run test:test-target tests/ternary/test_gold_standard_api.py

# Performance benchmarks
hatch run test:test-perf
```

### Code Quality

```bash
# Linting
hatch run ruff:check
hatch run ruff:fix

# Type checking
hatch run mypy:check

# Build package
hatch build
```

## 📊 Test Categories

- **Unit Tests**: Core logic validation (`hatch run test:test-unit`)
- **Integration Tests**: Cross-backend compatibility (`hatch run test:test-integration`)
- **Performance Tests**: Benchmark suite (`hatch run test:test-performance`)
- **Gold Standard Tests**: Comprehensive API validation

## 🔍 Usage Examples

### Data Quality Rules

```python
# Age eligibility with boundary validation
age_eligible = TernaryExpressionBuilder.between("age", 18, 65)
# If upper boundary is UNKNOWN, result is UNKNOWN (prevents false positives)

# Multi-condition data quality
clean_record = TernaryLogicalExpressionNode("AND", [
    TernaryColumnExpressionNode("email", "IS_NOT_NULL", None),
    TernaryColumnExpressionNode("phone", "IS_NOT_NULL", None),
    TernaryColumnExpressionNode("address", "!=", "")
])
```

### Business Logic Implementation

```python
# Complex eligibility criteria
loan_eligible = TernaryLogicalExpressionNode("AND", [
    TernaryColumnExpressionNode("credit_score", ">=", 650),
    TernaryColumnExpressionNode("income", ">", 50000),
    TernaryLogicalExpressionNode("OR", [
        TernaryColumnExpressionNode("employment_years", ">=", 2),
        TernaryColumnExpressionNode("assets", ">", 100000)
    ])
])

# Risk assessment with multiple evaluation modes
df_approved = df.filter(loan_eligible.eval_is_true()(df))        # Auto-approve
df_manual_review = df.filter(loan_eligible.eval_is_unknown()(df))  # Manual review
df_rejected = df.filter(loan_eligible.eval_is_false()(df))       # Auto-reject
```

### Cross-Backend Compatibility

```python
# Same expression works across different DataFrame types
import pandas as pd
import polars as pl
import ibis

expression = BooleanExpressionBuilder.gt("value", 100)

# Works automatically with any backend
pandas_result = pd_df.query(expression.eval_is_true()(pd_df))
polars_result = pl_df.filter(expression.eval_is_true()(pl_df))
ibis_result = ibis_table.filter(expression.eval_is_true()(ibis_table))
```

## 📚 Documentation

- [Contributing Guidelines](CONTRIBUTING.md)
- [Testing Procedures](TESTING.md)
- [Release Process](RELEASE.md)
- [API Documentation](https://mountainash-expressions.readthedocs.io/)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- Development setup
- Branching strategy
- Code standards
- Testing requirements
- Pull request process

## 📋 Requirements

### Core Dependencies

- `ibis-framework[pandas,sqlite,duckdb] == 10.4.0`
- `numpy >=1.23.2,<3`
- `pandas >=2.2.0`
- `polars ==1.16.0`
- `pyarrow ==17.0.0`
- `narwhals` (cross-DataFrame compatibility)

### Optional Dependencies

- `xarray ==2024.11.0` (N-dimensional arrays)
- `pyspark >=3.5.0` (distributed processing)
- Database backends: `mssql`, `snowflake`, `postgres`, `bigquery`, `trino`

## 🏷️ Versioning

We use [CalVer](https://calver.org/) versioning: `YYYY.MM.MICRO`

- **YYYY.MM.0.0**: Release candidates
- **YYYY.MM.1.0**: Production releases  
- **YYYY.MM.1.x**: Updates and patches

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [mountainash-dataframes](https://github.com/mountainash-io/mountainash-dataframes): DataFrame abstractions and operations
- [mountainash-constants](https://github.com/mountainash-io/mountainash-constants): Shared constants and enums
- [mountainash-settings](https://github.com/mountainash-io/mountainash-settings): Configuration management

## 🏔️ Mountain Ash Ecosystem

Mountain Ash Expressions is part of the Mountain Ash ecosystem of Python packages designed for data science and engineering workflows. The ecosystem provides:

- **Unified APIs** across different data processing backends
- **Type-safe operations** with comprehensive validation
- **Real-world data handling** with sophisticated missing value support
- **Performance optimization** through mathematical foundations
- **Enterprise-ready** architecture patterns and testing

---

**Built with ❤️ by the Mountain Ash Team**