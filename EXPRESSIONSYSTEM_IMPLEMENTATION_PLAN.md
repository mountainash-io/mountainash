# ExpressionSystem Implementation Plan

## Overview
Refactor from current visitor-centric architecture to documented ExpressionSystem pattern, where:
- **ExpressionSystem** = Concrete backend primitives (public methods)
- **Visitor** = Logic-aware dispatcher that uses ExpressionSystem

## Phase 1: Create NarwhalsExpressionSystem (Backend Primitives)

### Step 1.1: Create ExpressionSystem Base Class
**File**: `src/mountainash_expressions/core/expression_system/base.py`

```python
from abc import ABC, abstractmethod
from typing import Any, List

class ExpressionSystem(ABC):
    """Base class for backend expression systems.

    Each backend (Narwhals, Polars, Ibis) implements this to provide
    native expression primitives.
    """

    # Backend identification
    @abstractmethod
    def get_backend_id(self) -> str:
        """Return unique backend identifier (e.g., 'narwhals', 'polars')"""
        pass

    @abstractmethod
    def get_native_type(self) -> type:
        """Return native expression type (e.g., nw.Expr, pl.Expr)"""
        pass

    @abstractmethod
    def is_native_expression(self, obj: Any) -> bool:
        """Check if object is a native backend expression"""
        pass

    # Basic expression creation
    @abstractmethod
    def col(self, name: str) -> Any:
        """Create column reference"""
        pass

    @abstractmethod
    def lit(self, value: Any) -> Any:
        """Create literal value"""
        pass

    # Comparison operations (backend-agnostic - work for Boolean & Ternary)
    @abstractmethod
    def eq(self, left: Any, right: Any) -> Any:
        """Equality comparison"""
        pass

    @abstractmethod
    def ne(self, left: Any, right: Any) -> Any:
        """Not equal comparison"""
        pass

    @abstractmethod
    def gt(self, left: Any, right: Any) -> Any:
        """Greater than comparison"""
        pass

    @abstractmethod
    def lt(self, left: Any, right: Any) -> Any:
        """Less than comparison"""
        pass

    @abstractmethod
    def ge(self, left: Any, right: Any) -> Any:
        """Greater than or equal comparison"""
        pass

    @abstractmethod
    def le(self, left: Any, right: Any) -> Any:
        """Less than or equal comparison"""
        pass

    # Logical operations (Boolean semantics - NULLs treated as False)
    @abstractmethod
    def and_(self, left: Any, right: Any) -> Any:
        """Boolean AND"""
        pass

    @abstractmethod
    def or_(self, left: Any, right: Any) -> Any:
        """Boolean OR"""
        pass

    @abstractmethod
    def not_(self, expr: Any) -> Any:
        """Boolean NOT"""
        pass

    # Collection operations
    @abstractmethod
    def is_in(self, expr: Any, values: List[Any]) -> Any:
        """Check if expression value is in list"""
        pass

    # Null handling
    @abstractmethod
    def is_null(self, expr: Any) -> Any:
        """Check if expression is NULL"""
        pass

    @abstractmethod
    def is_not_null(self, expr: Any) -> Any:
        """Check if expression is not NULL"""
        pass

    # Type casting
    @abstractmethod
    def cast(self, expr: Any, target_type: Any, **kwargs) -> Any:
        """Cast expression to target type"""
        pass
```

### Step 1.2: Create NarwhalsExpressionSystem
**File**: `src/mountainash_expressions/backends/narwhals/narwhals_expression_system.py`

```python
import narwhals as nw
from typing import Any, List
from ...core.expression_system.base import ExpressionSystem

class NarwhalsExpressionSystem(ExpressionSystem):
    """Concrete expression system for Narwhals backend.

    Provides all backend-specific primitives using Narwhals API.
    """

    def get_backend_id(self) -> str:
        return "narwhals"

    def get_native_type(self) -> type:
        return nw.Expr

    def is_native_expression(self, obj: Any) -> bool:
        return isinstance(obj, nw.Expr)

    # Basic expression creation
    def col(self, name: str) -> nw.Expr:
        """Create Narwhals column reference"""
        return nw.col(name)

    def lit(self, value: Any) -> nw.Expr:
        """Create Narwhals literal value"""
        return nw.lit(value)

    # Comparison operations
    def eq(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        return left == right

    def ne(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        return left != right

    def gt(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        return left > right

    def lt(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        return left < right

    def ge(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        return left >= right

    def le(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        return left <= right

    # Logical operations
    def and_(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        return left & right

    def or_(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        return left | right

    def not_(self, expr: nw.Expr) -> nw.Expr:
        return ~expr

    # Collection operations
    def is_in(self, expr: nw.Expr, values: List[Any]) -> nw.Expr:
        return expr.is_in(list(values))

    # Null handling
    def is_null(self, expr: nw.Expr) -> nw.Expr:
        return expr.is_null()

    def is_not_null(self, expr: nw.Expr) -> nw.Expr:
        return ~expr.is_null()

    # Type casting
    def cast(self, expr: nw.Expr, target_type: Any, **kwargs) -> nw.Expr:
        return expr.cast(target_type, **kwargs)
```

**Test**: Create simple test to verify ExpressionSystem works
```python
def test_narwhals_expression_system():
    system = NarwhalsExpressionSystem()

    # Test primitives
    col_expr = system.col("age")
    assert isinstance(col_expr, nw.Expr)

    lit_expr = system.lit(25)
    assert isinstance(lit_expr, nw.Expr)

    # Test operations
    eq_expr = system.eq(col_expr, lit_expr)
    assert isinstance(eq_expr, nw.Expr)

    # Test on dataframe
    df = pl.DataFrame({'age': [25, 30, 35]})
    nw_df = nw.from_native(df)
    result = nw_df.filter(eq_expr)
    assert result.shape[0] == 1
```

---

## Phase 2: Refactor BooleanExpressionVisitor to Use ExpressionSystem

### Step 2.1: Update Visitor to Accept ExpressionSystem
**File**: `src/mountainash_expressions/core/expression_visitors/boolean_expression_visitor.py`

```python
from typing import Any, List
from ..expression_system.base import ExpressionSystem
from ..expression_nodes import ExpressionNode

class BooleanExpressionVisitor:
    """Boolean logic visitor that uses ExpressionSystem.

    This visitor handles Boolean logic semantics (NULLs treated as False)
    and works with ANY backend through the ExpressionSystem interface.
    """

    def __init__(self, expression_system: ExpressionSystem):
        self.backend = expression_system  # ← Key change: injected dependency

    # Helper: Process operands using backend
    def _process_operand(self, operand: Any) -> Any:
        """Convert any operand to native backend expression."""
        # Already native expression - pass through
        if self.backend.is_native_expression(operand):
            return operand

        # ExpressionNode - recursively visit
        if isinstance(operand, ExpressionNode):
            return operand.accept(self)

        # String - column reference
        if isinstance(operand, str):
            return self.backend.col(operand)  # ← Uses backend!

        # Other - literal value
        return self.backend.lit(operand)  # ← Uses backend!

    def _process_operands(self, operands: List[Any]) -> List[Any]:
        """Process multiple operands."""
        return [self._process_operand(op) for op in operands]

    # Comparison operations - use backend methods
    def visit_boolean_comparison_eq(self, node) -> Any:
        left = self._process_operand(node.left)
        right = self._process_operand(node.right)
        return self.backend.eq(left, right)  # ← Uses backend method!

    def visit_boolean_comparison_ne(self, node) -> Any:
        left = self._process_operand(node.left)
        right = self._process_operand(node.right)
        return self.backend.ne(left, right)

    def visit_boolean_comparison_gt(self, node) -> Any:
        left = self._process_operand(node.left)
        right = self._process_operand(node.right)
        return self.backend.gt(left, right)

    # ... similar for lt, ge, le

    # Logical operations - use backend methods with reduce
    def visit_boolean_logical_and(self, node) -> Any:
        operands = self._process_operands(node.operands)
        return reduce(lambda x, y: self.backend.and_(x, y), operands)

    def visit_boolean_logical_or(self, node) -> Any:
        operands = self._process_operands(node.operands)
        return reduce(lambda x, y: self.backend.or_(x, y), operands)

    def visit_boolean_logical_not(self, node) -> Any:
        operand = self._process_operand(node.operands[0])
        return self.backend.not_(operand)

    # Collection operations
    def visit_boolean_collection_in(self, node) -> Any:
        element = self._process_operand(node.element)
        # Container might be a list of values
        if isinstance(node.container, (list, tuple, set)):
            return self.backend.is_in(element, list(node.container))
        else:
            container = self._process_operand(node.container)
            return self.backend.is_in(element, container)
```

### Step 2.2: Update Visitor Factory
**File**: `src/mountainash_expressions/core/expression_visitors/visitor_factory.py`

Update to create visitors with ExpressionSystem:

```python
@classmethod
def get_visitor_for_backend(
    cls,
    backend: Any,
    logic_type: CONST_LOGIC_TYPES
) -> ExpressionVisitor:
    """Get visitor for backend and logic type."""
    backend_type = cls._identify_backend(backend)

    # Create ExpressionSystem for backend
    if backend_type == CONST_VISITOR_BACKENDS.NARWHALS:
        from ...backends.narwhals.narwhals_expression_system import NarwhalsExpressionSystem
        expression_system = NarwhalsExpressionSystem()
    elif backend_type == CONST_VISITOR_BACKENDS.POLARS:
        from ...backends.polars.polars_expression_system import PolarsExpressionSystem
        expression_system = PolarsExpressionSystem()
    # ... other backends

    # Create visitor with ExpressionSystem
    if logic_type == CONST_LOGIC_TYPES.BOOLEAN:
        from .boolean_expression_visitor import BooleanExpressionVisitor
        return BooleanExpressionVisitor(expression_system)
    elif logic_type == CONST_LOGIC_TYPES.TERNARY:
        from .ternary_expression_visitor import TernaryExpressionVisitor
        return TernaryExpressionVisitor(expression_system)
    # ... other logic types
```

**Test**: Verify visitor works with ExpressionSystem
```python
def test_boolean_visitor_with_expression_system():
    # Create expression system
    system = NarwhalsExpressionSystem()

    # Create visitor with system
    visitor = BooleanExpressionVisitor(system)

    # Create expression node
    node = BooleanComparisonEqNode(
        left=SourceExpressionNode("age"),
        right=LiteralExpressionNode(25)
    )

    # Visit to compile
    expr = node.accept(visitor)

    # Should return native expression
    assert isinstance(expr, nw.Expr)

    # Test on dataframe
    df = pl.DataFrame({'age': [25, 30, 35]})
    nw_df = nw.from_native(df)
    result = nw_df.filter(expr)
    assert result.shape[0] == 1
```

---

## Phase 3: Remove Old Backend-Specific Visitors

### Step 3.1: Deprecate Old Files
Mark these as deprecated (don't delete yet - for reference):
- `backends/narwhals/narwhals_boolean_visitor.py` → Move to `_backup/`
- `backends/narwhals/narwhals_visitor.py` → Move to `_backup/`

### Step 3.2: Update Imports
Update all imports to use new structure:
```python
# OLD
from mountainash_expressions.backends.narwhals.narwhals_boolean_visitor import NarwhalsBooleanExpressionVisitor

# NEW
from mountainash_expressions.core.expression_system.base import ExpressionSystem
from mountainash_expressions.backends.narwhals.narwhals_expression_system import NarwhalsExpressionSystem
from mountainash_expressions.core.expression_visitors.boolean_expression_visitor import BooleanExpressionVisitor
```

---

## Phase 4: Extend to Polars Backend

### Step 4.1: Create PolarsExpressionSystem
**File**: `src/mountainash_expressions/backends/polars/polars_expression_system.py`

```python
import polars as pl
from typing import Any, List
from ...core.expression_system.base import ExpressionSystem

class PolarsExpressionSystem(ExpressionSystem):
    """Concrete expression system for Polars backend."""

    def get_backend_id(self) -> str:
        return "polars"

    def get_native_type(self) -> type:
        return pl.Expr

    def is_native_expression(self, obj: Any) -> bool:
        return isinstance(obj, pl.Expr)

    def col(self, name: str) -> pl.Expr:
        return pl.col(name)

    def lit(self, value: Any) -> pl.Expr:
        return pl.lit(value)

    def eq(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        return left == right

    # ... all other methods (same as Narwhals but pl.* instead of nw.*)
```

### Step 4.2: Test Polars Backend
```python
def test_polars_expression_system():
    system = PolarsExpressionSystem()
    visitor = BooleanExpressionVisitor(system)

    # Same expression tree as Narwhals test
    node = BooleanComparisonEqNode(
        left=SourceExpressionNode("age"),
        right=LiteralExpressionNode(25)
    )

    expr = node.accept(visitor)
    assert isinstance(expr, pl.Expr)  # ← Polars expression!

    # Test on Polars dataframe (no Narwhals wrapper)
    df = pl.DataFrame({'age': [25, 30, 35]})
    result = df.filter(expr)
    assert result.shape[0] == 1
```

### Step 4.3: Verify Same Visitor Works for Both Backends
```python
def test_universal_visitor():
    """Test that ONE visitor works with MULTIPLE backends"""

    # Same expression tree
    node = BooleanComparisonEqNode(
        left=SourceExpressionNode("age"),
        right=LiteralExpressionNode(25)
    )

    # Narwhals backend
    narwhals_system = NarwhalsExpressionSystem()
    narwhals_visitor = BooleanExpressionVisitor(narwhals_system)
    narwhals_expr = node.accept(narwhals_visitor)

    # Polars backend
    polars_system = PolarsExpressionSystem()
    polars_visitor = BooleanExpressionVisitor(polars_system)
    polars_expr = node.accept(polars_visitor)

    # Same visitor code, different backends!
    assert isinstance(narwhals_expr, nw.Expr)
    assert isinstance(polars_expr, pl.Expr)
```

---

## Phase 5: Integration & Cleanup

### Step 5.1: Update Expression Nodes
Update expression nodes to use factory with new pattern:
```python
class BooleanComparisonEqNode:
    def eval(self):
        def eval_expr(backend: Any) -> Any:
            # Factory creates ExpressionSystem + Visitor
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(
                backend,
                CONST_LOGIC_TYPES.BOOLEAN
            )
            return self.accept(visitor)
        return eval_expr
```

### Step 5.2: Update Documentation
- Update ARCHITECTURE_MISMATCH_ANALYSIS.md to reflect new pattern
- Update REFACTORING_COMPLETE.md with ExpressionSystem pattern
- Add EXPRESSIONSYSTEM_ARCHITECTURE.md with diagrams

### Step 5.3: Full Test Suite
```bash
# Test Narwhals backend
hatch run test:test-target tests/backends/narwhals/

# Test Polars backend
hatch run test:test-target tests/backends/polars/

# Test visitor works with both
hatch run test:test-target tests/core/expression_visitors/
```

---

## Success Criteria

- [ ] NarwhalsExpressionSystem implements all ExpressionSystem methods
- [ ] BooleanExpressionVisitor uses ExpressionSystem (not direct backend calls)
- [ ] Visitor works with Narwhals backend
- [ ] PolarsExpressionSystem implemented
- [ ] Same BooleanExpressionVisitor works with Polars backend
- [ ] All existing tests pass
- [ ] No direct `nw.*` or `pl.*` calls in visitor code
- [ ] Factory pattern updated to create ExpressionSystem + Visitor
- [ ] Old backend-specific visitors deprecated/removed

---

## Benefits Achieved

1. **Backend Independence**: BooleanExpressionVisitor has ZERO backend-specific code
2. **Code Reuse**: ONE visitor implementation works with ALL backends
3. **Easy Extension**: Add new backend = implement ExpressionSystem (visitor unchanged)
4. **Clear Architecture**: Backend primitives vs logic dispatch clearly separated
5. **Testability**: Mock ExpressionSystem to test visitor logic in isolation
6. **Consistency**: Same logic semantics across all backends

---

## Timeline Estimate

- Phase 1 (ExpressionSystem base + Narwhals): **2-3 hours**
- Phase 2 (Refactor visitor): **2-3 hours**
- Phase 3 (Cleanup): **1 hour**
- Phase 4 (Polars backend): **1-2 hours**
- Phase 5 (Integration & testing): **2-3 hours**

**Total: 8-12 hours** for complete implementation and testing
