# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mountainash-expressions** is a Python package that provides a sophisticated cross-backend DataFrame expression system. The package implements a **three-layer protocol architecture** with automatic backend detection across Polars, Narwhals, Ibis (Polars/DuckDB/SQLite), and Pandas.

The package is designed as a foundation for cross-backend DataFrame filtering, mutations, and operations that need consistent expression evaluation regardless of the underlying DataFrame implementation.

## Principles Repository

Design principles for this project are documented at:
`/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/`

Consult the principles when making architectural decisions, adding new operations, or resolving design tensions. The principles explain the *why* behind the patterns described in this file.

## Current Architecture Status

**IMPORTANT**: The package uses a **Substrait-aligned architecture** with clear separation between Substrait-standard operations and Mountainash extensions. See [ADR-008](docs/adr/ADR-008-substrait-extension-alignment.md) for full details.

**Architecture Principles:**
- **Substrait-first**: Operations align with [Substrait specification](https://substrait.io/) where possible
- **Extension separation**: Custom operations live in `extensions_mountainash/` directories
- **Minimal AST**: Only 7 node types (ScalarFunctionNode handles most operations)
- **Function registry**: ENUM-based function keys for type safety and IDE autocomplete

**Implementation Status:**
- ✅ Substrait categories: 13 implemented (comparison, boolean, arithmetic, string, datetime, etc.)
- ✅ Mountainash extensions: 6 implemented (ternary, null, name, datetime convenience, etc.)
- ✅ Backend implementations: Polars, Ibis, Narwhals complete
- ✅ Cross-backend testing: 10,000+ lines of tests
- ⚠️ Pandas backend: Detection exists, limited testing

## Package Structure

The codebase follows a **Substrait-aligned architecture** with clear separation between standard and extension components.

```
src/mountainash_expressions/
├── __init__.py                              # Main package exports
├── __version__.py                           # Package version
├── types.py                                 # Type aliases
│
├── core/                                    # CORE ARCHITECTURE
│   ├── constants.py                        # Backend enums, logic types
│   │
│   ├── expression_nodes/
│   │   └── substrait/                      # MINIMAL 7-NODE AST
│   │       ├── exn_base.py                 # Base ExpressionNode
│   │       ├── exn_field_reference.py      # Column references
│   │       ├── exn_literal.py              # Constants
│   │       ├── exn_scalar_function.py      # Universal function node (most ops)
│   │       ├── exn_cast.py                 # Type conversion
│   │       ├── exn_ifthen.py               # Conditionals
│   │       └── exn_singular_or_list.py     # IN/NOT IN
│   │
│   ├── expression_system/
│   │   ├── expsys_base.py                  # Base class & registration
│   │   └── function_keys/
│   │       └── enums.py                    # ALL FUNCTION KEYS (KEY_* & MOUNTAINASH_*)
│   │
│   ├── expression_protocols/
│   │   ├── api_builders/
│   │   │   ├── substrait/                  # Builder protocol stubs
│   │   │   │   └── prtcl_api_bldr_*.py
│   │   │   └── extensions_mountainash/     # Extension builder protocols
│   │   │       └── prtcl_api_bldr_ext_ma_*.py
│   │   │
│   │   └── expression_systems/
│   │       ├── substrait/                  # ExpressionSystem protocols
│   │       │   └── prtcl_expsys_*.py
│   │       └── extensions_mountainash/     # Extension system protocols
│   │           └── prtcl_expsys_ext_ma_*.py
│   │
│   ├── expression_api/
│   │   ├── api_base.py                     # BaseExpressionAPI with compile()
│   │   ├── boolean.py                      # BooleanExpressionAPI (main user class)
│   │   ├── descriptor.py                   # NamespaceDescriptor for .str, .dt, .name
│   │   ├── entrypoints.py                  # col(), lit(), when(), coalesce(), etc.
│   │   └── api_builders/
│   │       ├── substrait/                  # API builder implementations
│   │       │   └── api_bldr_*.py
│   │       └── extensions_mountainash/     # Extension API builders
│   │           └── api_bldr_ext_ma_*.py
│   │
│   └── utils/
│       └── temporal.py                     # Temporal parsing utilities
│
└── backends/                                # BACKEND IMPLEMENTATIONS
    └── expression_systems/
        ├── base.py                         # Backend registration
        │
        ├── polars/
        │   ├── __init__.py                 # PolarsExpressionSystem composition
        │   ├── base.py                     # PolarsBaseExpressionSystem
        │   ├── substrait/                  # Substrait implementations
        │   │   ├── expsys_pl_scalar_comparison.py
        │   │   ├── expsys_pl_scalar_boolean.py
        │   │   ├── expsys_pl_scalar_arithmetic.py
        │   │   ├── expsys_pl_scalar_string.py
        │   │   ├── expsys_pl_scalar_datetime.py
        │   │   └── ... (13 Substrait categories)
        │   └── extensions_mountainash/     # Extension implementations
        │       ├── expsys_pl_ext_ma_scalar_ternary.py
        │       ├── expsys_pl_ext_ma_null.py
        │       ├── expsys_pl_ext_ma_name.py
        │       └── ... (6 extension categories)
        │
        ├── ibis/                           # Same structure as polars/
        │   ├── substrait/
        │   │   └── expsys_ib_*.py
        │   └── extensions_mountainash/
        │       └── expsys_ib_ext_ma_*.py
        │
        └── narwhals/                       # Same structure as polars/
            ├── substrait/
            │   └── expsys_nw_*.py
            └── extensions_mountainash/
                └── expsys_nw_ext_ma_*.py
```

## Naming Conventions

### File Prefixes

| Prefix | Meaning | Example |
|--------|---------|---------|
| `exn_` | Expression Node | `exn_scalar_function.py` |
| `prtcl_` | Protocol | `prtcl_expsys_scalar_comparison.py` |
| `api_bldr_` | API Builder | `api_bldr_scalar_comparison.py` |
| `expsys_` | Expression System (backend) | `expsys_pl_scalar_comparison.py` |
| `ext_ma_` | Mountainash Extension | `expsys_pl_ext_ma_null.py` |

### Backend Prefixes

| Prefix | Backend |
|--------|---------|
| `pl_` | Polars |
| `ib_` | Ibis |
| `nw_` | Narwhals |

### Function Key Enums

| Type | Pattern | Example |
|------|---------|---------|
| Substrait | `KEY_<CATEGORY>` | `KEY_SCALAR_COMPARISON.EQUAL` |
| Mountainash | `MOUNTAINASH_<CATEGORY>` | `MOUNTAINASH_TERNARY.T_EQ` |

### Class Naming

| Component | Substrait Pattern | Mountainash Pattern |
|-----------|-------------------|---------------------|
| Protocol | `Substrait<Category>ExpressionSystemProtocol` | `MountainAsh<Category>ExpressionSystemProtocol` |
| Backend | `<Backend><Category>ExpressionSystem` | `<Backend><Category>ExtensionSystem` |

## Implemented Categories

### Substrait Categories (13)

| Category | Function Key Enum | Operations |
|----------|-------------------|------------|
| `scalar_comparison` | `KEY_SCALAR_COMPARISON` | equal, lt, gt, lte, gte, between, is_null, coalesce, etc. |
| `scalar_boolean` | `KEY_SCALAR_BOOLEAN` | and, or, not, xor |
| `scalar_arithmetic` | `KEY_SCALAR_ARITHMETIC` | add, subtract, multiply, divide, modulo, power |
| `scalar_string` | `KEY_SCALAR_STRING` | upper, lower, trim, contains, starts_with, etc. |
| `scalar_datetime` | `KEY_SCALAR_DATETIME` | extract |
| `scalar_rounding` | `KEY_SCALAR_ROUNDING` | round, ceil, floor |
| `scalar_logarithmic` | `KEY_SCALAR_LOGARITHMIC` | log, log10, log2 |
| `scalar_set` | `KEY_SCALAR_SET` | index_in |
| `scalar_aggregate` | `KEY_SCALAR_AGGREGATE` | count |
| `field_reference` | `KEY_FIELD_REFERENCE` | col |
| `literal` | `KEY_LITERAL` | lit |
| `cast` | `KEY_CAST` | cast |
| `conditional` | `KEY_CONDITIONAL` | if_then_else |

### Mountainash Extensions (6)

| Category | Function Key Enum | Operations |
|----------|-------------------|------------|
| `ext_ma_scalar_ternary` | `MOUNTAINASH_TERNARY` | t_eq, t_ne, t_and, t_or, t_not, is_true, maybe_true, etc. |
| `ext_ma_datetime` | `MOUNTAINASH_DATETIME` | year, month, day, add_days, diff_hours, etc. |
| `ext_ma_null` | `MOUNTAINASH_NULL` | fill_null, null_if |
| `ext_ma_name` | `MOUNTAINASH_NAME` | alias, prefix, suffix |
| `ext_ma_scalar_arithmetic` | `MOUNTAINASH_ARITHMETIC` | floor_divide |
| `ext_ma_scalar_boolean` | `MOUNTAINASH_COMPARISON` | xor_parity, is_close |

## Test Structure

```
tests/
├── conftest.py                          # ~606 lines of fixtures
├── fixtures/
│   └── backend_helpers.py              # Cross-backend utilities (~329 lines)
│
├── cross_backend/                       # MAIN TEST SUITE
│   ├── test_arithmetic.py              # (~637 lines)
│   ├── test_boolean.py                 # (~605 lines)
│   ├── test_conditional.py             # (~408 lines)
│   ├── test_expression_builder_api.py  # Fluent API tests (~775 lines)
│   ├── test_native.py                  # Native expression tests (~509 lines)
│   ├── test_pattern.py                 # Regex, pattern matching (~577 lines)
│   ├── test_string.py                  # String operations (~748 lines)
│   ├── test_temporal_advanced.py       # Complex datetime ops (~591 lines)
│   ├── test_temporal_natural.py        # Natural language time (~411 lines)
│   ├── test_ternary.py                 # Ternary logic operations (~800 lines)
│   ├── test_ternary_auto_booleanize.py # Auto-booleanization (~1,600 lines)
│   └── test_t_col.py                   # t_col() as configurable nullif (~1,100 lines)
│
├── unit/
│   ├── test_namespace_infrastructure.py # (~582 lines)
│   └── test_protocol_alignment.py      # Protocol-implementation alignment (~711 lines)
├── integration/
└── backends/
```


**Total Test Lines: ~11,000+** (including 163 auto-booleanization tests and 116 t_col tests)

## Core Architecture: Substrait-Aligned Design

### The Minimal AST (7 Node Types)

All expressions compile to one of these Substrait-aligned node types:

```python
ExpressionNode (base class)
├── FieldReferenceNode(column)           # Column references: col("age")
├── LiteralNode(value)                   # Constants: lit(30)
├── ScalarFunctionNode(function, args)   # 90% of operations
├── IfThenNode(condition, then, else)    # Conditionals: when().then().otherwise()
├── CastNode(expression, target_type)    # Type conversions: .cast(int)
└── SingularOrListNode(values)           # IN / NOT IN operations
```

**Key insight**: Most operations use `ScalarFunctionNode` with a function key ENUM, rather than category-specific node types.

### The Architecture Flow

```python
# 1. User builds expression (creates AST)
ma.col("age").gt(30)
    ↓
API Builder: api_bldr_scalar_comparison.py
    ↓
Creates: ScalarFunctionNode(
    function_key=KEY_SCALAR_COMPARISON.GT,
    arguments=[FieldReferenceNode("age"), LiteralNode(30)]
)

# 2. Compile to backend-native expression
expr.compile(df)
    ↓
Backend detection → PolarsExpressionSystem
    ↓
Visitor dispatches based on function_key
    ↓
PolarsScalarComparisonExpressionSystem.gt(left, right)
    ↓
Returns: pl.col("age").gt(30)

# 3. Execute on DataFrame
df.filter(backend_expr) → Filtered DataFrame
```

### Protocol Layer

Each category has an ExpressionSystemProtocol that backends implement:

```python
# core/expression_protocols/expression_systems/substrait/prtcl_expsys_scalar_comparison.py
class SubstraitScalarComparisonExpressionSystemProtocol(Protocol):
    """Protocol for comparison operations."""

    def equal(self, x: SupportedExpressions, y: SupportedExpressions, /) -> SupportedExpressions:
        """Whether two values are equal."""
        ...

    def lt(self, x: SupportedExpressions, y: SupportedExpressions, /) -> SupportedExpressions:
        """Less than comparison."""
        ...

# Mountainash extension protocols
# core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_null.py
class MountainAshNullExpressionSystemProtocol(Protocol):
    def fill_null(self, input: SupportedExpressions, replacement: SupportedExpressions, /) -> SupportedExpressions:
        ...
```

### Backend Implementation Layer

Each backend implements the protocols for its expression type:

```python
# backends/expression_systems/polars/substrait/expsys_pl_scalar_comparison.py
class PolarsScalarComparisonExpressionSystem(
    PolarsBaseExpressionSystem,
    SubstraitScalarComparisonExpressionSystemProtocol
):
    def equal(self, x: PolarsExpr, y: PolarsExpr, /) -> PolarsExpr:
        return x.eq(y)

    def lt(self, x: PolarsExpr, y: PolarsExpr, /) -> PolarsExpr:
        return x.lt(y)
```

### Backend Composition

Each backend composes all protocol implementations:

```python
# backends/expression_systems/polars/__init__.py
@register_expression_system(CONST_VISITOR_BACKENDS.POLARS)
class PolarsExpressionSystem(
    # Substrait categories
    PolarsScalarComparisonExpressionSystem,
    PolarsScalarBooleanExpressionSystem,
    PolarsScalarArithmeticExpressionSystem,
    PolarsScalarStringExpressionSystem,
    PolarsScalarDatetimeExpressionSystem,
    # ... 13 Substrait categories
    # Mountainash extensions
    PolarsTernaryExtensionSystem,
    PolarsNullExtensionSystem,
    PolarsNameExtensionSystem,
    # ... 6 extension categories
):
    """Complete Polars backend ExpressionSystem."""
    pass
```

## Public API (User-Facing)

### Main Entry Point

```python
import mountainash_expressions as ma

# Build expression (backend-agnostic AST)
expr = ma.col("age").gt(30).and_(ma.col("score").ge(85))

# Compile to backend-native expression
backend_expr = expr.compile(df)

# Use with DataFrame
result = df.filter(backend_expr)
```

### Core Functions

```python
# Column & Literal
col(name)           # Column reference
lit(value)          # Literal value

# Horizontal operations
coalesce(*exprs)    # First non-null value
greatest(*exprs)    # Maximum value (element-wise)
least(*exprs)       # Minimum value (element-wise)

# Conditional
when(cond).then(val).otherwise(alt)  # If-then-else

# Native expression passthrough
native(backend_expr)  # Wrap backend-specific expression

# Ternary column (configurable nullif)
t_col(name, unknown={...})  # Column with custom UNKNOWN values
```

## Ternary Logic System

### Overview

Ternary logic provides three-valued logic semantics where:
- **TRUE (1)**: Definitely true
- **UNKNOWN (0)**: Cannot determine (NULL, missing, or custom sentinel)
- **FALSE (-1)**: Definitely false

Unlike boolean logic where NULL typically propagates as NULL, ternary logic uses explicit UNKNOWN (0) sentinel values, enabling powerful data validation scenarios.

### Key Concepts

**Why Ternary?**
- Boolean: `True AND NULL = NULL` (ambiguous)
- Ternary: `TRUE AND UNKNOWN = UNKNOWN (0)` (explicit sentinel value)

Ternary logic enables filtering strategies like "exclude only definitely false" or "include anything that might be true."

### t_col() - Configurable Nullif

`t_col()` creates a ternary-aware column reference that treats custom values as UNKNOWN:

```python
import mountainash_expressions as ma

# Standard column: only NULL is unknown
expr = ma.col("score").t_gt(70)  # NULL → UNKNOWN

# With custom sentinel: -99999 treated as UNKNOWN (like SQL NULLIF)
expr = ma.t_col("score", unknown={-99999}).t_gt(70)

# Multiple sentinels
expr = ma.t_col("value", unknown={-999, -9999, ""}).t_eq("active")
```

**Use Cases:**
- Legacy systems with numeric sentinels (-99999, 0, -1)
- Empty string as missing
- Special marker values ("N/A", "UNKNOWN")
- Multi-system data with different null representations

### Ternary Operations

**Comparison (return -1/0/1):**
```python
.t_eq(other)        # Ternary equal
.t_ne(other)        # Ternary not equal
.t_gt(other)        # Ternary greater than
.t_lt(other)        # Ternary less than
.t_ge(other)        # Ternary greater or equal
.t_le(other)        # Ternary less or equal
.t_is_in(values)    # Ternary membership
.t_is_not_in(values) # Ternary non-membership
```

**Logical (min/max semantics):**
```python
.t_and(*others)     # Minimum: T∧U=U, T∧F=F, U∧F=F
.t_or(*others)      # Maximum: T∨U=T, T∨F=T, U∨F=U
.t_not()            # Sign flip: ¬T=F, ¬U=U, ¬F=T
.t_xor(*others)     # Exactly one TRUE
.t_xor_parity(*others) # Odd number of TRUEs
```

**Constants:**
```python
ma.always_true()    # Constant 1
ma.always_false()   # Constant -1
ma.always_unknown() # Constant 0
```

### Auto-Booleanization

Ternary expressions must be converted to boolean for DataFrame filtering. The `compile()` method accepts a `booleanizer` parameter:

```python
# Default: is_true() - only TRUE(1) passes filter
expr.compile(df)                      # TRUE → True, else → False
expr.compile(df, booleanizer="is_true")

# maybe_true() - lenient, gives benefit of doubt
expr.compile(df, booleanizer="maybe_true")  # TRUE or UNKNOWN → True

# No booleanization - get raw -1/0/1 values
expr.compile(df, booleanizer=None)

# Custom callable
expr.compile(df, booleanizer=lambda e: e.ge(0))  # UNKNOWN or TRUE
```

**Built-in Booleanizers:**
| Booleanizer | TRUE(1) | UNKNOWN(0) | FALSE(-1) |
|-------------|---------|------------|-----------|
| `is_true` (default) | True | False | False |
| `maybe_true` | True | True | False |
| `is_false` | False | False | True |
| `maybe_false` | False | True | True |
| `is_unknown` | False | True | False |
| `is_known` | True | False | True |

### Bidirectional Coercion

The namespace layer automatically coerces between boolean and ternary:

```python
# Boolean expression used in ternary operation → auto-wrapped with to_ternary()
ma.col("active").eq(True).t_and(ma.col("score").t_gt(70))
# Internally: to_ternary(eq(...)).t_and(t_gt(...))

# Ternary expression used directly → auto-booleanized at compile
result = df.filter(ma.col("value").t_gt(50).compile(df))
# Internally: compile applies is_true() booleanizer
```

### Ternary Logic Examples

```python
import mountainash_expressions as ma

# Basic ternary comparison
expr = ma.col("score").t_gt(70)  # Returns -1/0/1

# With custom sentinel value (like SQL NULLIF)
expr = ma.t_col("score", unknown={-99999}).t_gt(70)

# Ternary logic chain
expr = (
    ma.t_col("rating", unknown={0}).t_ge(4)
    .t_and(ma.col("verified").t_eq(True))
    .t_or(ma.col("premium").t_eq(True))
)

# Different booleanization strategies
strict_filter = expr.compile(df, booleanizer="is_true")   # Only definitely good
lenient_filter = expr.compile(df, booleanizer="maybe_true") # Include uncertain

# Get raw ternary values for analysis
ternary_values = expr.compile(df, booleanizer=None)
```

### BooleanExpressionAPI Methods

**Flat Operations (accessed directly):**

```python
# Comparison
.eq(other)          # Equal (==)
.ne(other)          # Not equal (!=)
.gt(other)          # Greater than (>)
.lt(other)          # Less than (<)
.ge(other)          # Greater than or equal (>=)
.le(other)          # Less than or equal (<=)
.is_close(other, precision)  # Approximately equal
.between(lower, upper)       # Value in range

# Logical
.and_(*others)      # Logical AND
.or_(*others)       # Logical OR
.xor_(*others)      # Logical XOR
.not_()             # Logical NOT
.is_in(values)      # In collection
.is_not_in(values)  # Not in collection
.always_true()      # Constant TRUE
.always_false()     # Constant FALSE

# Arithmetic
.add(other)         # Addition (+)
.subtract(other)    # Subtraction (-)
.multiply(other)    # Multiplication (*)
.divide(other)      # Division (/)
.modulo(other)      # Modulo (%)
.power(other)       # Exponentiation (**)
.floor_divide(other) # Floor division (//)

# Null handling
.is_null()          # Check if null
.is_not_null()      # Check if not null
.fill_null(value)   # Replace nulls

# Type
.cast(dtype)        # Type conversion
```

**Explicit Namespaces (accessed via accessor):**

```python
# String operations (.str)
.str.upper()        # To uppercase
.str.lower()        # To lowercase
.str.trim()         # Strip whitespace
.str.contains(pattern)
.str.starts_with(prefix)
.str.ends_with(suffix)
.str.replace(old, new)
.str.slice(start, end)
.str.len()          # String length

# Date/time operations (.dt)
.dt.year()          # Extract year
.dt.month()         # Extract month
.dt.day()           # Extract day
.dt.hour()          # Extract hour
.dt.minute()        # Extract minute
.dt.second()        # Extract second
.dt.weekday()       # Day of week
.dt.add_days(n)     # Add days
.dt.add_hours(n)    # Add hours
.dt.diff_days(other)   # Difference in days
.dt.diff_hours(other)  # Difference in hours
.dt.truncate(unit)     # Truncate to unit

# Name operations (.name)
.name.alias(new_name)  # Rename column
.name.prefix(prefix)   # Add prefix
.name.suffix(suffix)   # Add suffix
```

**Python Operator Overloading:**

```python
# Comparison
col("a") > col("b")   # .gt()
col("a") >= col("b")  # .ge()
col("a") < col("b")   # .lt()
col("a") <= col("b")  # .le()
col("a") == col("b")  # .eq()
col("a") != col("b")  # .ne()

# Logical
col("a") & col("b")   # .and_()
col("a") | col("b")   # .or_()
col("a") ^ col("b")   # .xor_()
~col("a")             # .not_()

# Arithmetic
col("a") + col("b")   # .add()
col("a") - col("b")   # .subtract()
col("a") * col("b")   # .multiply()
col("a") / col("b")   # .divide()
col("a") // col("b")  # .floor_divide()
col("a") % col("b")   # .modulo()
col("a") ** col("b")  # .power()
-col("a")             # .multiply(-1)
```

## Backend Support

### Fully Implemented (3 backends)

1. **Polars** ✅
   - Native type: `pl.Expr`
   - Implementation: ~1,423 lines
   - All protocol categories implemented
   - Test success: 100%

2. **Narwhals** ✅
   - Native type: `nw.Expr`
   - Implementation: ~991 lines
   - All protocol categories implemented
   - Note: Auto-rejects Narwhals-wrapped Ibis (incompatible)

3. **Ibis** ✅
   - Native type: `ir.Expr`
   - Implementation: ~984 lines
   - Supports multiple backends: Polars, DuckDB, SQLite
   - Test success varies by backend

### Backend-Specific Notes

**Ibis-DuckDB** ⚠️
- Most tests pass
- Modulo semantics differ from Python (remainder vs modulo)

**Ibis-SQLite** ⚠️
- Integer division instead of float division (20/3 = 6, not 6.666...)
- Modulo semantics differ
- Limited temporal operations

**Pandas** 📋
- Detection implemented in visitor factory
- Limited testing
- Needs implementation work

## Dependencies

### Core Dependencies

```toml
# From pyproject.toml
polars = ">=1.35.1"
pandas = ">=2.2.0"
narwhals = "*"
pyarrow = "==17.0.0"
numpy = ">=1.23.2,<3"
```

### Ibis Framework

**IMPORTANT:** Using **local Ibis fork** with Polars calendar interval fix

```toml
ibis-framework = { path = "/home/nathanielramm/git/ibis", extras = ["pandas", "sqlite", "duckdb"] }
```

## Development Commands

### Testing

```bash
# Full test suite with coverage
hatch run test:test

# Fast iteration (no coverage)
hatch run test:test-quick

# Specific test file
hatch run test:test-target tests/cross_backend/test_boolean.py

# Specific test function
hatch run test:test-target tests/cross_backend/test_boolean.py::test_and_operation

# Without coverage (fastest)
hatch run test:test-target-quick <path>
```

### Linting & Type Checking

```bash
hatch run ruff:check      # Check for issues
hatch run ruff:fix        # Auto-fix issues
hatch run mypy:check      # Type safety validation
```

### Building

```bash
hatch build               # Build distribution
```

## Known Issues & Backend Inconsistencies

### 1. SQLite Integer Division

```python
# Expected (Python, Polars, Pandas)
20 / 3 = 6.666...

# Actual (SQLite)
20 / 3 = 6
```

### 2. Modulo Semantics

```python
# Python/Polars/Pandas (modulo - sign of divisor)
-7 % 3 = 2

# SQLite/DuckDB (remainder - sign of dividend)
-7 % 3 = -1
```

### 3. Temporal Limitations

- SQLite: Very limited datetime filtering
- Backend-specific temporal support varies

## Common Development Tasks

### Adding a New Substrait Operation

1. **Add to function key enum:**
   ```python
   # core/expression_system/function_keys/enums.py
   class FKEY_SUBSTRAIT_SCALAR_COMPARISON(Enum):
       NEW_OP = auto()  # Add to appropriate category
   ```

2. **Add to ExpressionSystem protocol:**
   ```python
   # core/expression_protocols/expression_systems/substrait/prtcl_expsys_scalar_comparison.py
   class SubstraitScalarComparisonExpressionSystemProtocol(Protocol):
       def new_op(self, x: SupportedExpressions, y: SupportedExpressions, /) -> SupportedExpressions:
           """Description of new operation."""
           ...
   ```

3. **Implement in API builder:**
   ```python
   # core/expression_api/api_builders/substrait/api_bldr_scalar_comparison.py
   def new_op(self, other) -> BaseExpressionAPI:
       other_node = self._to_node_or_value(other)
       node = ScalarFunctionNode(
           function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.NEW_OP,
           arguments=[self._node, other_node],
       )
       return self._build(node)
   ```

4. **Implement in all backends:**
   ```python
   # backends/expression_systems/polars/substrait/expsys_pl_scalar_comparison.py
   def new_op(self, x: PolarsExpr, y: PolarsExpr, /) -> PolarsExpr:
       return x.some_polars_method(y)

   # backends/expression_systems/ibis/substrait/expsys_ib_scalar_comparison.py
   def new_op(self, x: ir.Expr, y: ir.Expr, /) -> ir.Expr:
       return x.some_ibis_method(y)

   # backends/expression_systems/narwhals/substrait/expsys_nw_scalar_comparison.py
   def new_op(self, x: nw.Expr, y: nw.Expr, /) -> nw.Expr:
       return x.some_narwhals_method(y)
   ```

5. **Add tests:**
   ```python
   # tests/cross_backend/test_boolean.py
   @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
   def test_new_op(backend_name, ...):
       ...
   ```

### Adding a Mountainash Extension

For operations not in Substrait, use the extension pattern:

1. **Add to extension enum:**
   ```python
   # core/expression_system/function_keys/enums.py
   class FKEY_MOUNTAINASH_<CATEGORY>(Enum):
       NEW_OP = "new_op"
   ```

2. **Create/update extension protocol:**
   ```python
   # core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_<category>.py
   class MountainAsh<Category>ExpressionSystemProtocol(Protocol):
       def new_op(self, x: SupportedExpressions, /) -> SupportedExpressions: ...
   ```

3. **Implement in API builder:**
   ```python
   # core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_<category>.py
   ```

4. **Implement in all backends:**
   ```python
   # backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_<category>.py
   # backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_<category>.py
   # backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_<category>.py
   ```

### Debugging Expression Compilation

```python
import mountainash_expressions as ma

# Build expression
expr = ma.col("age").gt(30)

# Inspect the AST node
print(f"Node type: {type(expr._node)}")
print(f"Node: {expr._node}")
print(f"Operator: {expr._node.operator}")

# Compile and inspect
backend_expr = expr.compile(df)
print(f"Backend expression: {backend_expr}")
print(f"Backend type: {type(backend_expr)}")
```

## Architecture Summary

| Layer | Location | Count |
|-------|----------|-------|
| **Expression Nodes** | `core/expression_nodes/substrait/` | 7 node types |
| **Function Keys** | `core/expression_system/function_keys/enums.py` | 13 Substrait + 6 Extension ENUMs |
| **Protocols** | `core/expression_protocols/` | ~20 protocol files |
| **API Builders** | `core/expression_api/api_builders/` | ~20 builder files |
| **Backend: Polars** | `backends/expression_systems/polars/` | 18 implementation files |
| **Backend: Ibis** | `backends/expression_systems/ibis/` | 18 implementation files |
| **Backend: Narwhals** | `backends/expression_systems/narwhals/` | 18 implementation files |
| **Tests** | `tests/` | ~11,000+ lines |

## Quick Reference

### Import Paths

```python
# Public API (recommended)
import mountainash_expressions as ma
from mountainash_expressions import col, lit, coalesce, greatest, least, when, native, t_col

# Expression API classes
from mountainash_expressions import BooleanExpressionAPI, BaseExpressionAPI

# Constants
from mountainash_expressions import CONST_VISITOR_BACKENDS, CONST_LOGIC_TYPES

# Function key enums (for advanced usage)
from mountainash_expressions.core.expression_system.function_keys.enums import (
    KEY_SCALAR_COMPARISON,
    KEY_SCALAR_BOOLEAN,
    KEY_SCALAR_ARITHMETIC,
    MOUNTAINASH_TERNARY,
    MOUNTAINASH_NULL,
)

# Protocols (for type hints / backend implementation)
from mountainash_expressions.core.expression_protocols.expression_systems.substrait import (
    SubstraitScalarComparisonExpressionSystemProtocol,
    SubstraitScalarBooleanExpressionSystemProtocol,
)
from mountainash_expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshNullExpressionSystemProtocol,
    MountainAshTernaryExpressionSystemProtocol,
)

# Nodes (for AST manipulation)
from mountainash_expressions.core.expression_nodes.substrait import (
    ExpressionNode,
    ScalarFunctionNode,
    FieldReferenceNode,
    LiteralNode,
)
```

### Common Patterns

```python
import mountainash_expressions as ma

# Simple filter
result = df.filter(ma.col("age").gt(30).compile(df))

# Complex filter
expr = (
    ma.col("age").gt(30)
    .and_(ma.col("score").ge(85))
    .or_(ma.col("premium").eq(True))
)
result = df.filter(expr.compile(df))

# String operations
expr = ma.col("name").str.lower().str.contains("john")

# Date operations
expr = ma.col("created").dt.year().eq(2024)

# Conditional
expr = ma.when(ma.col("age").lt(18)).then(ma.lit("minor")).otherwise(ma.lit("adult"))

# Coalesce
expr = ma.coalesce(ma.col("phone_mobile"), ma.col("phone_home"), ma.lit("N/A"))

# Arithmetic
expr = ma.col("price") * ma.col("quantity") + ma.col("tax")

# Ternary logic - basic
expr = ma.col("score").t_gt(70)  # Returns -1/0/1
result = df.filter(expr.compile(df))  # Auto-booleanizes with is_true()

# Ternary logic - with custom sentinel (like SQL NULLIF)
expr = ma.t_col("score", unknown={-99999}).t_gt(70)

# Ternary logic - lenient filtering (include uncertain)
result = df.filter(expr.compile(df, booleanizer="maybe_true"))

# Ternary logic - chained operations
expr = (
    ma.t_col("rating", unknown={0}).t_ge(4)
    .t_and(ma.col("active").t_eq(True))
)
```

## Future Work

### Potential Enhancements

- Substrait serialization (to/from Substrait protobuf)
- Window functions (Substrait window extension)
- Additional aggregation expressions
- Unified visitor finalization
- User-defined functions
- Expression optimization


## References

- [ADR-008: Substrait Extension Alignment](docs/adr/ADR-008-substrait-extension-alignment.md) - Full architecture documentation
- [Substrait Specification](https://substrait.io/) - Open standard for data compute operations
- [ADR-002: Substrait Builder Protocols](docs/adr/ADR-002-substrait-builder-protocols.md)
- [ADR-007: Mountainash Extension System](docs/adr/ADR-007-mountainash-extension-system.md)

## GitHub Operations

This project uses [hiivmind-pulse-gh](https://github.com/hiivmind/hiivmind-pulse-gh) for GitHub automation.

**Configuration Location**: `/home/nathanielramm/git/mountainash-io/mountainash/.hiivmind/github`

Use the hiivmind-pulse-gh plugin for all GitHub operations (issues, PRs, milestones, project status) to benefit from automatic context enrichment.
