# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mountainash-expressions** is a Python package that provides a sophisticated cross-backend DataFrame expression system. The package currently implements **Boolean logic** (TRUE/FALSE) with automatic backend detection across Polars, Narwhals, Ibis (Polars/DuckDB/SQLite), and Pandas. **Ternary logic** (TRUE/FALSE/UNKNOWN) is architecturally designed but not yet implemented.

The package is designed as a foundation for cross-backend DataFrame filtering, mutations, and operations that need consistent expression evaluation regardless of the underlying DataFrame implementation.

## Current Architecture Status

**IMPORTANT**: The package uses an **ExpressionSystem pattern** with a **Universal Visitor** approach. Boolean logic is fully implemented and tested across 6 backends. Ternary logic architecture is designed but awaiting implementation.

**Migration Status:**
- ✅ Boolean logic: Fully implemented and tested
- ✅ ExpressionSystem pattern: Complete
- ✅ Universal visitor with mixins: Complete
- ✅ Cross-backend testing: 703 tests passing
- ⚠️ Ternary logic: Designed but not implemented
- ⚠️ Pandas backend: Detection exists, limited testing

## Actual Package Structure

```
src/mountainash_expressions/
├── __init__.py                          # Main package exports
├── __version__.py                       # Package version
├── constants.py                         # Legacy redirect to core.constants
│
├── api/                                 # PUBLIC API (User-facing)
│   ├── __init__.py                     # Exports: col(), lit(), filter(), etc.
│   ├── expression_builder.py          # Fluent API builder (700+ lines)
│   └── temporal_helpers.py             # Natural language time expressions
│
├── core/                                # CORE ARCHITECTURE
│   ├── constants.py                    # Enums: backends, logic types, operators
│   │
│   ├── expression_nodes/               # AST Node Definitions
│   │   ├── __init__.py
│   │   ├── expression_nodes.py        # Base classes: ExpressionNode, etc.
│   │   └── boolean_expression_nodes.py # Boolean-specific node types
│   │
│   ├── expression_visitors/            # VISITOR PATTERN (Mixin-based)
│   │   ├── __init__.py
│   │   ├── expression_visitor.py      # Abstract base visitor
│   │   ├── universal_boolean_visitor.py # ⭐ MAIN VISITOR (776 lines)
│   │   ├── visitor_factory.py         # Auto-registration & backend detection
│   │   │
│   │   ├── arithmetic_mixins/         # +, -, *, /, %, **
│   │   ├── boolean_mixins/            # AND, OR, NOT, ==, !=, <, >, <=, >=
│   │   ├── common_mixins/             # col, lit, cast, native
│   │   ├── conditional_mixins/        # if-else, when-then, coalesce
│   │   ├── pattern_mixins/            # Regex, glob, pattern matching
│   │   ├── string_mixins/             # String operations
│   │   └── temporal_mixins/           # DateTime operations
│   │
│   ├── expression_system/              # BACKEND ABSTRACTION INTERFACE
│   │   ├── __init__.py
│   │   └── base.py                    # Abstract ExpressionSystem class
│   │
│   ├── backend_visitors/               # Legacy BackendVisitor protocol
│   │   ├── __init__.py
│   │   └── backend_visitor.py
│   │
│   └── expression_parameters/          # Parameter handling
│       ├── __init__.py
│       └── expression_parameter.py
│
├── backends/                            # BACKEND IMPLEMENTATIONS
│   ├── polars/
│   │   └── expression_system/
│   │       └── polars_expression_system.py      # Returns pl.Expr (663 lines)
│   │
│   ├── narwhals/
│   │   └── expression_system/
│   │       └── narwhals_expression_system.py    # Returns nw.Expr (734 lines)
│   │
│   └── ibis/
│       └── expression_system/
│           └── ibis_expression_system.py        # Returns ir.Expr (800+ lines)
│
└── _deprecated/                         # OLD CODE (being phased out)
    ├── _boolean_expression_visitor.py   # Old visitor (11KB)
    └── _backup/                         # Previous iterations
```

## Test Structure

```
tests/
├── conftest.py                          # ⭐ 500+ lines of fixtures
├── fixtures/
│   └── backend_helpers.py              # Cross-backend utilities
│
├── cross_backend/                       # ⭐ MAIN TEST SUITE
│   ├── test_arithmetic.py              # +, -, *, /, %, **
│   ├── test_boolean.py                 # AND, OR, NOT, comparisons
│   ├── test_conditional.py             # if-else, when-then, coalesce
│   ├── test_expression_builder_api.py  # Fluent API tests
│   ├── test_pattern.py                 # Regex, glob, pattern matching
│   ├── test_string.py                  # String operations
│   ├── test_temporal_advanced.py       # Complex datetime ops
│   └── test_temporal_natural.py        # Natural language time (refactored)
│
├── unit/                                # Unit tests
├── integration/                         # Integration tests
├── backends/                            # Backend-specific tests
└── _deprecated/                         # Old tests (moved here)
```

## Core Architecture: ExpressionSystem Pattern

### The Architecture Flow

```python
# 1. User builds expression (backend-agnostic AST)
User API (col(), lit(), etc.)
    ↓
ExpressionBuilder (fluent interface)
    ↓
ExpressionNode (AST: BooleanComparisonNode, etc.)

# 2. Compile to backend-native expression
ExpressionNode.accept(visitor)
    ↓
UniversalBooleanExpressionVisitor (injected with ExpressionSystem)
    ↓
ExpressionSystem.col() / .eq() / .and_() / etc.
    ↓
Backend-native expression (pl.Expr | nw.Expr | ir.Expr)

# 3. Execute on DataFrame
DataFrame.filter(backend_expr) → Filtered DataFrame
```

### Key Components

#### 1. ExpressionSystem (Abstract Interface)

Located: `core/expression_system/base.py`

The ExpressionSystem defines the interface all backends must implement:

```python
class ExpressionSystem(ABC):
    """Abstract interface for backend-specific expression generation."""

    @abstractmethod
    def col(self, name: str) -> BackendExpr:
        """Column reference"""

    @abstractmethod
    def lit(self, value: Any) -> BackendExpr:
        """Literal value"""

    @abstractmethod
    def eq(self, left: BackendExpr, right: BackendExpr) -> BackendExpr:
        """Equality comparison"""

    # ... many more methods for all operations
```

#### 2. Backend ExpressionSystems

Each backend implements the ExpressionSystem interface:

- **PolarsExpressionSystem** (`backends/polars/`) → Returns `pl.Expr`
- **NarwhalsExpressionSystem** (`backends/narwhals/`) → Returns `nw.Expr`
- **IbisExpressionSystem** (`backends/ibis/`) → Returns `ir.Expr`

Example:
```python
class PolarsExpressionSystem(ExpressionSystem):
    def col(self, name: str) -> pl.Expr:
        return pl.col(name)

    def eq(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        return left == right
```

#### 3. Universal Visitor

`UniversalBooleanExpressionVisitor` (`core/expression_visitors/universal_boolean_visitor.py`)

The visitor:
- Works with **any** ExpressionSystem through dependency injection
- Composed of **7 mixin categories** for different operation types
- Returns backend-native expressions directly (not Callables)
- Single implementation handles all backends

Mixin composition:
```python
class UniversalBooleanExpressionVisitor(
    # Common operations
    CastExpressionVisitor,
    LiteralExpressionVisitor,
    SourceExpressionVisitor,

    # Boolean logic
    BooleanCollectionExpressionVisitor,
    BooleanComparisonExpressionVisitor,
    BooleanConstantExpressionVisitor,
    BooleanOperatorsExpressionVisitor,
    BooleanUnaryExpressionVisitor,

    # Other operations
    ArithmeticOperatorsExpressionVisitor,
    StringOperatorsExpressionVisitor,
    PatternOperatorsExpressionVisitor,
    ConditionalOperatorsExpressionVisitor,
    TemporalOperatorsExpressionVisitor,
):
    def __init__(self, backend: ExpressionSystem):
        self.backend = backend  # Injected ExpressionSystem
```

Each mixin uses `self.backend` to generate expressions:
```python
# Example from boolean_mixins/
def visit_comparison_expression(self, node):
    left = self._process_operand(node.left)
    right = self._process_operand(node.right)
    return self.backend.eq(left, right)  # Uses injected backend
```

#### 4. Visitor Factory

`ExpressionVisitorFactory` (`core/expression_visitors/visitor_factory.py`)

Responsibilities:
- Auto-detects backend from DataFrame type
- Auto-registers ExpressionSystems on import
- Creates visitor with appropriate ExpressionSystem

```python
# Backend detection priority:
# 1. Narwhals (must check first - wraps other backends)
# 2. Ibis
# 3. Polars
# 4. Pandas (detection exists, limited testing)

visitor = ExpressionVisitorFactory.get_visitor_for_backend(
    df,
    CONST_LOGIC_TYPES.BOOLEAN,
    use_universal=True
)
```

### Key Design Decisions

✅ **Eager compilation** - Compile once, reuse many times
✅ **Reusable expressions** - Same backend expression works on multiple DataFrames
✅ **Inspectable** - Can examine backend expression before execution
✅ **Dependency injection** - Visitor doesn't know which backend it's using
❌ **NOT lazy** - No nested Callables (old approach removed)

**Before (Legacy - REMOVED):**
```python
# Visitor methods returned Callables (lambdas)
def _B_eq(self, left, right) -> Callable:
    return lambda table: left.accept(self)(table) == right.accept(self)(table)

# Compilation and execution conflated
result = node.eval()(df)  # Compiles + executes every time
```

**After (Current):**
```python
# Visitor methods return backend expressions directly
def visit_comparison_expression(self, node) -> pl.Expr | nw.Expr | ir.Expr:
    left_expr = self._process_operand(node.left)
    right_expr = self._process_operand(node.right)
    return self.backend.eq(left_expr, right_expr)

# Compilation separate from execution
backend_expr = node.accept(visitor)  # Compile once
result1 = df1.filter(backend_expr)   # Reuse
result2 = df2.filter(backend_expr)   # Reuse
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

# Or use helper functions (compile + execute)
result = ma.filter(df, ma.col("age").gt(30))
```

### Core Functions

**Column & Literal:**
- `col(name)` - Column reference
- `lit(value)` - Literal value

**Helper Functions:**
- `filter(df, expr)` - Filter DataFrame
- `select(df, *exprs)` - Select columns
- `with_columns(df, **exprs)` - Add/modify columns

**Logic Combinators:**
- `and_(*exprs)` - Logical AND
- `or_(*exprs)` - Logical OR
- `not_(expr)` - Logical NOT

**Conditional:**
- `when(cond).then(val).otherwise(alt)` - If-then-else
- `coalesce(*values)` - First non-null value

**Temporal Helpers (Natural Language):**
- `within_last(col, "10 minutes")` - Like journalctl
- `older_than(col, "7 days")` - Like find -mtime
- `time_ago("2 hours")` - Absolute time calculation
- `between_last(col, "1 hour", "3 hours")` - Time range

### ExpressionBuilder Methods

The fluent interface (`api/expression_builder.py`) provides:

**Comparison:**
- `.eq(other)` / `.ne(other)` - Equality/inequality
- `.lt(other)` / `.le(other)` - Less than/less or equal
- `.gt(other)` / `.ge(other)` - Greater than/greater or equal

**Arithmetic:**
- `.add(other)` / `.sub(other)` - Addition/subtraction
- `.mul(other)` / `.div(other)` - Multiplication/division
- `.mod(other)` / `.pow(other)` - Modulo/exponentiation

**Logic:**
- `.and_(other)` / `.or_(other)` - Logical AND/OR
- `.not_()` - Logical NOT
- `.is_in(values)` / `.is_not_in(values)` - Membership

**String:**
- `.contains(pattern)` / `.startswith(prefix)` / `.endswith(suffix)`
- `.lower()` / `.upper()` / `.strip()`
- `.len()` / `.slice(start, end)`

**Temporal:**
- `.year()` / `.month()` / `.day()` - Extract components
- `.hour()` / `.minute()` / `.second()` - Time components
- `.date()` / `.time()` - Date/time extraction

**Conditional:**
- `.when(cond).then(val).otherwise(alt)` - Conditional expression
- `.coalesce(other)` - First non-null

**Casting:**
- `.cast(dtype)` - Type conversion

## Backend Support

### Fully Working (3 backends)

1. **Polars** ✅
   - Native type: `pl.Expr`
   - Implementation: `backends/polars/expression_system/polars_expression_system.py` (663 lines)
   - Test success: 100%
   - Status: Production ready

2. **Narwhals** ✅
   - Native type: `nw.Expr`
   - Implementation: `backends/narwhals/expression_system/narwhals_expression_system.py` (734 lines)
   - Test success: 100%
   - Status: Production ready
   - Note: Auto-rejects Narwhals-wrapped Ibis (incompatible)

3. **Ibis-Polars** ✅
   - Native type: `ir.Expr` (Polars backend)
   - Implementation: `backends/ibis/expression_system/ibis_expression_system.py` (800+ lines)
   - Test success: 100%
   - Status: Production ready

### Partial Support (2 backends)

4. **Ibis-DuckDB** ⚠️
   - Native type: `ir.Expr` (DuckDB backend)
   - Test success: Most tests pass
   - Known issues:
     - Modulo semantics differ from Python (remainder vs modulo)
     - Recent DuckDB dependency issues (resolved in latest versions)
   - Status: Usable with caveats

5. **Ibis-SQLite** ⚠️
   - Native type: `ir.Expr` (SQLite backend)
   - Test success: Limited (14% for temporal, arithmetic issues)
   - Known issues:
     - Integer division instead of float division (20/3 = 6, not 6.666...)
     - Modulo semantics differ
     - Temporal operations limited
   - Status: Limited use

### Detection Only (1 backend)

6. **Pandas** 📋
   - Detection: Implemented in visitor factory
   - Testing: Limited
   - Status: Needs implementation work

### Not Implemented

- **PyArrow** - Commented out in backend detection

## Logic Systems

### Boolean Logic (IMPLEMENTED) ✅

**Status:** Fully implemented and tested

**Values:** TRUE, FALSE

**Components:**
- Visitor: `UniversalBooleanExpressionVisitor` (776 lines)
- Nodes: `BooleanExpressionNode`, `BooleanComparisonExpressionNode`, etc.
- Operations: All comparison, logical, arithmetic, string, pattern, temporal, conditional

**Test Coverage:**
- 703 tests passing
- 6 backends
- Cross-backend parametrized tests

### Ternary Logic (DESIGNED, NOT IMPLEMENTED) ⚠️

**Status:** Architecture designed, awaiting implementation

**Intended Values:**
- TRUE = -1
- FALSE = 1
- UNKNOWN = 0

**Purpose:** NULL-safe three-valued logic

**What Exists:**
- Constants defined: `CONST_TERNARY_LOGIC_VALUES` in `core/constants.py`
- Legacy node definitions in deprecated code
- Mentioned 82 times in codebase

**What's Missing:**
- No `UniversalTernaryExpressionVisitor`
- No ternary mixins
- No ternary ExpressionSystem methods
- No test suite

**References:**
- "The Silent Ternary Problem" documented in `docs/`

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
# Development dependency
ibis-framework = { path = "/home/nathanielramm/git/ibis", extras = ["pandas", "sqlite", "duckdb"], develop = true }
```

The local fork includes fixes for Polars backend calendar interval handling.

### Mountain Ash Ecosystem

Local development dependencies:

```toml
mountainash-constants = { path = "../mountainash-constants", develop = true }
mountainash-settings = { path = "../mountainash-settings", develop = true }
mountainash-utils-files = { path = "../mountainash-utils-files", develop = true }
mountainash-utils-os = { path = "../mountainash-utils-os", develop = true }
```

## Development Commands

### Essential Daily Commands

**Testing:**
```bash
# Full test suite with coverage
hatch run test:test

# Fast iteration (no coverage)
hatch run test:test-quick

# Specific test file
hatch run test:test-target tests/cross_backend/test_temporal_natural.py

# Specific test function
hatch run test:test-target tests/cross_backend/test_boolean.py::test_and_operation
```

**Linting:**
```bash
hatch run ruff:check      # Check for issues
hatch run ruff:fix        # Auto-fix issues
```

**Type Checking:**
```bash
hatch run mypy:check      # Type safety validation
```

**Build:**
```bash
hatch build               # Build distribution
```

### Test Categories

```bash
hatch run test:test-unit           # Unit tests only
hatch run test:test-integration    # Integration tests only
hatch run test:test-performance    # Performance benchmarks
hatch run test:test-changed        # Only changed files
hatch run test:test-changed-quick  # Changed files (no coverage)
```

### Targeted Testing

```bash
# With coverage
hatch run test:test-target <path>

# Without coverage (fastest)
hatch run test:test-target-quick <path>

# Performance only
hatch run test:test-perf
```

## Known Issues & Backend Inconsistencies

Full documentation: `docs/BACKEND_INCONSISTENCIES.md`

### 1. SQLite Integer Division ⚠️

**Issue:** SQLite performs integer division instead of float division

```python
# Expected (Python, Polars, Pandas)
20 / 3 = 6.666...

# Actual (SQLite)
20 / 3 = 6
```

**Impact:** Breaks cross-backend compatibility for division operations

**Status:** Marked with `pytest.xfail` in tests

### 2. Modulo Semantics ⚠️

**Issue:** Different modulo behavior across backends

```python
# Python/Polars/Pandas (modulo - sign of divisor)
-7 % 3 = 2

# SQLite/DuckDB (remainder - sign of dividend)
-7 % 3 = -1
```

**Impact:** Negative number modulo operations inconsistent

### 3. Ibis Reverse Operator Bug ⚠️

**Issue:** Literal-first operations fail in Ibis <= 11.0.0

```python
# Fails in older Ibis
literal(5) + ibis._['col']  # InputTypeError

# Workaround: Column reference first
ibis._['col'] + literal(5)  # Works
```

**Impact:** Operation order matters with Ibis

**Status:** Fixed in newer Ibis versions

### 4. Temporal Limitations

**Issue:** Backend-specific temporal support varies

- SQLite: Very limited datetime filtering
- Some backends lack full temporal operation support

## Test Results

### Latest Test Run

```
703 tests passing ✅
6 skipped
4 xfailed (expected failures for known issues)
110 xpassed (DuckDB tests now passing after dependency fix)
```

### Success Rates by Backend

| Backend | Status | Success Rate |
|---------|--------|--------------|
| Polars | ✅ | 100% |
| Narwhals | ✅ | 100% |
| Ibis-Polars | ✅ | 100% |
| Ibis-DuckDB | ⚠️ | ~95% (modulo issues) |
| Ibis-SQLite | ⚠️ | 14% temporal, arithmetic issues |
| Pandas | 📋 | Limited testing |

## Common Development Tasks

### Adding a New Backend

1. **Create ExpressionSystem implementation:**
   ```bash
   mkdir -p src/mountainash_expressions/backends/<backend_name>/expression_system
   ```

2. **Implement the interface:**
   ```python
   # <backend_name>_expression_system.py
   from mountainash_expressions.core.expression_system import ExpressionSystem

   class MyBackendExpressionSystem(ExpressionSystem):
       def col(self, name: str) -> MyBackendExpr:
           return my_backend.col(name)

       def eq(self, left, right) -> MyBackendExpr:
           return left == right

       # ... implement all abstract methods
   ```

3. **Register in visitor factory:**
   ```python
   # The @register_expression_system decorator auto-registers
   @register_expression_system(CONST_VISITOR_BACKENDS.MY_BACKEND)
   class MyBackendExpressionSystem(ExpressionSystem):
       ...
   ```

4. **Add backend detection:**
   ```python
   # In visitor_factory.py _identify_backend()
   if isinstance(dataframe, MyBackendDataFrame):
       return CONST_VISITOR_BACKENDS.MY_BACKEND
   ```

5. **Add tests:**
   ```python
   # In tests/conftest.py
   @pytest.fixture
   def my_backend_df():
       return create_my_backend_df(...)

   # Add to cross_backend test parametrization
   ```

### Running Backend-Specific Tests

```bash
# All backends
hatch run test:test tests/cross_backend/

# Specific backend (via pytest -k filter)
hatch run test:test tests/cross_backend/ -k polars
hatch run test:test tests/cross_backend/ -k ibis
hatch run test:test tests/cross_backend/ -k narwhals
```

### Debugging Expression Compilation

```python
import mountainash_expressions as ma

# Build expression
expr = ma.col("age").gt(30)

# Get the AST node
node = expr._node
print(f"Node type: {type(node)}")
print(f"Node: {node}")

# Manually create visitor
from mountainash_expressions.core.expression_visitors import ExpressionVisitorFactory
from mountainash_expressions.core.constants import CONST_LOGIC_TYPES

visitor = ExpressionVisitorFactory.get_visitor_for_backend(
    df,
    CONST_LOGIC_TYPES.BOOLEAN,
    use_universal=True
)

# Compile and inspect
backend_expr = node.accept(visitor)
print(f"Backend expression: {backend_expr}")
print(f"Backend type: {type(backend_expr)}")
```

## Architecture Principles

### 1. Dependency Injection

The visitor doesn't know which backend it's using - the ExpressionSystem is injected at runtime. This enables:
- Single visitor implementation for all backends
- Easy testing (mock ExpressionSystem)
- Clear separation of concerns

### 2. Mixin-Based Composition

The visitor is composed of focused mixins, each handling one operation category:
- Easy to extend (add new mixin)
- Easy to maintain (small, focused files)
- Easy to test (test each mixin independently)

### 3. Backend Isolation

Each backend implementation is self-contained:
- No cross-backend dependencies
- Backend-specific optimizations possible
- Easy to add/remove backends

### 4. Eager Compilation

Expressions compile once and reuse:
- Better performance (no repeated compilation)
- Inspectable results (examine before execution)
- Easier debugging (see what was generated)

### 5. Type Safety

Using protocols and type annotations throughout:
- Better IDE support
- Catch errors at type-check time
- Clear interfaces

## Migration & Legacy Code

### Deprecated Code Locations

1. **`src/mountainash_expressions/_deprecated/`**
   - Old visitor implementation (11,866 bytes)
   - Backup directories

2. **`tests/_deprecated/`**
   - Old test files
   - Moved from project root

3. **Temporary files**
   - 5 `.tmp` files in `boolean_mixins/`
   - 16 total backup/tmp files across project

### What Changed in the Refactoring

**Old Approach (Removed):**
- Visitor methods returned Callables (lambdas)
- Nested lambda hell
- Compilation + execution conflated
- One visitor per backend
- Many small fragmented files

**New Approach (Current):**
- Visitor methods return backend expressions
- Direct expression generation
- Compilation separate from execution
- One universal visitor for all backends
- ExpressionSystem interface for backends
- Mixin-based composition

### Cleanup TODO

- [ ] Remove 5 `.tmp` files from boolean_mixins
- [ ] Clean up 16 backup files
- [ ] Archive `_deprecated/` directories
- [ ] Remove unused imports

## Documentation References

### Internal Documentation

- `docs/BACKEND_INCONSISTENCIES.md` - Backend behavior differences
- `TEST_REFACTORING_COMPLETE.md` - Test refactoring details
- `TEST_REFACTORING_SUMMARY.md` - Test migration summary
- `docs/ExpressionSystemRefactoring/` - Architecture docs
- "The Silent Ternary Problem" - Ternary logic challenges

### Key Source Files

- `api/expression_builder.py:1` - Public API entry point
- `core/expression_visitors/universal_boolean_visitor.py:1` - Main visitor
- `core/expression_visitors/visitor_factory.py:1` - Backend detection
- `core/expression_system/base.py:1` - ExpressionSystem interface
- `backends/polars/expression_system/polars_expression_system.py:1` - Example backend

## Future Work

### Planned Features

1. **Ternary Logic Implementation**
   - Create `UniversalTernaryExpressionVisitor`
   - Implement ternary mixins
   - Add NULL-safe operations
   - Create ternary test suite

2. **Pandas Backend Completion**
   - Comprehensive testing
   - Performance optimization
   - Full operation coverage

3. **PyArrow Backend**
   - Implementation
   - Integration
   - Testing

### Potential Enhancements

- Window functions
- Aggregation expressions
- User-defined functions
- Expression optimization
- Query planning

## Quick Reference

### Import Paths (Actual, Working)

```python
# Public API (recommended)
import mountainash_expressions as ma
from mountainash_expressions import col, lit, filter, when, coalesce

# ExpressionBuilder (if needed directly)
from mountainash_expressions.api import ExpressionBuilder

# Visitor factory (advanced usage)
from mountainash_expressions.core.expression_visitors import ExpressionVisitorFactory

# Constants
from mountainash_expressions.core.constants import (
    CONST_LOGIC_TYPES,
    CONST_VISITOR_BACKENDS,
    CONST_COMPARISON_OPERATORS,
)

# ExpressionSystem (for backend implementation)
from mountainash_expressions.core.expression_system import ExpressionSystem

# Nodes (for AST manipulation)
from mountainash_expressions.core.expression_nodes import (
    ExpressionNode,
    BooleanComparisonExpressionNode,
    # ... other nodes
)
```

### Common Patterns

**Filter DataFrame:**
```python
import mountainash_expressions as ma
filtered = ma.filter(df, ma.col("age").gt(30))
```

**Complex Expression:**
```python
expr = (
    ma.col("age").gt(30)
    .and_(ma.col("score").ge(85))
    .or_(ma.col("premium").eq(True))
)
result = ma.filter(df, expr)
```

**Conditional Column:**
```python
new_df = ma.with_columns(
    df,
    category=ma.when(ma.col("age").lt(18))
        .then(ma.lit("minor"))
        .when(ma.col("age").lt(65))
        .then(ma.lit("adult"))
        .otherwise(ma.lit("senior"))
)
```

**Natural Language Temporal:**
```python
recent = ma.filter(df, ma.within_last(ma.col("timestamp"), "24 hours"))
old = ma.filter(df, ma.older_than(ma.col("created"), "7 days"))
```

## Support & Contributing

For issues, questions, or contributions related to this package, refer to the Mountain Ash project documentation and guidelines.

**Key Points:**
- Always run tests before committing: `hatch run test:test`
- Always run linter: `hatch run ruff:check`
- Always run type checker: `hatch run mypy:check`
- Follow the ExpressionSystem pattern for new backends
- Use mixin composition for new operation categories
- Write cross-backend parametrized tests
