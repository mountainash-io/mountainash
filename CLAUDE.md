# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mountainash-expressions** is a Python package that provides a sophisticated cross-backend DataFrame expression system. The package implements a **three-layer protocol architecture** with automatic backend detection across Polars, Narwhals, Ibis (Polars/DuckDB/SQLite), and Pandas.

The package is designed as a foundation for cross-backend DataFrame filtering, mutations, and operations that need consistent expression evaluation regardless of the underlying DataFrame implementation.

## Current Architecture Status

**IMPORTANT**: The package uses a **Protocol-Driven Visitor Pattern** with a **three-layer protocol architecture**. All major operation categories are fully implemented and tested across multiple backends.

**Implementation Status:**
- ✅ Boolean logic: Fully implemented and tested
- ✅ Arithmetic operations: Fully implemented
- ✅ String operations: Fully implemented
- ✅ Temporal operations: Fully implemented
- ✅ Horizontal operations (coalesce, greatest, least): Fully implemented
- ✅ Three-layer protocol architecture: Complete
- ✅ Standalone category visitors: Complete (~1,862 lines)
- ✅ AST nodes: Complete (~1,241 lines)
- ✅ Protocol definitions: Complete (~1,081 lines)
- ✅ Namespace-based API: Complete (~2,832 lines)
- ✅ Backend implementations: Complete for Polars (1,423 lines), Ibis (984 lines), Narwhals (991 lines)
- ✅ Cross-backend testing: 7,500+ lines of tests
- ⚠️ Ternary logic: Designed but not implemented
- ⚠️ Pandas backend: Detection exists, limited testing

## Package Structure

```
src/mountainash_expressions/
├── __init__.py                          # Main package exports
├── __version__.py                       # Package version
├── constants.py                         # Legacy redirect to core.constants
├── runtime_imports.py                   # Runtime import utilities
├── types.py                             # Type aliases
│
├── core/                                # CORE ARCHITECTURE
│   ├── constants.py                    # Enums: backends, logic types, operators
│   │
│   ├── expression_api/                 # EXPRESSION API FACADES
│   │   ├── __init__.py                # Exports: BaseExpressionAPI, BooleanExpressionAPI
│   │   ├── base.py                    # BaseExpressionAPI - abstract base with compile()
│   │   ├── boolean.py                 # BooleanExpressionAPI - main user-facing class
│   │   └── descriptor.py              # NamespaceDescriptor for .str, .dt, .name accessors
│   │
│   ├── namespaces/                     # NAMESPACE-BASED API (~2,832 lines)
│   │   ├── __init__.py                # Export all namespaces
│   │   ├── base.py                    # BaseNamespace abstract class
│   │   ├── entrypoints.py             # col(), lit(), coalesce(), greatest(), least(), when(), native()
│   │   ├── boolean.py                 # Comparison & logical operations (~389 lines)
│   │   ├── arithmetic.py              # Math operations (~308 lines)
│   │   ├── string.py                  # String operations (~449 lines)
│   │   ├── datetime.py                # Temporal operations (~705 lines)
│   │   ├── name.py                    # Alias/prefix/suffix (~142 lines)
│   │   ├── null.py                    # Null handling (~113 lines)
│   │   ├── horizontal.py              # Horizontal ops (~101 lines)
│   │   ├── type.py                    # Type casting (~45 lines)
│   │   ├── conditional.py             # When/then/otherwise (~112 lines)
│   │   └── native.py                  # Native expression passthrough (~51 lines)
│   │
│   ├── protocols/                      # PROTOCOL DEFINITIONS (~1,081 lines)
│   │   ├── __init__.py                # Export all protocols
│   │   ├── arithmetic_protocols.py    # 3 protocols + ENUM_ARITHMETIC_OPERATORS
│   │   ├── boolean_protocols.py       # 3 protocols + ENUM_BOOLEAN_OPERATORS (~153 lines)
│   │   ├── core_protocols.py          # 3 protocols + ENUM_CORE_OPERATORS
│   │   ├── horizontal_protocols.py    # 3 protocols + ENUM_HORIZONTAL_OPERATORS
│   │   ├── name_protocols.py          # 3 protocols + ENUM_NAME_OPERATORS
│   │   ├── native_protocols.py        # 3 protocols + ENUM_NATIVE_OPERATORS
│   │   ├── null_protocols.py          # 3 protocols + ENUM_NULL_OPERATORS
│   │   ├── string_protocols.py        # 3 protocols + ENUM_STRING_OPERATORS (~171 lines)
│   │   ├── temporal_protocols.py      # 3 protocols + ENUM_TEMPORAL_OPERATORS (~210 lines)
│   │   ├── type_protocols.py          # 3 protocols + ENUM_TYPE_OPERATORS
│   │   └── conditional_protocols.py   # Conditional protocols
│   │
│   ├── expression_nodes/              # AST NODES (~1,241 lines)
│   │   ├── __init__.py                # Export all nodes (~160 lines)
│   │   ├── base_expression_node.py   # Base node class
│   │   ├── types.py                  # Type aliases (~111 lines)
│   │   ├── arithmetic_expression_nodes.py
│   │   ├── boolean_expression_nodes.py    # (~156 lines)
│   │   ├── conditional_expression_nodes.py
│   │   ├── core_expression_nodes.py       # ColumnExpressionNode, LiteralExpressionNode
│   │   ├── horizontal_expression_nodes.py # Coalesce, greatest, least
│   │   ├── name_expression_nodes.py
│   │   ├── native_expression_nodes.py
│   │   ├── null_expression_nodes.py
│   │   ├── string_expression_nodes.py     # (~172 lines)
│   │   ├── temporal_expression_nodes.py
│   │   └── type_expression_nodes.py
│   │
│   ├── expression_visitors/          # STANDALONE VISITORS (~1,862 lines)
│   │   ├── __init__.py
│   │   ├── expression_visitor.py    # Abstract base (~43 lines)
│   │   ├── visitor_factory.py       # Backend detection & dispatch (~499 lines)
│   │   ├── types.py                 # Type aliases
│   │   ├── arithmetic_visitor.py    # (~130 lines)
│   │   ├── boolean_visitor.py       # (~286 lines)
│   │   ├── conditional_visitor.py   # (~62 lines)
│   │   ├── core_visitor.py          # col(), lit() (~58 lines)
│   │   ├── horizontal_visitor.py    # (~77 lines)
│   │   ├── name_visitor.py          # (~83 lines)
│   │   ├── native_visitor.py        # (~51 lines)
│   │   ├── null_visitor.py          # (~83 lines)
│   │   ├── string_visitor.py        # (~163 lines)
│   │   ├── temporal_visitor.py      # (~228 lines)
│   │   └── type_visitor.py          # (~48 lines)
│   │
│   ├── expression_system/            # BACKEND ABSTRACTION INTERFACE
│   │   ├── __init__.py
│   │   └── base.py                  # ExpressionSystem protocol composition
│   │
│   ├── expression_parameters/        # PARAMETER RESOLUTION
│   │   ├── __init__.py
│   │   └── expression_parameter.py  # ExpressionParameter abstraction
│   │
│   └── utils/
│       ├── __init__.py
│       └── temporal.py              # Temporal parsing utilities
│
└── backends/                          # BACKEND IMPLEMENTATIONS
    ├── __init__.py
    └── expression_systems/
        ├── polars/                   # Polars backend (~1,423 lines total)
        │   ├── __init__.py          # PolarsExpressionSystem composition (~61 lines)
        │   ├── base.py              # PolarsBaseExpressionSystem (~34 lines)
        │   ├── arithmetic.py        # (~123 lines)
        │   ├── boolean.py           # (~315 lines)
        │   ├── conditional.py       # (~32 lines)
        │   ├── core.py              # col(), lit() (~47 lines)
        │   ├── horizontal.py        # (~57 lines)
        │   ├── name.py              # (~74 lines)
        │   ├── native.py            # (~33 lines)
        │   ├── null.py              # (~78 lines)
        │   ├── string.py            # (~215 lines)
        │   ├── temporal.py          # (~321 lines)
        │   └── type.py              # (~33 lines)
        │
        ├── ibis/                     # Ibis backend (~984 lines total)
        │   ├── __init__.py          # IbisExpressionSystem composition (~50 lines)
        │   ├── base.py              # (~37 lines)
        │   ├── arithmetic.py        # (~36 lines)
        │   ├── boolean.py           # (~111 lines)
        │   ├── conditional.py       # (~32 lines)
        │   ├── core.py              # (~20 lines)
        │   ├── horizontal.py        # (~62 lines)
        │   ├── name.py              # (~116 lines)
        │   ├── native.py            # (~33 lines)
        │   ├── null.py              # (~31 lines)
        │   ├── string.py            # (~91 lines)
        │   ├── temporal.py          # (~352 lines)
        │   └── type.py              # (~13 lines)
        │
        └── narwhals/                 # Narwhals backend (~991 lines total)
            ├── __init__.py          # NarwhalsExpressionSystem composition (~50 lines)
            ├── base.py              # (~37 lines)
            ├── arithmetic.py        # (~66 lines)
            ├── boolean.py           # (~160 lines)
            ├── conditional.py       # (~32 lines)
            ├── core.py              # (~45 lines)
            ├── horizontal.py        # (~59 lines)
            ├── name.py              # (~86 lines)
            ├── native.py            # (~33 lines)
            ├── null.py              # (~31 lines)
            ├── string.py            # (~123 lines)
            ├── temporal.py          # (~254 lines)
            └── type.py              # (~15 lines)
```

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
│   └── test_temporal_natural.py        # Natural language time (~411 lines)
│
├── unit/
│   ├── test_namespace_infrastructure.py # (~582 lines)
│   └── test_protocol_alignment.py      # Protocol-implementation alignment (~711 lines)
├── integration/
└── backends/
```

**Total Test Lines: ~7,521**

## Core Architecture: Three-Layer Protocol Design

### The Three Protocol Layers

**IMPORTANT**: Every operation category defines **THREE** protocol interfaces:

1. **VisitorProtocol** - Defines visitor methods that traverse AST nodes
2. **ExpressionProtocol** - Defines backend primitive operations
3. **BuilderProtocol** - Defines fluent user-facing API methods (implemented by Namespaces)

### Protocol Categories

| Category | Protocols | Enum | Operations |
|----------|-----------|------|------------|
| **Core** | CoreVisitor, CoreExpression, CoreBuilder | ENUM_CORE_OPERATORS | col, lit |
| **Boolean** | BooleanVisitor, BooleanExpression, BooleanBuilder | ENUM_BOOLEAN_OPERATORS | eq, ne, gt, lt, ge, le, and_, or_, not_, is_in, etc. |
| **Arithmetic** | ArithmeticVisitor, ArithmeticExpression, ArithmeticBuilder | ENUM_ARITHMETIC_OPERATORS | add, subtract, multiply, divide, modulo, power, floor_divide |
| **String** | StringVisitor, StringExpression, StringBuilder | ENUM_STRING_OPERATORS | upper, lower, trim, contains, startswith, etc. |
| **Temporal** | TemporalVisitor, TemporalExpression, TemporalBuilder | ENUM_TEMPORAL_OPERATORS | year, month, day, add_days, diff_hours, etc. |
| **Horizontal** | HorizontalVisitor, HorizontalExpression, HorizontalBuilder | ENUM_HORIZONTAL_OPERATORS | coalesce, greatest, least |
| **Null** | NullVisitor, NullExpression, NullBuilder | ENUM_NULL_OPERATORS | is_null, is_not_null, fill_null |
| **Type** | TypeVisitor, TypeExpression, TypeBuilder | ENUM_TYPE_OPERATORS | cast |
| **Name** | NameVisitor, NameExpression, NameBuilder | ENUM_NAME_OPERATORS | alias, prefix, suffix |
| **Native** | NativeVisitor, NativeExpression, NativeBuilder | ENUM_NATIVE_OPERATORS | native (passthrough) |
| **Conditional** | - | - | when/then/otherwise |

### The Architecture Flow

```python
# 1. User builds expression (backend-agnostic AST)
User API: ma.col("age").gt(30)
    ↓
BooleanExpressionAPI (fluent interface) - dispatches to Namespaces
    ↓
BooleanNamespace.gt() - creates ExpressionNode
    ↓
BooleanComparisonExpressionNode (AST node)

# 2. Compile to backend-native expression
BooleanExpressionAPI.compile(df)
    ↓
ExpressionVisitorFactory.get_visitor_for_node() - selects visitor
    ↓
BooleanExpressionVisitor.visit_expression_node() - dispatches by operator
    ↓
ExpressionParameter.to_native_expression() - resolves operands
    ↓
Backend (e.g., PolarsExpressionSystem.gt()) - implements ExpressionProtocol
    ↓
Backend-native expression (pl.Expr | nw.Expr | ir.Expr)

# 3. Execute on DataFrame
df.filter(backend_expr) → Filtered DataFrame
```

### Key Components

#### 1. BooleanExpressionAPI (Main User Interface)

Located: `core/expression_api/boolean.py`

The main user-facing class that provides fluent expression building:

```python
class BooleanExpressionAPI(BaseExpressionAPI):
    """Expression API with standard two-valued boolean logic."""

    # Flat namespaces - methods accessed directly
    _FLAT_NAMESPACES = (
        BooleanComparisonNamespace,
        BooleanLogicalNamespace,
        ArithmeticNamespace,
        NullNamespace,
        TypeNamespace,
        HorizontalNamespace,
        NativeNamespace,
    )

    # Explicit namespace descriptors - accessed via .str, .dt, .name
    str = NamespaceDescriptor(StringNamespace)
    dt = NamespaceDescriptor(DateTimeNamespace)
    name = NamespaceDescriptor(NameNamespace)

    # Python operator overloading
    def __gt__(self, other): return self.gt(other)
    def __and__(self, other): return self.and_(other)
    def __add__(self, other): return self.add(other)
    # ... etc.
```

#### 2. Namespace-Based API

Located: `core/namespaces/`

Operations are organized into namespaces that implement BuilderProtocols:

```python
# core/namespaces/boolean.py
class BooleanNamespace(BaseNamespace, BooleanBuilderProtocol):
    """Boolean operations namespace."""

    def eq(self, other) -> BaseExpressionAPI:
        """Equal to (==)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.EQ,
            self._node,
            other_node,
        )
        return self._build(node)

    def and_(self, *others) -> BaseExpressionAPI:
        """Logical AND operation."""
        operands = [self._node] + [self._to_node_or_value(o) for o in others]
        node = BooleanIterableExpressionNode(
            ENUM_BOOLEAN_OPERATORS.AND,
            *operands,
        )
        return self._build(node)
```

#### 3. Entry Point Functions

Located: `core/namespaces/entrypoints.py`

```python
def col(name: str) -> BaseExpressionAPI:
    """Create a column reference expression."""
    node = ColumnExpressionNode(operator=ENUM_CORE_OPERATORS.COL, column=name)
    return BooleanExpressionAPI(node)

def lit(value: Any) -> BaseExpressionAPI:
    """Create a literal value expression."""
    node = LiteralExpressionNode(operator=ENUM_CORE_OPERATORS.LIT, value=value)
    return BooleanExpressionAPI(node)

def coalesce(*exprs) -> BaseExpressionAPI:
    """Return the first non-null value from multiple expressions."""
    ...

def when(condition) -> WhenBuilder:
    """Start a conditional when-then-otherwise expression."""
    ...

def native(expr: Any) -> BaseExpressionAPI:
    """Wrap a backend-native expression in the abstract expression API."""
    ...
```

#### 4. Visitor Factory

Located: `core/expression_visitors/visitor_factory.py`

Auto-detects backend and dispatches to appropriate visitor:

```python
class ExpressionVisitorFactory:
    _expression_systems_registry: Dict[CONST_VISITOR_BACKENDS, Type[ExpressionSystem]] = {}

    @classmethod
    def get_visitor_for_node(cls, node, expression_system, logic_type):
        """Get appropriate visitor for a specific node type."""
        if isinstance(node, (BooleanComparisonExpressionNode, ...)):
            return BooleanExpressionVisitor(expression_system)
        elif isinstance(node, (ArithmeticExpressionNode, ...)):
            return ArithmeticExpressionVisitor(expression_system)
        # ... etc.

    @classmethod
    def _identify_backend(cls, dataframe_or_backend):
        """Identify the backend from a DataFrame/Table object."""
        # Priority: 1. Narwhals, 2. Ibis, 3. Polars, 4. Pandas
        ...
```

#### 5. Backend ExpressionSystems

Located: `backends/expression_systems/*/`

Each backend composes protocol implementations:

```python
# backends/expression_systems/polars/__init__.py
@register_expression_system(CONST_VISITOR_BACKENDS.POLARS)
class PolarsExpressionSystem(
    PolarsCoreExpressionSystem,
    PolarsBooleanExpressionSystem,
    PolarsArithmeticExpressionSystem,
    PolarsStringExpressionSystem,
    PolarsTemporalExpressionSystem,
    PolarsTypeExpressionSystem,
    PolarsNullExpressionSystem,
    PolarsHorizontalExpressionSystem,
    PolarsNameExpressionSystem,
    PolarsNativeExpressionSystem,
    PolarsConditionalExpressionSystem,
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

### Adding a New Operation

1. **Add to protocol enum:**
   ```python
   # core/protocols/boolean_protocols.py
   class ENUM_BOOLEAN_OPERATORS(Enum):
       NEW_OP = auto()
   ```

2. **Add to VisitorProtocol:**
   ```python
   class BooleanVisitorProtocol(Protocol):
       def new_op(self, node: BooleanSomeNode) -> SupportedExpressions: ...
   ```

3. **Add to ExpressionProtocol:**
   ```python
   class BooleanExpressionProtocol(Protocol):
       def new_op(self, left, right) -> SupportedExpressions: ...
   ```

4. **Add to BuilderProtocol:**
   ```python
   class BooleanBuilderProtocol(Protocol):
       def new_op(self, other) -> BaseNamespace: ...
   ```

5. **Create expression node (if needed):**
   ```python
   # core/expression_nodes/boolean_expression_nodes.py
   class BooleanNewOpNode(BooleanExpressionNode):
       ...
   ```

6. **Implement in namespace:**
   ```python
   # core/namespaces/boolean.py
   def new_op(self, other) -> BaseExpressionAPI:
       node = BooleanNewOpNode(ENUM_BOOLEAN_OPERATORS.NEW_OP, ...)
       return self._build(node)
   ```

7. **Implement in visitor:**
   ```python
   # core/expression_visitors/boolean_visitor.py
   def new_op(self, node: BooleanNewOpNode) -> SupportedExpressions:
       left_expr = ExpressionParameter(node.left, ...).to_native_expression()
       right_expr = ExpressionParameter(node.right, ...).to_native_expression()
       return self.backend.new_op(left_expr, right_expr)
   ```

8. **Implement in all backends:**
   ```python
   # backends/expression_systems/polars/boolean.py
   def new_op(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
       return left.some_polars_method(right)
   ```

9. **Add tests:**
   ```python
   # tests/cross_backend/test_boolean.py
   @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
   def test_new_op(backend_name, ...):
       ...
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

## Line Count Summary

| Component | Lines | Status |
|-----------|-------|--------|
| **Protocols** | ~1,081 | ✅ Complete |
| **Expression Nodes** | ~1,241 | ✅ Complete |
| **Visitors** | ~1,862 | ✅ Complete |
| **Namespaces** | ~2,832 | ✅ Complete |
| **Backend: Polars** | ~1,423 | ✅ Complete |
| **Backend: Ibis** | ~984 | ✅ Complete |
| **Backend: Narwhals** | ~991 | ✅ Complete |
| **Tests** | ~7,521 | ✅ Comprehensive |
| **TOTAL** | ~18,000+ | ✅ Production ready |

## Quick Reference

### Import Paths

```python
# Public API (recommended)
import mountainash_expressions as ma
from mountainash_expressions import col, lit, coalesce, greatest, least, when, native

# Expression API classes
from mountainash_expressions import BooleanExpressionAPI, BaseExpressionAPI

# Constants
from mountainash_expressions import CONST_VISITOR_BACKENDS, CONST_LOGIC_TYPES

# Advanced: Visitor factory
from mountainash_expressions.core.expression_visitors import ExpressionVisitorFactory

# Advanced: Protocols (for type hints)
from mountainash_expressions.core.protocols import (
    BooleanVisitorProtocol,
    BooleanExpressionProtocol,
    BooleanBuilderProtocol,
)

# Advanced: Nodes (for AST manipulation)
from mountainash_expressions.core.expression_nodes import (
    ExpressionNode,
    BooleanComparisonExpressionNode,
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
```

## Future Work

### Planned

- **Ternary Logic**: NULL-safe three-valued logic (designed, not implemented)
- **Pandas Backend**: Full implementation and testing
- **PyArrow Backend**: Implementation

### Potential Enhancements

- Window functions
- Aggregation expressions
- User-defined functions
- Expression optimization
- Query planning
