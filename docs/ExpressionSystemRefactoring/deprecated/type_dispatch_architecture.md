# Type Dispatch Architecture for Universal Expression System

## Overview

The universal expression system must handle a fundamental challenge: bridging MountainAsh expression nodes with native backend expressions through a clean interface. The `Any` parameters in the expression system protocol hide complex type dispatch logic that enables seamless interoperability between different expression representations.

## Core Challenge

Methods like these need to handle multiple input types:

```python
def and_(self, left: Any, right: Any) -> Any:
    # left/right could be:
    # 1. MountainAsh ExpressionNode -> needs visitor conversion
    # 2. Native backend expression (nw.Expr, pl.Expr, ibis.Expr) -> use directly
    # 3. Python literal (int, str, bool) -> convert via lit()
    # 4. Column name string -> convert via col()
    # 5. Nested combinations of the above
```

This requires sophisticated type dispatch to convert inputs appropriately while maintaining type safety and performance.

## Architecture Patterns

### Pattern 1: Two-Level Type Dispatch System

The architecture uses a two-level dispatch system:
1. **Expression System Level**: Handles immediate type detection and conversion
2. **Visitor Level**: Handles recursive tree traversal and node conversion

```python
# core/expression_system/protocol.py
from typing import Union, Any, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from ...core.logic import ExpressionNode

class ExpressionSystem(ABC):
    """Protocol for backend expression systems with type dispatch."""
    
    def __init__(self):
        self._current_visitor = None
    
    def _set_current_visitor(self, visitor):
        """Called by visitors to register for recursive conversion."""
        self._current_visitor = visitor
    
    def and_(self, left: Any, right: Any) -> Any:
        """Public interface with automatic type dispatch."""
        left_native = self._to_native_expr(left)
        right_native = self._to_native_expr(right)
        return self._native_and(left_native, right_native)
    
    def or_(self, left: Any, right: Any) -> Any:
        """Public interface with automatic type dispatch."""
        left_native = self._to_native_expr(left)
        right_native = self._to_native_expr(right)
        return self._native_or(left_native, right_native)
    
    # Core type dispatch method
    def _to_native_expr(self, obj: Any) -> Any:
        """Convert any input to native backend expression."""
        if self._is_mountainash_node(obj):
            return self._convert_mountainash_node(obj)
        elif self._is_native_expr(obj):
            return obj  # Already converted
        elif isinstance(obj, str):
            return self.col(obj)  # String -> column reference
        else:
            return self.lit(obj)  # Literal value
    
    # Backend-specific methods (implemented by each backend)
    @abstractmethod
    def col(self, name: str) -> Any:
        """Create column reference in backend's native format."""
        pass
    
    @abstractmethod
    def lit(self, value: Any) -> Any:
        """Create literal value in backend's native format."""
        pass
    
    @abstractmethod
    def _native_and(self, left: Any, right: Any) -> Any:
        """Backend-specific AND operation on native expressions."""
        pass
    
    @abstractmethod
    def _native_or(self, left: Any, right: Any) -> Any:
        """Backend-specific OR operation on native expressions."""
        pass
    
    @abstractmethod
    def _is_native_expr(self, obj: Any) -> bool:
        """Check if object is a native expression for this backend."""
        pass
    
    # MountainAsh node handling
    def _is_mountainash_node(self, obj: Any) -> bool:
        """Check if object is a MountainAsh expression node."""
        from ...core.logic import ExpressionNode
        return isinstance(obj, ExpressionNode)
    
    def _convert_mountainash_node(self, node: 'ExpressionNode') -> Any:
        """Convert MountainAsh node to native expression via visitor."""
        if self._current_visitor is None:
            raise RuntimeError("No visitor registered - cannot convert MountainAsh nodes")
        return node.accept(self._current_visitor)
```

### Pattern 2: Backend-Specific Type Detection

Each backend implements type detection for its own expression types:

```python
# backends/narwhals_system/expression_system.py
import narwhals as nw

class NarwhalsExpressionSystem(ExpressionSystem):
    """Narwhals backend with multi-dataframe support."""
    
    def col(self, name: str) -> nw.Expr:
        return nw.col(name)
    
    def lit(self, value: Any) -> nw.Expr:
        return nw.lit(value)
    
    def _native_and(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        return left & right
    
    def _native_or(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        return left | right
    
    def _is_native_expr(self, obj: Any) -> bool:
        return isinstance(obj, nw.Expr)


# backends/polars_system/expression_system.py
import polars as pl

class PolarsExpressionSystem(ExpressionSystem):
    """Native Polars backend for performance optimization."""
    
    def col(self, name: str) -> pl.Expr:
        return pl.col(name)
    
    def lit(self, value: Any) -> pl.Expr:
        return pl.lit(value)
    
    def _native_and(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        return left & right
    
    def _native_or(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        return left | right
    
    def _is_native_expr(self, obj: Any) -> bool:
        return isinstance(obj, pl.Expr)


# backends/ibis_system/expression_system.py
import ibis
import ibis.expr.types as ir

class IbisExpressionSystem(ExpressionSystem):
    """Ibis backend for analytical SQL operations."""
    
    def __init__(self, table: ir.Table):
        super().__init__()
        self.table = table
    
    def col(self, name: str) -> ir.Column:
        return self.table[name]
    
    def lit(self, value: Any) -> ir.Scalar:
        return ibis.literal(value)
    
    def _native_and(self, left: ir.BooleanValue, right: ir.BooleanValue) -> ir.BooleanValue:
        return left & right
    
    def _native_or(self, left: ir.BooleanValue, right: ir.BooleanValue) -> ir.BooleanValue:
        return left | right
    
    def _is_native_expr(self, obj: Any) -> bool:
        return isinstance(obj, (ir.Expr, ir.Value))
```

### Pattern 3: Visitor-Expression System Integration

Visitors register themselves with expression systems to enable recursive conversion:

```python
# core/visitor/expression_system_visitor.py
from abc import ABC, abstractmethod
from typing import Any

class ExpressionSystemVisitor(ABC):
    """Base visitor that integrates with expression systems for type dispatch."""
    
    def __init__(self, expression_system: ExpressionSystem, logic_type: str):
        self.backend = expression_system
        self.logic_type = logic_type
        
        # CRITICAL: Register this visitor with the expression system
        # This enables recursive MountainAsh node conversion
        self.backend._set_current_visitor(self)
    
    def visit_logical_and(self, node: LogicalAndNode) -> Any:
        """Visit AND node with automatic type dispatch."""
        operands = node.operands
        
        # Start with first operand
        result = self._visit_operand(operands[0])
        
        # Chain AND operations - backend handles type dispatch
        for operand in operands[1:]:
            right = self._visit_operand(operand)
            result = self.backend.and_(result, right)  # Type dispatch here
        
        return result
    
    def visit_logical_or(self, node: LogicalOrNode) -> Any:
        """Visit OR node with automatic type dispatch."""
        operands = node.operands
        
        result = self._visit_operand(operands[0])
        for operand in operands[1:]:
            right = self._visit_operand(operand)
            result = self.backend.or_(result, right)  # Type dispatch here
        
        return result
    
    def _visit_operand(self, operand: Any) -> Any:
        """Visit an operand with automatic type handling."""
        if isinstance(operand, ExpressionNode):
            # Recursive node traversal
            return operand.accept(self)
        else:
            # Let expression system handle type conversion
            return self.backend._to_native_expr(operand)
    
    # Standard node visitors
    def visit_column(self, node: ColumnNode) -> Any:
        return self.backend.col(node.name)
    
    def visit_literal(self, node: LiteralNode) -> Any:
        return self.backend.lit(node.value)
    
    def visit_comparison(self, node: ComparisonNode) -> Any:
        left = self._visit_operand(node.left)
        right = self._visit_operand(node.right)
        
        # Dispatch to appropriate comparison method
        if node.operator == "==":
            return self.backend.eq(left, right)
        elif node.operator == "!=":
            return self.backend.ne(left, right)
        # ... other operators
```

### Pattern 4: Logic Type Specialization

Different logic types extend the base visitor with specialized behavior:

```python
# core/visitor/boolean_visitor.py
class BooleanExpressionSystemVisitor(ExpressionSystemVisitor):
    """Visitor for standard boolean logic."""
    
    def __init__(self, expression_system: ExpressionSystem):
        super().__init__(expression_system, "boolean")
    
    # Inherits standard behavior from base class
    # Boolean AND/OR use direct backend operations


# core/visitor/ternary_visitor.py
class TernaryExpressionSystemVisitor(ExpressionSystemVisitor):
    """Visitor for three-valued logic with if-then-else patterns."""
    
    def __init__(self, expression_system: ExpressionSystem):
        super().__init__(expression_system, "ternary")
    
    def visit_logical_and(self, node: LogicalAndNode) -> Any:
        """Ternary AND using backend-specific conditional logic."""
        left = self._visit_operand(node.operands[0])
        right = self._visit_operand(node.operands[1])
        
        # Delegate to backend's ternary implementation
        return self.backend.ternary_and(left, right)
    
    def visit_logical_or(self, node: LogicalOrNode) -> Any:
        """Ternary OR using backend-specific conditional logic."""
        left = self._visit_operand(node.operands[0])
        right = self._visit_operand(node.operands[1])
        
        return self.backend.ternary_or(left, right)
```

### Pattern 5: Ternary Logic Implementation

Each backend implements ternary logic using native conditional expressions:

```python
# Extension to ExpressionSystem protocol for ternary operations
class ExpressionSystem(ABC):
    # ... existing methods ...
    
    def ternary_and(self, left: Any, right: Any) -> Any:
        """Ternary AND with automatic type dispatch."""
        left_native = self._to_native_expr(left)
        right_native = self._to_native_expr(right)
        return self._native_ternary_and(left_native, right_native)
    
    def ternary_or(self, left: Any, right: Any) -> Any:
        """Ternary OR with automatic type dispatch."""
        left_native = self._to_native_expr(left)
        right_native = self._to_native_expr(right)
        return self._native_ternary_or(left_native, right_native)
    
    @abstractmethod
    def _native_ternary_and(self, left: Any, right: Any) -> Any:
        """Backend-specific ternary AND implementation."""
        pass
    
    @abstractmethod
    def _native_ternary_or(self, left: Any, right: Any) -> Any:
        """Backend-specific ternary OR implementation."""
        pass


# Backend implementations
class NarwhalsExpressionSystem(ExpressionSystem):
    def _native_ternary_and(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        """Ternary AND: FALSE dominates, then UNKNOWN, then TRUE."""
        return (
            nw.when((left == False) | (right == False)).then(False)
            .when((left == True) & (right == True)).then(True)
            .otherwise(None)  # UNKNOWN
        )
    
    def _native_ternary_or(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        """Ternary OR: TRUE dominates, then UNKNOWN, then FALSE."""
        return (
            nw.when((left == True) | (right == True)).then(True)
            .when((left == False) & (right == False)).then(False)
            .otherwise(None)  # UNKNOWN
        )


class PolarsExpressionSystem(ExpressionSystem):
    def _native_ternary_and(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Ternary AND using Polars when/then/otherwise."""
        return (
            pl.when((left == False) | (right == False)).then(False)
            .when((left == True) & (right == True)).then(True)
            .otherwise(None)  # UNKNOWN
        )
    
    def _native_ternary_or(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Ternary OR using Polars when/then/otherwise."""
        return (
            pl.when((left == True) | (right == True)).then(True)
            .when((left == False) & (right == False)).then(False)
            .otherwise(None)  # UNKNOWN
        )


class IbisExpressionSystem(ExpressionSystem):
    def _native_ternary_and(self, left: ir.BooleanValue, right: ir.BooleanValue) -> ir.BooleanValue:
        """Ternary AND using Ibis case/when expressions."""
        return (
            ibis.case()
            .when((left == False) | (right == False), False)
            .when((left == True) & (right == True), True)
            .else_(None)  # UNKNOWN
            .end()
        )
    
    def _native_ternary_or(self, left: ir.BooleanValue, right: ir.BooleanValue) -> ir.BooleanValue:
        """Ternary OR using Ibis case/when expressions."""
        return (
            ibis.case()
            .when((left == True) | (right == True), True)
            .when((left == False) & (right == False), False)
            .else_(None)  # UNKNOWN
            .end()
        )
```

## Expression Compilation Pipeline

The complete flow demonstrates how type dispatch enables seamless compilation:

```python
# Usage example showing type dispatch in action
def compile_expression_example():
    from mountainash_expressions.core.logic import LogicalAndNode, ColumnNode, LiteralNode
    
    # Complex expression tree with mixed types
    expr_tree = LogicalAndNode([
        ColumnNode("age"),           # MountainAsh node
        25,                          # Python literal
        "active",                    # Column name string
        LogicalOrNode([              # Nested MountainAsh node
            ColumnNode("premium"),
            True                     # Boolean literal
        ])
    ])
    
    # Compilation to Narwhals
    narwhals_system = NarwhalsExpressionSystem()
    ternary_visitor = TernaryExpressionSystemVisitor(narwhals_system)
    
    # Type dispatch happens automatically during traversal:
    # 1. ColumnNode("age") -> narwhals_system.col("age") -> nw.col("age")
    # 2. 25 -> narwhals_system.lit(25) -> nw.lit(25)
    # 3. "active" -> narwhals_system.col("active") -> nw.col("active")
    # 4. Nested LogicalOrNode -> recursive visitor call
    # 5. All combined with ternary_and() operations
    
    narwhals_expr = expr_tree.accept(ternary_visitor)
    
    # Compilation to Polars (different native types, same pattern)
    polars_system = PolarsExpressionSystem()
    boolean_visitor = BooleanExpressionSystemVisitor(polars_system)
    polars_expr = expr_tree.accept(boolean_visitor)
    
    # Compilation to Ibis (analytical SQL context)
    ibis_table = get_ibis_table()  # Some Ibis table
    ibis_system = IbisExpressionSystem(ibis_table)
    ternary_visitor = TernaryExpressionSystemVisitor(ibis_system)
    ibis_expr = expr_tree.accept(ternary_visitor)
    
    return narwhals_expr, polars_expr, ibis_expr
```

## Type Safety Considerations

### Runtime Type Checking

While the interface uses `Any`, runtime type checking ensures safety:

```python
def _to_native_expr(self, obj: Any) -> Any:
    """Type dispatch with runtime validation."""
    if self._is_mountainash_node(obj):
        return self._convert_mountainash_node(obj)
    elif self._is_native_expr(obj):
        # Validate it's the correct native type for this backend
        if not self._validate_native_type(obj):
            raise TypeError(f"Expected {self._get_native_type_name()}, got {type(obj)}")
        return obj
    elif isinstance(obj, str):
        return self.col(obj)
    elif isinstance(obj, (int, float, bool, type(None))):
        return self.lit(obj)
    else:
        raise TypeError(f"Cannot convert {type(obj)} to expression")
```

### Generic Type Hints (Future Enhancement)

```python
from typing import TypeVar, Generic

T = TypeVar('T')  # Native expression type for the backend

class ExpressionSystem(Generic[T], ABC):
    """Type-parameterized expression system."""
    
    @abstractmethod
    def col(self, name: str) -> T:
        pass
    
    @abstractmethod
    def lit(self, value: Any) -> T:
        pass
    
    def and_(self, left: Union[T, ExpressionNode, Any], right: Union[T, ExpressionNode, Any]) -> T:
        # Type dispatch with better type hints
        pass

class NarwhalsExpressionSystem(ExpressionSystem[nw.Expr]):
    # Concrete implementation with specific type
    pass
```

## Performance Considerations

### Type Dispatch Overhead

1. **Caching**: Type checks can be expensive, so cache type information when possible
2. **Fast Path**: Direct native-to-native operations bypass dispatch
3. **Visitor Registration**: One-time cost during visitor initialization

### Optimization Strategies

```python
class OptimizedExpressionSystem(ExpressionSystem):
    def __init__(self):
        super().__init__()
        self._type_cache = {}  # Cache type detection results
    
    def _to_native_expr(self, obj: Any) -> Any:
        """Optimized type dispatch with caching."""
        obj_id = id(obj)
        if obj_id in self._type_cache:
            converter = self._type_cache[obj_id]
            return converter(obj)
        
        # Standard dispatch logic with caching
        if self._is_mountainash_node(obj):
            converter = self._convert_mountainash_node
        elif self._is_native_expr(obj):
            converter = lambda x: x
        # ... etc
        
        self._type_cache[obj_id] = converter
        return converter(obj)
```

## Error Handling Patterns

### Type Conversion Errors

```python
class ExpressionTypeError(Exception):
    """Raised when type conversion fails."""
    def __init__(self, obj, backend_type, attempted_conversion):
        self.obj = obj
        self.backend_type = backend_type
        self.attempted_conversion = attempted_conversion
        super().__init__(
            f"Cannot convert {type(obj).__name__} to {backend_type} "
            f"expression via {attempted_conversion}"
        )

def _to_native_expr(self, obj: Any) -> Any:
    """Type dispatch with comprehensive error handling."""
    try:
        # ... dispatch logic ...
    except Exception as e:
        raise ExpressionTypeError(
            obj, 
            self.__class__.__name__, 
            "automatic_dispatch"
        ) from e
```

## Key Architecture Benefits

1. **Clean Interface**: Users see simple methods, complexity is hidden
2. **Type Safety**: Runtime validation ensures correct conversions
3. **Extensibility**: New backends just implement type detection methods
4. **Performance**: Direct native-to-native operations when possible
5. **Flexibility**: Handles mixed expression trees seamlessly
6. **Consistency**: Same patterns work across all backends

This type dispatch architecture is the foundation that makes the universal expression system possible while maintaining clean interfaces and good performance.