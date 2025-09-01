# Implementation Patterns for Expression System Refactoring

## Core Implementation Patterns

This document outlines the specific implementation patterns needed to build the universal expression system, focusing on concrete code structures and integration approaches.

## Pattern 1: Expression System Base Classes

### Abstract Base Expression System

```python
# src/mountainash_expressions/core/expression_system/base.py
from abc import ABC, abstractmethod
from typing import Any, Optional, TYPE_CHECKING, Dict, Type

if TYPE_CHECKING:
    from ...core.logic import ExpressionNode
    from ...core.visitor import ExpressionSystemVisitor

class ExpressionSystem(ABC):
    """
    Base class for all expression systems with type dispatch capabilities.
    
    Each backend (Narwhals, Polars, Ibis) extends this to provide
    native expression generation with automatic type conversion.
    """
    
    def __init__(self):
        self._current_visitor: Optional['ExpressionSystemVisitor'] = None
        self._native_type_cache: Dict[int, Any] = {}
    
    # ========================================
    # Public Interface (with type dispatch)
    # ========================================
    
    def col(self, name: str) -> Any:
        """Create a column reference in backend's native format."""
        return self._native_col(name)
    
    def lit(self, value: Any) -> Any:
        """Create a literal value in backend's native format."""
        return self._native_lit(value)
    
    def and_(self, left: Any, right: Any) -> Any:
        """Logical AND with automatic type dispatch."""
        left_native = self._to_native_expr(left)
        right_native = self._to_native_expr(right)
        return self._native_and(left_native, right_native)
    
    def or_(self, left: Any, right: Any) -> Any:
        """Logical OR with automatic type dispatch."""
        left_native = self._to_native_expr(left)
        right_native = self._to_native_expr(right)
        return self._native_or(left_native, right_native)
    
    def not_(self, expr: Any) -> Any:
        """Logical NOT with automatic type dispatch."""
        expr_native = self._to_native_expr(expr)
        return self._native_not(expr_native)
    
    def eq(self, left: Any, right: Any) -> Any:
        """Equality comparison with automatic type dispatch."""
        left_native = self._to_native_expr(left)
        right_native = self._to_native_expr(right)
        return self._native_eq(left_native, right_native)
    
    # ========================================
    # Ternary Logic Interface
    # ========================================
    
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
    
    def ternary_not(self, expr: Any) -> Any:
        """Ternary NOT with automatic type dispatch."""
        expr_native = self._to_native_expr(expr)
        return self._native_ternary_not(expr_native)
    
    # ========================================
    # Core Type Dispatch Logic
    # ========================================
    
    def _to_native_expr(self, obj: Any) -> Any:
        """
        Convert any input to native backend expression.
        
        Handles:
        - MountainAsh expression nodes (via visitor)
        - Native expressions (pass through)
        - String literals (convert to column references)
        - Python literals (convert to literal expressions)
        """
        # Use caching for performance
        obj_id = id(obj)
        if obj_id in self._native_type_cache:
            return self._native_type_cache[obj_id]
        
        result = self._convert_to_native(obj)
        self._native_type_cache[obj_id] = result
        return result
    
    def _convert_to_native(self, obj: Any) -> Any:
        """Actual conversion logic without caching."""
        if self._is_mountainash_node(obj):
            return self._convert_mountainash_node(obj)
        elif self._is_native_expr(obj):
            return obj  # Already in native format
        elif isinstance(obj, str):
            return self._native_col(obj)  # String -> column reference
        elif obj is None or isinstance(obj, (int, float, bool)):
            return self._native_lit(obj)  # Literal value
        else:
            raise TypeError(f"Cannot convert {type(obj).__name__} to {self.get_backend_name()} expression")
    
    def _is_mountainash_node(self, obj: Any) -> bool:
        """Check if object is a MountainAsh expression node."""
        from ...core.logic import ExpressionNode
        return isinstance(obj, ExpressionNode)
    
    def _convert_mountainash_node(self, node: 'ExpressionNode') -> Any:
        """Convert MountainAsh node via registered visitor."""
        if self._current_visitor is None:
            raise RuntimeError(
                f"No visitor registered for {self.get_backend_name()} - "
                "cannot convert MountainAsh expression nodes"
            )
        return node.accept(self._current_visitor)
    
    # ========================================
    # Visitor Integration
    # ========================================
    
    def _set_current_visitor(self, visitor: 'ExpressionSystemVisitor') -> None:
        """Register visitor for MountainAsh node conversion."""
        self._current_visitor = visitor
    
    # ========================================
    # Backend Information
    # ========================================
    
    @abstractmethod
    def get_backend_name(self) -> str:
        """Return human-readable backend name."""
        pass
    
    @abstractmethod
    def get_native_expression_type(self) -> Type:
        """Return the native expression type for this backend."""
        pass
    
    # ========================================
    # Abstract Methods (Backend-Specific)
    # ========================================
    
    @abstractmethod
    def _native_col(self, name: str) -> Any:
        """Create native column reference."""
        pass
    
    @abstractmethod
    def _native_lit(self, value: Any) -> Any:
        """Create native literal value."""
        pass
    
    @abstractmethod
    def _native_and(self, left: Any, right: Any) -> Any:
        """Native boolean AND operation."""
        pass
    
    @abstractmethod
    def _native_or(self, left: Any, right: Any) -> Any:
        """Native boolean OR operation."""
        pass
    
    @abstractmethod
    def _native_not(self, expr: Any) -> Any:
        """Native boolean NOT operation."""
        pass
    
    @abstractmethod
    def _native_eq(self, left: Any, right: Any) -> Any:
        """Native equality comparison."""
        pass
    
    @abstractmethod
    def _is_native_expr(self, obj: Any) -> bool:
        """Check if object is native expression for this backend."""
        pass
    
    # Ternary logic abstract methods
    @abstractmethod
    def _native_ternary_and(self, left: Any, right: Any) -> Any:
        """Native ternary AND operation."""
        pass
    
    @abstractmethod
    def _native_ternary_or(self, left: Any, right: Any) -> Any:
        """Native ternary OR operation."""
        pass
    
    @abstractmethod
    def _native_ternary_not(self, expr: Any) -> Any:
        """Native ternary NOT operation."""
        pass
```

## Pattern 2: Backend-Specific Implementations

### Narwhals Expression System

```python
# src/mountainash_expressions/backends/narwhals_system/expression_system.py
import narwhals as nw
from ...core.expression_system.base import ExpressionSystem

class NarwhalsExpressionSystem(ExpressionSystem):
    """
    Narwhals-based expression system providing multi-dataframe support.
    
    Supports pandas, polars, pyarrow, and other Narwhals-compatible backends
    through a single unified interface.
    """
    
    def get_backend_name(self) -> str:
        return "narwhals"
    
    def get_native_expression_type(self) -> type:
        return nw.Expr
    
    # ========================================
    # Native Expression Creation
    # ========================================
    
    def _native_col(self, name: str) -> nw.Expr:
        return nw.col(name)
    
    def _native_lit(self, value: Any) -> nw.Expr:
        return nw.lit(value)
    
    # ========================================
    # Boolean Operations
    # ========================================
    
    def _native_and(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        return left & right
    
    def _native_or(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        return left | right
    
    def _native_not(self, expr: nw.Expr) -> nw.Expr:
        return ~expr
    
    def _native_eq(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        return left == right
    
    # ========================================
    # Type Detection
    # ========================================
    
    def _is_native_expr(self, obj: Any) -> bool:
        return isinstance(obj, nw.Expr)
    
    # ========================================
    # Ternary Logic Implementation
    # ========================================
    
    def _native_ternary_and(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        """
        Ternary AND using Narwhals when/then/otherwise.
        
        Truth table:
        - FALSE AND anything = FALSE
        - TRUE AND TRUE = TRUE
        - TRUE AND NULL = NULL
        - NULL AND anything = NULL (unless other is FALSE)
        """
        return (
            nw.when((left == False) | (right == False)).then(False)
            .when((left == True) & (right == True)).then(True)
            .otherwise(None)  # UNKNOWN/NULL
        )
    
    def _native_ternary_or(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        """
        Ternary OR using Narwhals when/then/otherwise.
        
        Truth table:
        - TRUE OR anything = TRUE
        - FALSE OR FALSE = FALSE
        - FALSE OR NULL = NULL
        - NULL OR anything = NULL (unless other is TRUE)
        """
        return (
            nw.when((left == True) | (right == True)).then(True)
            .when((left == False) & (right == False)).then(False)
            .otherwise(None)  # UNKNOWN/NULL
        )
    
    def _native_ternary_not(self, expr: nw.Expr) -> nw.Expr:
        """
        Ternary NOT using Narwhals when/then/otherwise.
        
        Truth table:
        - NOT TRUE = FALSE
        - NOT FALSE = TRUE  
        - NOT NULL = NULL
        """
        return (
            nw.when(expr == True).then(False)
            .when(expr == False).then(True)
            .otherwise(None)  # UNKNOWN/NULL
        )
```

### Polars Expression System

```python
# src/mountainash_expressions/backends/polars_system/expression_system.py
import polars as pl
from ...core.expression_system.base import ExpressionSystem

class PolarsExpressionSystem(ExpressionSystem):
    """
    Native Polars expression system for optimal performance.
    
    Uses Polars expressions directly, bypassing Narwhals layer
    for maximum performance when working specifically with Polars.
    """
    
    def get_backend_name(self) -> str:
        return "polars"
    
    def get_native_expression_type(self) -> type:
        return pl.Expr
    
    # ========================================
    # Native Expression Creation
    # ========================================
    
    def _native_col(self, name: str) -> pl.Expr:
        return pl.col(name)
    
    def _native_lit(self, value: Any) -> pl.Expr:
        return pl.lit(value)
    
    # ========================================
    # Boolean Operations
    # ========================================
    
    def _native_and(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        return left & right
    
    def _native_or(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        return left | right
    
    def _native_not(self, expr: pl.Expr) -> pl.Expr:
        return ~expr
    
    def _native_eq(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        return left == right
    
    # ========================================
    # Type Detection
    # ========================================
    
    def _is_native_expr(self, obj: Any) -> bool:
        return isinstance(obj, pl.Expr)
    
    # ========================================
    # Ternary Logic Implementation
    # ========================================
    
    def _native_ternary_and(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Ternary AND using Polars when/then/otherwise."""
        return (
            pl.when((left == False) | (right == False)).then(False)
            .when((left == True) & (right == True)).then(True)
            .otherwise(None)
        )
    
    def _native_ternary_or(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Ternary OR using Polars when/then/otherwise."""
        return (
            pl.when((left == True) | (right == True)).then(True)
            .when((left == False) & (right == False)).then(False)
            .otherwise(None)
        )
    
    def _native_ternary_not(self, expr: pl.Expr) -> pl.Expr:
        """Ternary NOT using Polars when/then/otherwise."""
        return (
            pl.when(expr == True).then(False)
            .when(expr == False).then(True)
            .otherwise(None)
        )
```

### Ibis Expression System

```python
# src/mountainash_expressions/backends/ibis_system/expression_system.py
import ibis
import ibis.expr.types as ir
from ...core.expression_system.base import ExpressionSystem

class IbisExpressionSystem(ExpressionSystem):
    """
    Ibis-based expression system for analytical SQL operations.
    
    Provides SQL-compatible expressions that can be executed
    across multiple SQL backends (PostgreSQL, Spark, etc.).
    """
    
    def __init__(self, table: ir.Table):
        super().__init__()
        self.table = table
    
    def get_backend_name(self) -> str:
        return "ibis"
    
    def get_native_expression_type(self) -> type:
        return ir.Expr
    
    # ========================================
    # Native Expression Creation
    # ========================================
    
    def _native_col(self, name: str) -> ir.Column:
        if name not in self.table.columns:
            raise ValueError(f"Column '{name}' not found in table. Available: {self.table.columns}")
        return self.table[name]
    
    def _native_lit(self, value: Any) -> ir.Scalar:
        return ibis.literal(value)
    
    # ========================================
    # Boolean Operations
    # ========================================
    
    def _native_and(self, left: ir.BooleanValue, right: ir.BooleanValue) -> ir.BooleanValue:
        return left & right
    
    def _native_or(self, left: ir.BooleanValue, right: ir.BooleanValue) -> ir.BooleanValue:
        return left | right
    
    def _native_not(self, expr: ir.BooleanValue) -> ir.BooleanValue:
        return ~expr
    
    def _native_eq(self, left: ir.Value, right: ir.Value) -> ir.BooleanValue:
        return left == right
    
    # ========================================
    # Type Detection
    # ========================================
    
    def _is_native_expr(self, obj: Any) -> bool:
        return isinstance(obj, (ir.Expr, ir.Value))
    
    # ========================================
    # Ternary Logic Implementation
    # ========================================
    
    def _native_ternary_and(self, left: ir.BooleanValue, right: ir.BooleanValue) -> ir.BooleanValue:
        """Ternary AND using Ibis case expressions."""
        return (
            ibis.case()
            .when((left == False) | (right == False), False)
            .when((left == True) & (right == True), True)
            .else_(None)  # UNKNOWN/NULL
            .end()
        )
    
    def _native_ternary_or(self, left: ir.BooleanValue, right: ir.BooleanValue) -> ir.BooleanValue:
        """Ternary OR using Ibis case expressions."""
        return (
            ibis.case()
            .when((left == True) | (right == True), True)
            .when((left == False) & (right == False), False)
            .else_(None)  # UNKNOWN/NULL
            .end()
        )
    
    def _native_ternary_not(self, expr: ir.BooleanValue) -> ir.BooleanValue:
        """Ternary NOT using Ibis case expressions."""
        return (
            ibis.case()
            .when(expr == True, False)
            .when(expr == False, True)
            .else_(None)  # UNKNOWN/NULL
            .end()
        )
```

## Pattern 3: Visitor Integration

### Base Expression System Visitor

```python
# src/mountainash_expressions/core/visitor/expression_system_visitor.py
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..expression_system.base import ExpressionSystem
    from ..logic import ExpressionNode, LogicalAndNode, LogicalOrNode, ColumnNode, LiteralNode

class ExpressionSystemVisitor(ABC):
    """
    Base visitor that integrates with expression systems.
    
    This visitor automatically registers itself with the expression system
    to enable recursive MountainAsh node conversion during type dispatch.
    """
    
    def __init__(self, expression_system: 'ExpressionSystem', logic_type: str):
        self.backend = expression_system
        self.logic_type = logic_type
        
        # CRITICAL: Register with expression system for recursive conversion
        self.backend._set_current_visitor(self)
    
    # ========================================
    # Logical Operations with Type Dispatch
    # ========================================
    
    def visit_logical_and(self, node: 'LogicalAndNode') -> Any:
        """Visit AND node with automatic type dispatch."""
        if not node.operands:
            raise ValueError("AND node must have operands")
        
        # Start with first operand
        result = self._visit_operand(node.operands[0])
        
        # Chain AND operations - backend handles type dispatch
        for operand in node.operands[1:]:
            right = self._visit_operand(operand)
            result = self._get_and_operation()(result, right)
        
        return result
    
    def visit_logical_or(self, node: 'LogicalOrNode') -> Any:
        """Visit OR node with automatic type dispatch."""
        if not node.operands:
            raise ValueError("OR node must have operands")
        
        result = self._visit_operand(node.operands[0])
        for operand in node.operands[1:]:
            right = self._visit_operand(operand)
            result = self._get_or_operation()(result, right)
        
        return result
    
    def _visit_operand(self, operand: Any) -> Any:
        """Visit operand with automatic type dispatch."""
        if isinstance(operand, self._get_expression_node_type()):
            # Recursive MountainAsh node
            return operand.accept(self)
        else:
            # Let expression system handle type conversion
            return self.backend._to_native_expr(operand)
    
    # ========================================
    # Basic Node Visitors
    # ========================================
    
    def visit_column(self, node: 'ColumnNode') -> Any:
        """Convert column node to backend-specific column reference."""
        return self.backend.col(node.name)
    
    def visit_literal(self, node: 'LiteralNode') -> Any:
        """Convert literal node to backend-specific literal."""
        return self.backend.lit(node.value)
    
    # ========================================
    # Abstract Methods for Logic Type Specialization
    # ========================================
    
    @abstractmethod
    def _get_and_operation(self):
        """Return the appropriate AND operation for this logic type."""
        pass
    
    @abstractmethod
    def _get_or_operation(self):
        """Return the appropriate OR operation for this logic type."""
        pass
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _get_expression_node_type(self):
        """Get the base expression node type for isinstance checks."""
        from ..logic import ExpressionNode
        return ExpressionNode
```

### Boolean Logic Visitor

```python
# src/mountainash_expressions/core/visitor/boolean_visitor.py
from .expression_system_visitor import ExpressionSystemVisitor

class BooleanExpressionSystemVisitor(ExpressionSystemVisitor):
    """
    Visitor for standard boolean logic operations.
    
    Uses backend's standard boolean operations (and_, or_, not_).
    """
    
    def __init__(self, expression_system):
        super().__init__(expression_system, "boolean")
    
    def _get_and_operation(self):
        """Standard boolean AND operation."""
        return self.backend.and_
    
    def _get_or_operation(self):
        """Standard boolean OR operation."""
        return self.backend.or_
    
    def visit_logical_not(self, node) -> Any:
        """Boolean NOT operation."""
        if len(node.operands) != 1:
            raise ValueError("NOT operation requires exactly one operand")
        
        operand = self._visit_operand(node.operands[0])
        return self.backend.not_(operand)
```

### Ternary Logic Visitor

```python
# src/mountainash_expressions/core/visitor/ternary_visitor.py
from .expression_system_visitor import ExpressionSystemVisitor

class TernaryExpressionSystemVisitor(ExpressionSystemVisitor):
    """
    Visitor for three-valued logic operations.
    
    Uses backend's ternary logic operations (ternary_and, ternary_or, ternary_not)
    which implement proper NULL/UNKNOWN handling.
    """
    
    def __init__(self, expression_system):
        super().__init__(expression_system, "ternary")
    
    def _get_and_operation(self):
        """Ternary AND operation with NULL handling."""
        return self.backend.ternary_and
    
    def _get_or_operation(self):
        """Ternary OR operation with NULL handling."""
        return self.backend.ternary_or
    
    def visit_logical_not(self, node) -> Any:
        """Ternary NOT operation."""
        if len(node.operands) != 1:
            raise ValueError("NOT operation requires exactly one operand")
        
        operand = self._visit_operand(node.operands[0])
        return self.backend.ternary_not(operand)
    
    # ========================================
    # Ternary-Specific Operations
    # ========================================
    
    def visit_is_unknown(self, node) -> Any:
        """Check if value is UNKNOWN/NULL."""
        if len(node.operands) != 1:
            raise ValueError("IS_UNKNOWN operation requires exactly one operand")
        
        operand = self._visit_operand(node.operands[0])
        return self.backend._to_native_expr(operand).is_null()
    
    def visit_is_known(self, node) -> Any:
        """Check if value is not UNKNOWN/NULL."""
        if len(node.operands) != 1:
            raise ValueError("IS_KNOWN operation requires exactly one operand")
        
        operand = self._visit_operand(node.operands[0])
        return self.backend._to_native_expr(operand).is_not_null()
```

## Pattern 4: Expression Compilation API

### Expression Compiler

```python
# src/mountainash_expressions/core/compiler.py
from typing import Any, Dict, Type
from .expression_system.base import ExpressionSystem
from .visitor.expression_system_visitor import ExpressionSystemVisitor
from .visitor.boolean_visitor import BooleanExpressionSystemVisitor
from .visitor.ternary_visitor import TernaryExpressionSystemVisitor

class ExpressionCompiler:
    """
    Compiles MountainAsh expression trees to backend-specific expressions.
    
    Handles backend selection, visitor creation, and expression compilation.
    """
    
    def __init__(self):
        self._expression_systems: Dict[str, ExpressionSystem] = {}
        self._visitor_classes: Dict[str, Type[ExpressionSystemVisitor]] = {
            "boolean": BooleanExpressionSystemVisitor,
            "ternary": TernaryExpressionSystemVisitor,
        }
    
    def register_backend(self, name: str, expression_system: ExpressionSystem):
        """Register an expression system backend."""
        self._expression_systems[name] = expression_system
    
    def register_logic_type(self, name: str, visitor_class: Type[ExpressionSystemVisitor]):
        """Register a logic type visitor."""
        self._visitor_classes[name] = visitor_class
    
    def compile(self, expression_tree: Any, backend: str, logic_type: str = "boolean") -> Any:
        """
        Compile expression tree to backend-specific expression.
        
        Args:
            expression_tree: MountainAsh expression tree
            backend: Backend name ("narwhals", "polars", "ibis")
            logic_type: Logic type ("boolean", "ternary")
            
        Returns:
            Backend-specific native expression
        """
        if backend not in self._expression_systems:
            raise ValueError(f"Unknown backend: {backend}. Available: {list(self._expression_systems.keys())}")
        
        if logic_type not in self._visitor_classes:
            raise ValueError(f"Unknown logic type: {logic_type}. Available: {list(self._visitor_classes.keys())}")
        
        # Get expression system and visitor
        expression_system = self._expression_systems[backend]
        visitor_class = self._visitor_classes[logic_type]
        visitor = visitor_class(expression_system)
        
        # Compile expression
        try:
            return expression_tree.accept(visitor)
        except Exception as e:
            raise CompilationError(
                f"Failed to compile expression to {backend} backend with {logic_type} logic: {e}"
            ) from e


class CompilationError(Exception):
    """Raised when expression compilation fails."""
    pass


# Global compiler instance
_compiler = ExpressionCompiler()

def compile_expression(expression_tree: Any, backend: str, logic_type: str = "boolean") -> Any:
    """Convenience function for expression compilation."""
    return _compiler.compile(expression_tree, backend, logic_type)

def register_backend(name: str, expression_system: ExpressionSystem):
    """Convenience function for backend registration."""
    _compiler.register_backend(name, expression_system)
```

## Pattern 5: Usage Examples

### Basic Usage Pattern

```python
# examples/basic_usage.py
from mountainash_expressions.core.logic import LogicalAndNode, ColumnNode, LiteralNode
from mountainash_expressions.core.compiler import compile_expression, register_backend
from mountainash_expressions.backends.narwhals_system import NarwhalsExpressionSystem
from mountainash_expressions.backends.polars_system import PolarsExpressionSystem

# Register backends
register_backend("narwhals", NarwhalsExpressionSystem())
register_backend("polars", PolarsExpressionSystem())

# Create expression tree
expression = LogicalAndNode([
    ColumnNode("age"),
    LiteralNode(25),
    ColumnNode("active")
])

# Compile to different backends
narwhals_expr = compile_expression(expression, "narwhals", "boolean")
polars_expr = compile_expression(expression, "polars", "ternary")

# Use with dataframes
import pandas as pd
import polars as pl
import narwhals as nw

# Narwhals (works with any supported dataframe)
df_pandas = pd.DataFrame({"age": [20, 30], "active": [True, False]})
nw_df = nw.from_native(df_pandas)
result = nw_df.filter(narwhals_expr)

# Polars (native performance)
df_polars = pl.DataFrame({"age": [20, 30], "active": [True, None]})
result = df_polars.filter(polars_expr)
```

### Advanced Type Dispatch Example

```python
# examples/type_dispatch_example.py
def demonstrate_type_dispatch():
    """Show how type dispatch handles mixed input types."""
    
    # Complex expression with mixed types
    expression = LogicalAndNode([
        ColumnNode("user_age"),          # MountainAsh node
        25,                              # Python int literal
        "is_active",                     # String (column name)
        LogicalOrNode([                  # Nested MountainAsh node
            LiteralNode(True),           # MountainAsh literal node
            ColumnNode("is_premium")     # Another MountainAsh node
        ])
    ])
    
    # Compilation automatically handles all type conversions:
    # 1. ColumnNode("user_age") -> backend.col("user_age")
    # 2. 25 -> backend.lit(25)
    # 3. "is_active" -> backend.col("is_active")
    # 4. Nested LogicalOrNode -> recursive visitor call
    # 5. All combined with appropriate and_/or_ operations
    
    narwhals_expr = compile_expression(expression, "narwhals", "ternary")
    return narwhals_expr
```

This implementation pattern provides the foundation for building the universal expression system with clean type dispatch, extensible backends, and consistent logic type handling across all supported expression systems.