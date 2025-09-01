# Narwhals Migration Guide for MountainAsh Expressions

## Overview

This guide outlines how to adapt MountainAsh Expressions to use [Narwhals](https://github.com/narwhals-dev/narwhals) for multi-backend support while maintaining the library's ternary logic capabilities. Narwhals provides a lightweight compatibility layer between dataframe libraries (pandas, Polars, PyArrow, cuDF, Modin, Dask, etc.) with zero dependencies.

## Architecture Strategy

### Core Principles

1. **Use Narwhals for binary operations** - Leverage narwhals' existing boolean logic support
2. **Implement ternary logic externally** - Build ternary operations as an extension layer
3. **Maintain backend independence** - Work with any dataframe library narwhals supports
4. **Preserve existing visitor pattern** - Adapt rather than replace current architecture

## Implementation Approach

### 1. Binary Operations with Narwhals

Replace backend-specific binary operations with narwhals expressions:

```python
# mountainash_expressions/core/binary_expr.py
import narwhals as nw
from typing import Any

class BinaryExpression:
    """Wrapper around narwhals expressions for binary logic."""
    
    def __init__(self, expr: nw.Expr):
        self._expr = expr
    
    def and_(self, other: 'BinaryExpression') -> 'BinaryExpression':
        return BinaryExpression(self._expr & other._expr)
    
    def or_(self, other: 'BinaryExpression') -> 'BinaryExpression':
        return BinaryExpression(self._expr | other._expr)
    
    def not_(self) -> 'BinaryExpression':
        return BinaryExpression(~self._expr)
    
    def xor(self, other: 'BinaryExpression') -> 'BinaryExpression':
        # XOR = (A & ~B) | (~A & B)
        return BinaryExpression(
            (self._expr & ~other._expr) | (~self._expr & other._expr)
        )
    
    def to_narwhals(self) -> nw.Expr:
        """Get the underlying narwhals expression."""
        return self._expr
```

### 2. Ternary Logic Extension Layer

Build ternary logic on top of narwhals using integer encoding:
- `FALSE = 0`
- `UNKNOWN = 1` (NULL)
- `TRUE = 2`

```python
# mountainash_expressions/ternary/ternary_expr.py
import narwhals as nw
from typing import Any, Optional, Literal

class TernaryExpression:
    """
    Ternary logic expression built on top of narwhals.
    Uses integer encoding: FALSE=0, UNKNOWN=1, TRUE=2
    """
    
    def __init__(self, expr: nw.Expr, is_ternary: bool = False):
        self._expr = expr
        self._is_ternary = is_ternary
    
    @classmethod
    def from_binary(cls, expr: nw.Expr) -> 'TernaryExpression':
        """Convert binary expression to ternary (NULL becomes UNKNOWN)."""
        # Map: False->0, True->2, NULL->1
        ternary_expr = (
            nw.when(expr.is_null()).then(1)
            .when(expr == False).then(0)
            .when(expr == True).then(2)
            .otherwise(1)  # Safety fallback
        )
        return cls(ternary_expr, is_ternary=True)
    
    @classmethod
    def from_column(cls, col_name: str) -> 'TernaryExpression':
        """Create ternary expression from column name."""
        expr = nw.col(col_name)
        return cls.from_binary(expr)
    
    def and_(self, other: Any) -> 'TernaryExpression':
        """Ternary AND: minimum value (Kleene logic)."""
        other = self._ensure_ternary(other)
        result = nw.when(self._expr < other._expr).then(self._expr).otherwise(other._expr)
        return TernaryExpression(result, is_ternary=True)
    
    def or_(self, other: Any) -> 'TernaryExpression':
        """Ternary OR: maximum value (Kleene logic)."""
        other = self._ensure_ternary(other)
        result = nw.when(self._expr > other._expr).then(self._expr).otherwise(other._expr)
        return TernaryExpression(result, is_ternary=True)
    
    def not_(self) -> 'TernaryExpression':
        """Ternary NOT: 0->2, 2->0, 1->1."""
        result = (
            nw.when(self._expr == 0).then(2)
            .when(self._expr == 2).then(0)
            .otherwise(1)  # UNKNOWN stays UNKNOWN
        )
        return TernaryExpression(result, is_ternary=True)
    
    def is_true(self) -> nw.Expr:
        """Check if value is TRUE."""
        return self._expr == 2
    
    def is_false(self) -> nw.Expr:
        """Check if value is FALSE."""
        return self._expr == 0
    
    def is_unknown(self) -> nw.Expr:
        """Check if value is UNKNOWN."""
        return self._expr == 1
    
    def maybe_true(self) -> nw.Expr:
        """Check if value is TRUE or UNKNOWN."""
        return self._expr >= 1
    
    def maybe_false(self) -> nw.Expr:
        """Check if value is FALSE or UNKNOWN."""
        return self._expr <= 1
    
    def to_boolean(self) -> nw.Expr:
        """Convert back to boolean (UNKNOWN becomes NULL)."""
        return (
            nw.when(self._expr == 0).then(False)
            .when(self._expr == 2).then(True)
            .otherwise(None)
        )
```

### 3. Visitor Pattern Adapter

Bridge your existing visitor pattern with narwhals:

```python
# mountainash_expressions/adapters/visitor_adapter.py
import narwhals as nw
from typing import Any

class NarwhalsVisitorAdapter:
    """
    Adapter to use narwhals expressions with your existing visitor pattern.
    """
    
    def __init__(self, df: Any):
        """Initialize with a dataframe (pandas, polars, etc)."""
        self.nw_df = nw.from_native(df)
        self.native_namespace = nw.get_native_namespace(df)
    
    def visit_logical_expression(self, expr_node) -> nw.Expr:
        """Convert LogicalExpressionNode to narwhals Expr."""
        if expr_node.operation == "AND":
            left = self.visit_logical_expression(expr_node.operands[0])
            right = self.visit_logical_expression(expr_node.operands[1])
            return left & right
        elif expr_node.operation == "OR":
            left = self.visit_logical_expression(expr_node.operands[0])
            right = self.visit_logical_expression(expr_node.operands[1])
            return left | right
        elif expr_node.operation == "NOT":
            operand = self.visit_logical_expression(expr_node.operands[0])
            return ~operand
        elif expr_node.operation == "XOR":
            left = self.visit_logical_expression(expr_node.operands[0])
            right = self.visit_logical_expression(expr_node.operands[1])
            return (left & ~right) | (~left & right)
        # Add more operations as needed
    
    def execute(self, expr_node) -> Any:
        """Execute expression and return native result."""
        nw_expr = self.visit_logical_expression(expr_node)
        result = self.nw_df.select(nw_expr)
        return nw.to_native(result)
```

### 4. Unified Expression Builder

Create a unified interface for both logic types:

```python
# mountainash_expressions/builder.py
import narwhals as nw
from typing import Union, Literal, List
from .core.binary_expr import BinaryExpression
from .ternary.ternary_expr import TernaryExpression

LogicType = Literal["binary", "ternary"]

class ExpressionBuilder:
    """
    Unified builder for binary and ternary expressions using narwhals.
    """
    
    def __init__(self, logic_type: LogicType = "binary"):
        self.logic_type = logic_type
    
    def col(self, name: str) -> Union[BinaryExpression, TernaryExpression]:
        """Create a column expression."""
        if self.logic_type == "binary":
            return BinaryExpression(nw.col(name))
        else:
            return TernaryExpression.from_column(name)
    
    def lit(self, value: Any) -> Union[BinaryExpression, TernaryExpression]:
        """Create a literal expression."""
        if self.logic_type == "binary":
            return BinaryExpression(nw.lit(value))
        else:
            if value is None:
                return TernaryExpression(nw.lit(1), is_ternary=True)
            elif value is True:
                return TernaryExpression(nw.lit(2), is_ternary=True)
            elif value is False:
                return TernaryExpression(nw.lit(0), is_ternary=True)
            else:
                raise ValueError(f"Invalid ternary literal: {value}")
    
    @staticmethod
    def and_(*exprs) -> Union[BinaryExpression, TernaryExpression]:
        """N-ary AND operation."""
        if not exprs:
            raise ValueError("Need at least one expression")
        
        result = exprs[0]
        for expr in exprs[1:]:
            result = result.and_(expr)
        return result
    
    @staticmethod
    def or_(*exprs) -> Union[BinaryExpression, TernaryExpression]:
        """N-ary OR operation."""
        if not exprs:
            raise ValueError("Need at least one expression")
        
        result = exprs[0]
        for expr in exprs[1:]:
            result = result.or_(expr)
        return result
```

## Usage Examples

### Basic Binary Logic

```python
import narwhals as nw
import pandas as pd
from mountainash_expressions import BinaryExpression

# Works with any backend
df = pd.DataFrame({
    'a': [True, False, True, False],
    'b': [True, True, False, False]
})

nw_df = nw.from_native(df)

# Direct narwhals usage for binary logic
result = nw_df.select(
    (nw.col('a') & nw.col('b')).alias('and'),
    (nw.col('a') | nw.col('b')).alias('or'),
    (~nw.col('a')).alias('not_a')
)
```

### Ternary Logic Operations

```python
import pandas as pd
import narwhals as nw
from mountainash_expressions import TernaryExpression

# DataFrame with NULL values
df = pd.DataFrame({
    'a': [True, False, None, True],
    'b': [False, None, True, True],
})

nw_df = nw.from_native(df)

# Create ternary expressions
ternary_a = TernaryExpression.from_column('a')
ternary_b = TernaryExpression.from_column('b')

# Perform ternary operations
result = nw_df.select(
    ternary_a.and_(ternary_b).to_boolean().alias('ternary_and'),
    ternary_a.or_(ternary_b).to_boolean().alias('ternary_or'),
    ternary_a.not_().to_boolean().alias('ternary_not'),
    ternary_a.is_unknown().alias('a_is_unknown'),
    ternary_a.maybe_true().alias('a_maybe_true'),
)

# Convert back to native format
native_result = nw.to_native(result)
```

### XOR Operations

```python
# Binary XOR
binary_xor = BinaryExpression(nw.col('a')).xor(BinaryExpression(nw.col('b')))

# Ternary XOR (exclusive - exactly one TRUE)
ternary_xor = ternary_a.xor(ternary_b, exclusive=True)

result = nw_df.select(
    binary_xor.to_narwhals().alias('binary_xor'),
    ternary_xor.to_boolean().alias('ternary_xor')
)
```

## Testing Strategy

### Multi-Backend Testing

```python
# tests/test_ternary_with_backends.py
import pytest
import narwhals as nw
from mountainash_expressions import TernaryExpression

@pytest.mark.parametrize("constructor", [
    "pandas",
    "polars", 
    "pyarrow",
    "modin",
    "dask",
])
def test_ternary_logic_across_backends(constructor):
    """Test ternary operations work with all backends."""
    df = create_test_dataframe(constructor)
    nw_df = nw.from_native(df)
    
    ternary_a = TernaryExpression.from_column('a')
    ternary_b = TernaryExpression.from_column('b')
    
    # Test AND operation
    and_result = nw_df.select(
        ternary_a.and_(ternary_b).to_boolean().alias('result')
    )
    
    # Test OR operation
    or_result = nw_df.select(
        ternary_a.or_(ternary_b).to_boolean().alias('result')
    )
    
    # Verify results match expected ternary logic
    assert_ternary_logic_correct(nw.to_native(and_result), 'and')
    assert_ternary_logic_correct(nw.to_native(or_result), 'or')
```

## Migration Checklist

- [ ] **Phase 1: Setup**
  - [ ] Add narwhals as a dependency
  - [ ] Create adapter module structure
  - [ ] Set up multi-backend testing infrastructure

- [ ] **Phase 2: Binary Logic Migration**
  - [ ] Implement BinaryExpression wrapper
  - [ ] Replace backend-specific binary operations with narwhals
  - [ ] Test binary operations across all backends

- [ ] **Phase 3: Ternary Logic Implementation**
  - [ ] Implement TernaryExpression class
  - [ ] Add ternary operation methods (and_, or_, not_, xor)
  - [ ] Implement state checking methods (is_true, is_unknown, etc.)
  - [ ] Add conversion methods (to_boolean, from_binary)

- [ ] **Phase 4: Visitor Pattern Integration**
  - [ ] Create NarwhalsVisitorAdapter
  - [ ] Map existing visitor operations to narwhals expressions
  - [ ] Test visitor pattern with narwhals backend

- [ ] **Phase 5: Testing & Documentation**
  - [ ] Create comprehensive test suite for all backends
  - [ ] Write performance benchmarks
  - [ ] Update documentation with narwhals examples
  - [ ] Add migration guide for existing users

## Benefits of This Approach

1. **Multi-backend support**: Automatically works with pandas, Polars, PyArrow, cuDF, Modin, Dask, and more
2. **Zero dependencies**: Narwhals has no dependencies, keeping your library lightweight
3. **Performance**: Leverages each backend's optimized operations
4. **Gradual migration**: Can migrate incrementally without breaking existing code
5. **Clean separation**: Binary logic uses narwhals directly, ternary logic is your value-add
6. **Future-proof**: As narwhals adds more backends, your library automatically supports them

## Potential Future Enhancements

### Contributing Ternary Logic to Narwhals

Once your ternary implementation is stable, consider proposing it as a narwhals extension:

```python
# Potential narwhals API
expr = nw.col('a').ternary.and_(nw.col('b'))
expr = nw.col('a').ternary.or_(nw.col('b'))
expr = nw.col('a').ternary.not_()
```

### Performance Optimizations

- Implement backend-specific optimizations where needed
- Use native ternary operations if backend supports them (e.g., SQL databases)
- Cache ternary conversions for repeated operations

## Resources

- [Narwhals Documentation](https://narwhals-dev.github.io/narwhals/)
- [Narwhals GitHub](https://github.com/narwhals-dev/narwhals)
- [Three-valued Logic (Wikipedia)](https://en.wikipedia.org/wiki/Three-valued_logic)
- [Kleene Logic](https://en.wikipedia.org/wiki/Three-valued_logic#Kleene_and_Priest_logics)