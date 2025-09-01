# Refined Expression System Architecture

## Core Architectural Principles

This refined architecture addresses key issues in the initial design, focusing on clean separation of concerns, type-based self-organization, and elimination of magical thinking patterns.

### Key Principles

1. **Node-Operator Alignment**: Every operator gets its own specific node type
2. **Visitor-Operator Alignment**: Every operator gets its own visitor method (1-1 mapping)
3. **Centralized Parameter Dispatch**: ExpressionParameter handles ALL type detection and conversion
4. **Self-Organizing Types**: No "optimized" classes - efficiency emerges from type protocols
5. **Clean Separation**: Each component has a single, clear responsibility

## Core Component: ExpressionParameter

The `ExpressionParameter` class is the cornerstone of the type dispatch system, handling all parameter type detection and conversion in one place.

```python
# core/expression_system/parameter.py
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .base import ExpressionSystem
    from ..visitor import ExpressionVisitor

class ParameterType(Enum):
    """Enumeration of parameter types in priority order."""
    EXPRESSION_NODE = "expression_node"      # MountainAsh expression nodes
    NATIVE_EXPRESSION = "native_expression"  # Backend-specific expressions (pl.Expr, nw.Expr)
    COLUMN_REFERENCE = "column_reference"    # String column names
    LITERAL_VALUE = "literal_value"          # Python literals (int, float, bool, None)
    UNKNOWN = "unknown"                      # Cannot determine type

class ExpressionParameter:
    """
    Centralized parameter type detection and conversion.
    
    This class encapsulates ALL type dispatch logic, providing a clean
    interface for converting various input types to native backend expressions.
    It eliminates scattered type checking throughout the codebase.
    """
    
    def __init__(
        self, 
        value: Any, 
        expression_system: 'ExpressionSystem',
        visitor: Optional['ExpressionVisitor'] = None
    ):
        """
        Initialize parameter with value and conversion context.
        
        Args:
            value: The parameter value to be converted
            expression_system: Backend system for native expression creation
            visitor: Optional visitor for recursive MountainAsh node conversion
        """
        self.value = value
        self.expression_system = expression_system
        self.visitor = visitor
        self._type = self._detect_type()
        
    def _detect_type(self) -> ParameterType:
        """
        Detect parameter type in order of specificity.
        
        Order matters: check from most specific to least specific.
        """
        # 1. MountainAsh expression nodes (highest priority)
        if self._is_expression_node():
            return ParameterType.EXPRESSION_NODE
            
        # 2. Native backend expressions
        if self.expression_system.is_native_expression(self.value):
            return ParameterType.NATIVE_EXPRESSION
            
        # 3. String disambiguation (column vs literal)
        if isinstance(self.value, str):
            if self._looks_like_column_name(self.value):
                return ParameterType.COLUMN_REFERENCE
            else:
                return ParameterType.LITERAL_VALUE
                
        # 4. Python literals
        if self._is_literal():
            return ParameterType.LITERAL_VALUE
            
        # 5. Unknown type
        return ParameterType.UNKNOWN
    
    def _is_expression_node(self) -> bool:
        """Check if value is a MountainAsh expression node."""
        from ...core.logic import ExpressionNode
        return isinstance(self.value, ExpressionNode)
    
    def _is_literal(self) -> bool:
        """Check if value is a Python literal."""
        return self.value is None or isinstance(self.value, (bool, int, float))
    
    def _looks_like_column_name(self, s: str) -> bool:
        """
        Heuristic to determine if string is likely a column name.
        
        Column names typically:
        - Are valid Python identifiers
        - May contain dots for qualified names (table.column)
        - Don't contain spaces or special characters
        """
        # Check for qualified column name (table.column)
        if '.' in s:
            parts = s.split('.')
            return all(part.isidentifier() for part in parts)
        
        # Simple column name
        return s.isidentifier()
    
    def to_native_expression(self) -> Any:
        """
        Convert parameter to native backend expression.
        
        Returns:
            Native expression for the backend
            
        Raises:
            ValueError: If ExpressionNode conversion requires visitor but none provided
            TypeError: If parameter type cannot be converted
        """
        if self._type == ParameterType.EXPRESSION_NODE:
            if not self.visitor:
                raise ValueError(
                    "Cannot convert ExpressionNode without visitor context. "
                    "Provide visitor when creating ExpressionParameter."
                )
            return self.value.accept(self.visitor)
            
        elif self._type == ParameterType.NATIVE_EXPRESSION:
            return self.value  # Already in correct format
            
        elif self._type == ParameterType.COLUMN_REFERENCE:
            return self.expression_system.col(self.value)
            
        elif self._type == ParameterType.LITERAL_VALUE:
            return self.expression_system.lit(self.value)
            
        else:
            raise TypeError(
                f"Cannot convert {type(self.value).__name__} to "
                f"{self.expression_system.get_backend_name()} expression. "
                f"Value: {repr(self.value)}"
            )
    
    @property
    def type_name(self) -> str:
        """Human-readable type name for debugging."""
        return self._type.value
    
    def __repr__(self) -> str:
        return f"ExpressionParameter(type={self.type_name}, value={repr(self.value)})"
```

## Node Type Alignment with Logic Type Binding

Every operator+logic combination gets its own specific node type, binding logic semantics to the node.

```python
# core/logic/nodes.py
from abc import ABC, abstractmethod
from typing import Any, List

class ExpressionNode(ABC):
    """Base class for all expression nodes."""
    
    expression_type: str
    logic_type: str
    
    @abstractmethod
    def accept(self, visitor: 'ExpressionVisitor') -> Any:
        """Accept a visitor for traversal."""
        pass

# ========================================
# Boolean Logic Nodes
# ========================================

class BooleanLogicalAndNode(ExpressionNode):
    """Boolean AND operation: NULLs treated as False."""
    
    expression_type = "logical_and"
    logic_type = "boolean"
    
    def __init__(self, operands: List[Any]):
        self.operands = operands
    
    def accept(self, visitor):
        return visitor.visit_boolean_logical_and(self)

class BooleanLogicalOrNode(ExpressionNode):
    """Boolean OR operation: NULLs treated as False."""
    
    expression_type = "logical_or"
    logic_type = "boolean"
    
    def __init__(self, operands: List[Any]):
        self.operands = operands
    
    def accept(self, visitor):
        return visitor.visit_boolean_logical_or(self)

# ========================================  
# Ternary Logic Nodes
# ========================================

class TernaryLogicalAndNode(ExpressionNode):
    """Ternary AND operation: NULL-aware Kleene logic."""
    
    expression_type = "logical_and"
    logic_type = "ternary"
    
    def __init__(self, operands: List[Any]):
        self.operands = operands
    
    def accept(self, visitor):
        return visitor.visit_ternary_logical_and(self)

class TernaryLogicalOrNode(ExpressionNode):
    """Ternary OR operation: NULL-aware Kleene logic."""
    
    expression_type = "logical_or"
    logic_type = "ternary"
    
    def __init__(self, operands: List[Any]):
        self.operands = operands
    
    def accept(self, visitor):
        return visitor.visit_ternary_logical_or(self)

class LogicalNotNode(ExpressionNode):
    """Logical NOT operation node."""
    
    def __init__(self, operand: Any):
        self.operand = operand
    
    def accept(self, visitor):
        return visitor.visit_logical_not(self)

class LogicalXorNode(ExpressionNode):
    """Logical XOR operation node."""
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_logical_xor(self)

# ========================================
# Boolean Comparison Nodes
# ========================================

class BooleanComparisonEqNode(ExpressionNode):
    """Boolean equality comparison: NULLs treated as False."""
    
    expression_type = "comparison_eq"
    logic_type = "boolean"
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_boolean_comparison_eq(self)

class BooleanComparisonNeNode(ExpressionNode):
    """Boolean inequality comparison: NULLs treated as False."""
    
    expression_type = "comparison_ne"
    logic_type = "boolean"
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_boolean_comparison_ne(self)

class BooleanComparisonGtNode(ExpressionNode):
    """Boolean greater-than comparison: NULLs treated as False."""
    
    expression_type = "comparison_gt"
    logic_type = "boolean"
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_boolean_comparison_gt(self)

class BooleanComparisonLtNode(ExpressionNode):
    """Boolean less-than comparison: NULLs treated as False."""
    
    expression_type = "comparison_lt"
    logic_type = "boolean"
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_boolean_comparison_lt(self)

class BooleanComparisonGeNode(ExpressionNode):
    """Boolean greater-than-or-equal comparison: NULLs treated as False."""
    
    expression_type = "comparison_ge"
    logic_type = "boolean"
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_boolean_comparison_ge(self)

class BooleanComparisonLeNode(ExpressionNode):
    """Boolean less-than-or-equal comparison: NULLs treated as False."""
    
    expression_type = "comparison_le"
    logic_type = "boolean"
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_boolean_comparison_le(self)

class BooleanComparisonInNode(ExpressionNode):
    """Boolean membership test: NULLs treated as False."""
    
    expression_type = "comparison_in"
    logic_type = "boolean"
    
    def __init__(self, value: Any, collection: Any):
        self.value = value
        self.collection = collection
    
    def accept(self, visitor):
        return visitor.visit_boolean_comparison_in(self)

class BooleanComparisonIsNullNode(ExpressionNode):
    """Boolean null check."""
    
    expression_type = "comparison_is_null"
    logic_type = "boolean"
    
    def __init__(self, operand: Any):
        self.operand = operand
    
    def accept(self, visitor):
        return visitor.visit_boolean_comparison_is_null(self)

class BooleanComparisonIsNotNullNode(ExpressionNode):
    """Boolean not-null check."""
    
    expression_type = "comparison_is_not_null"
    logic_type = "boolean"
    
    def __init__(self, operand: Any):
        self.operand = operand
    
    def accept(self, visitor):
        return visitor.visit_boolean_comparison_is_not_null(self)

# ========================================
# Ternary Comparison Nodes
# ========================================

class TernaryComparisonEqNode(ExpressionNode):
    """Ternary equality comparison: NULL-aware with propagation."""
    
    expression_type = "comparison_eq"
    logic_type = "ternary"
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_ternary_comparison_eq(self)

class TernaryComparisonNeNode(ExpressionNode):
    """Ternary inequality comparison: NULL-aware with propagation."""
    
    expression_type = "comparison_ne"
    logic_type = "ternary"
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_ternary_comparison_ne(self)

class TernaryComparisonGtNode(ExpressionNode):
    """Ternary greater-than comparison: NULL-aware with propagation."""
    
    expression_type = "comparison_gt"
    logic_type = "ternary"
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_ternary_comparison_gt(self)

class TernaryComparisonLtNode(ExpressionNode):
    """Ternary less-than comparison: NULL-aware with propagation."""
    
    expression_type = "comparison_lt"
    logic_type = "ternary"
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_ternary_comparison_lt(self)

class TernaryComparisonGeNode(ExpressionNode):
    """Ternary greater-than-or-equal comparison: NULL-aware with propagation."""
    
    expression_type = "comparison_ge"  
    logic_type = "ternary"
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_ternary_comparison_ge(self)

class TernaryComparisonLeNode(ExpressionNode):
    """Ternary less-than-or-equal comparison: NULL-aware with propagation."""
    
    expression_type = "comparison_le"
    logic_type = "ternary"
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_ternary_comparison_le(self)

class TernaryComparisonInNode(ExpressionNode):
    """Ternary membership test: NULL-aware with propagation."""
    
    expression_type = "comparison_in"
    logic_type = "ternary"
    
    def __init__(self, value: Any, collection: Any):
        self.value = value
        self.collection = collection
    
    def accept(self, visitor):
        return visitor.visit_ternary_comparison_in(self)

class TernaryComparisonIsNullNode(ExpressionNode):
    """Ternary null check (equivalent to boolean)."""
    
    expression_type = "comparison_is_null"
    logic_type = "ternary"
    
    def __init__(self, operand: Any):
        self.operand = operand
    
    def accept(self, visitor):
        return visitor.visit_ternary_comparison_is_null(self)

class TernaryComparisonIsNotNullNode(ExpressionNode):
    """Ternary not-null check (equivalent to boolean)."""
    
    expression_type = "comparison_is_not_null"
    logic_type = "ternary"
    
    def __init__(self, operand: Any):
        self.operand = operand
    
    def accept(self, visitor):
        return visitor.visit_ternary_comparison_is_not_null(self)

# ========================================
# Ternary Logic Nodes
# ========================================

class TernaryIsUnknownNode(ExpressionNode):
    """Check if value is UNKNOWN/NULL in ternary logic."""
    
    def __init__(self, operand: Any):
        self.operand = operand
    
    def accept(self, visitor):
        return visitor.visit_ternary_is_unknown(self)

class TernaryIsKnownNode(ExpressionNode):
    """Check if value is not UNKNOWN/NULL in ternary logic."""
    
    def __init__(self, operand: Any):
        self.operand = operand
    
    def accept(self, visitor):
        return visitor.visit_ternary_is_known(self)

class TernaryMaybeTrueNode(ExpressionNode):
    """Check if value is TRUE or UNKNOWN in ternary logic."""
    
    def __init__(self, operand: Any):
        self.operand = operand
    
    def accept(self, visitor):
        return visitor.visit_ternary_maybe_true(self)

class TernaryMaybeFalseNode(ExpressionNode):
    """Check if value is FALSE or UNKNOWN in ternary logic."""
    
    def __init__(self, operand: Any):
        self.operand = operand
    
    def accept(self, visitor):
        return visitor.visit_ternary_maybe_false(self)

# ========================================
# Basic Nodes
# ========================================

class ColumnNode(ExpressionNode):
    """Column reference node."""
    
    def __init__(self, name: str):
        self.name = name
    
    def accept(self, visitor):
        return visitor.visit_column(self)

class LiteralNode(ExpressionNode):
    """Literal value node."""
    
    def __init__(self, value: Any):
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_literal(self)
```

## Visitor with Logic+Operator Method Binding

Each operator+logic combination gets its own visitor method, handling the semantic differences between logic types.

```python
# core/visitor/base.py
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..expression_system.base import ExpressionSystem
    from ..expression_system.parameter import ExpressionParameter
    from ..logic.nodes import *

class ExpressionVisitor(ABC):
    """
    Base visitor with logic+operator method binding.
    
    Each (logic_type, expression_type) combination has its own method,
    handling the semantic differences between boolean and ternary logic.
    """
    
    def __init__(self, expression_system: 'ExpressionSystem'):
        self.expression_system = expression_system
    
    # ========================================
    # Boolean Logic Visitors
    # ========================================
    
    @abstractmethod
    def visit_boolean_logical_and(self, node: 'BooleanLogicalAndNode') -> Any:
        """Visit boolean AND node: NULLs treated as False."""
        pass
    
    @abstractmethod
    def visit_boolean_logical_or(self, node: 'BooleanLogicalOrNode') -> Any:
        """Visit boolean OR node: NULLs treated as False."""
        pass
    
    # ========================================
    # Boolean Comparison Visitors
    # ========================================
    
    @abstractmethod
    def visit_boolean_comparison_eq(self, node: 'BooleanComparisonEqNode') -> Any:
        """Visit boolean equality comparison: NULLs treated as False."""
        pass
    
    @abstractmethod
    def visit_boolean_comparison_ne(self, node: 'BooleanComparisonNeNode') -> Any:
        """Visit boolean inequality comparison: NULLs treated as False."""
        pass
    
    @abstractmethod
    def visit_boolean_comparison_gt(self, node: 'BooleanComparisonGtNode') -> Any:
        """Visit boolean greater-than comparison: NULLs treated as False."""
        pass
    
    @abstractmethod
    def visit_boolean_comparison_lt(self, node: 'BooleanComparisonLtNode') -> Any:
        """Visit boolean less-than comparison: NULLs treated as False."""
        pass
    
    @abstractmethod
    def visit_boolean_comparison_ge(self, node: 'BooleanComparisonGeNode') -> Any:
        """Visit boolean greater-than-or-equal comparison: NULLs treated as False."""
        pass
    
    @abstractmethod
    def visit_boolean_comparison_le(self, node: 'BooleanComparisonLeNode') -> Any:
        """Visit boolean less-than-or-equal comparison: NULLs treated as False."""
        pass
    
    @abstractmethod
    def visit_boolean_comparison_in(self, node: 'BooleanComparisonInNode') -> Any:
        """Visit boolean membership test: NULLs treated as False."""
        pass
    
    @abstractmethod
    def visit_boolean_comparison_is_null(self, node: 'BooleanComparisonIsNullNode') -> Any:
        """Visit boolean null check."""
        pass
    
    @abstractmethod
    def visit_boolean_comparison_is_not_null(self, node: 'BooleanComparisonIsNotNullNode') -> Any:
        """Visit boolean not-null check."""
        pass
    
    # ========================================
    # Ternary Logic Visitors  
    # ========================================
    
    @abstractmethod
    def visit_ternary_logical_and(self, node: 'TernaryLogicalAndNode') -> Any:
        """Visit ternary AND node: NULL-aware Kleene logic."""
        pass
    
    @abstractmethod
    def visit_ternary_logical_or(self, node: 'TernaryLogicalOrNode') -> Any:
        """Visit ternary OR node: NULL-aware Kleene logic.""" 
        pass
    
    # ========================================
    # Ternary Comparison Visitors
    # ========================================
    
    @abstractmethod
    def visit_ternary_comparison_eq(self, node: 'TernaryComparisonEqNode') -> Any:
        """Visit ternary equality comparison: NULL-aware with propagation."""
        pass
    
    @abstractmethod
    def visit_ternary_comparison_ne(self, node: 'TernaryComparisonNeNode') -> Any:
        """Visit ternary inequality comparison: NULL-aware with propagation."""
        pass
    
    @abstractmethod
    def visit_ternary_comparison_gt(self, node: 'TernaryComparisonGtNode') -> Any:
        """Visit ternary greater-than comparison: NULL-aware with propagation."""
        pass
    
    @abstractmethod
    def visit_ternary_comparison_lt(self, node: 'TernaryComparisonLtNode') -> Any:
        """Visit ternary less-than comparison: NULL-aware with propagation."""
        pass
    
    @abstractmethod
    def visit_ternary_comparison_ge(self, node: 'TernaryComparisonGeNode') -> Any:
        """Visit ternary greater-than-or-equal comparison: NULL-aware with propagation."""
        pass
    
    @abstractmethod
    def visit_ternary_comparison_le(self, node: 'TernaryComparisonLeNode') -> Any:
        """Visit ternary less-than-or-equal comparison: NULL-aware with propagation."""
        pass
    
    @abstractmethod
    def visit_ternary_comparison_in(self, node: 'TernaryComparisonInNode') -> Any:
        """Visit ternary membership test: NULL-aware with propagation."""
        pass
    
    @abstractmethod
    def visit_ternary_comparison_is_null(self, node: 'TernaryComparisonIsNullNode') -> Any:
        """Visit ternary null check (equivalent to boolean)."""
        pass
    
    @abstractmethod
    def visit_ternary_comparison_is_not_null(self, node: 'TernaryComparisonIsNotNullNode') -> Any:
        """Visit ternary not-null check (equivalent to boolean)."""
        pass
    
    # ========================================
    # Logic-Agnostic Operations
    # ========================================
    
    @abstractmethod
    def visit_logical_not(self, node: 'LogicalNotNode') -> Any:
        """Visit logical NOT node."""
        pass
    
    @abstractmethod
    def visit_logical_xor(self, node: 'LogicalXorNode') -> Any:
        """Visit logical XOR node."""
        pass
    
    # ========================================
    # Ternary Logic Visitors (Optional)
    # ========================================
    
    def visit_ternary_is_unknown(self, node: 'TernaryIsUnknownNode') -> Any:
        """Visit ternary is-unknown check node."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support ternary logic")
    
    def visit_ternary_is_known(self, node: 'TernaryIsKnownNode') -> Any:
        """Visit ternary is-known check node."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support ternary logic")
    
    def visit_ternary_maybe_true(self, node: 'TernaryMaybeTrueNode') -> Any:
        """Visit ternary maybe-true check node."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support ternary logic")
    
    def visit_ternary_maybe_false(self, node: 'TernaryMaybeFalseNode') -> Any:
        """Visit ternary maybe-false check node."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support ternary logic")
    
    # ========================================
    # Basic Node Visitors
    # ========================================
    
    @abstractmethod
    def visit_column(self, node: 'ColumnNode') -> Any:
        """Visit column reference node."""
        pass
    
    @abstractmethod
    def visit_literal(self, node: 'LiteralNode') -> Any:
        """Visit literal value node."""
        pass
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _process_operand(self, operand: Any) -> Any:
        """
        Process any operand through ExpressionParameter.
        
        This centralized method handles all type dispatch,
        converting any input to a native backend expression.
        """
        from ..expression_system.parameter import ExpressionParameter
        param = ExpressionParameter(operand, self.expression_system, self)
        return param.to_native_expression()
    
    def _process_operands(self, operands: List[Any]) -> List[Any]:
        """Process multiple operands."""
        return [self._process_operand(op) for op in operands]
```

## Self-Organizing Expression System

The expression system is self-organizing through type protocols, with no "optimization" classes or magical thinking.

```python
# core/expression_system/base.py
from abc import ABC, abstractmethod
from typing import Any, Type

class ExpressionSystem(ABC):
    """
    Self-organizing expression system based on type protocols.
    
    No "optimization" classes or caching layers - efficiency
    emerges naturally from type-based dispatch and backend
    implementations.
    """
    
    # ========================================
    # Backend Information
    # ========================================
    
    @abstractmethod
    def get_backend_name(self) -> str:
        """Return human-readable backend name."""
        pass
    
    @abstractmethod
    def get_native_type(self) -> Type:
        """Return the native expression type for this backend."""
        pass
    
    @abstractmethod
    def is_native_expression(self, obj: Any) -> bool:
        """Check if object is a native expression for this backend."""
        pass
    
    # ========================================
    # Expression Creation
    # ========================================
    
    @abstractmethod
    def col(self, name: str) -> Any:
        """Create column reference in native format."""
        pass
    
    @abstractmethod
    def lit(self, value: Any) -> Any:
        """Create literal value in native format."""
        pass
    
    # ========================================
    # Boolean Operations (Native)
    # ========================================
    
    @abstractmethod
    def native_and(self, left: Any, right: Any) -> Any:
        """Native AND operation."""
        pass
    
    @abstractmethod
    def native_or(self, left: Any, right: Any) -> Any:
        """Native OR operation."""
        pass
    
    @abstractmethod
    def native_not(self, expr: Any) -> Any:
        """Native NOT operation."""
        pass
    
    @abstractmethod
    def native_xor(self, left: Any, right: Any) -> Any:
        """Native XOR operation."""
        pass
    
    # ========================================
    # Comparison Operations (Native)
    # ========================================
    
    @abstractmethod
    def native_eq(self, left: Any, right: Any) -> Any:
        """Native equality comparison."""
        pass
    
    @abstractmethod
    def native_ne(self, left: Any, right: Any) -> Any:
        """Native inequality comparison."""
        pass
    
    @abstractmethod
    def native_gt(self, left: Any, right: Any) -> Any:
        """Native greater-than comparison."""
        pass
    
    @abstractmethod
    def native_lt(self, left: Any, right: Any) -> Any:
        """Native less-than comparison."""
        pass
    
    @abstractmethod
    def native_ge(self, left: Any, right: Any) -> Any:
        """Native greater-than-or-equal comparison."""
        pass
    
    @abstractmethod
    def native_le(self, left: Any, right: Any) -> Any:
        """Native less-than-or-equal comparison."""
        pass
    
    @abstractmethod
    def native_in(self, value: Any, collection: Any) -> Any:
        """Native membership test."""
        pass
    
    @abstractmethod
    def native_is_null(self, expr: Any) -> Any:
        """Native null check."""
        pass
    
    @abstractmethod
    def native_is_not_null(self, expr: Any) -> Any:
        """Native not-null check."""
        pass
    
    # ========================================
    # Ternary Logic Operations (Optional)
    # ========================================
    
    def supports_ternary(self) -> bool:
        """Check if backend supports ternary logic."""
        return hasattr(self, 'native_ternary_and')
    
    def native_ternary_and(self, left: Any, right: Any) -> Any:
        """Native ternary AND operation: NULL-aware Kleene logic."""
        raise NotImplementedError(f"{self.get_backend_name()} does not support ternary logic")
    
    def native_ternary_or(self, left: Any, right: Any) -> Any:
        """Native ternary OR operation: NULL-aware Kleene logic."""
        raise NotImplementedError(f"{self.get_backend_name()} does not support ternary logic")
    
    def native_ternary_not(self, expr: Any) -> Any:
        """Native ternary NOT operation: NULL-aware."""
        raise NotImplementedError(f"{self.get_backend_name()} does not support ternary logic")
    
    # ========================================
    # Ternary Comparison Operations (Optional)
    # ========================================
    
    def native_ternary_eq(self, left: Any, right: Any) -> Any:
        """Native ternary equality: NULL-aware with propagation."""
        raise NotImplementedError(f"{self.get_backend_name()} does not support ternary comparisons")
    
    def native_ternary_ne(self, left: Any, right: Any) -> Any:
        """Native ternary inequality: NULL-aware with propagation."""
        raise NotImplementedError(f"{self.get_backend_name()} does not support ternary comparisons")
    
    def native_ternary_gt(self, left: Any, right: Any) -> Any:
        """Native ternary greater-than: NULL-aware with propagation."""
        raise NotImplementedError(f"{self.get_backend_name()} does not support ternary comparisons")
    
    def native_ternary_lt(self, left: Any, right: Any) -> Any:
        """Native ternary less-than: NULL-aware with propagation."""
        raise NotImplementedError(f"{self.get_backend_name()} does not support ternary comparisons")
    
    def native_ternary_ge(self, left: Any, right: Any) -> Any:
        """Native ternary greater-than-or-equal: NULL-aware with propagation."""
        raise NotImplementedError(f"{self.get_backend_name()} does not support ternary comparisons")
    
    def native_ternary_le(self, left: Any, right: Any) -> Any:
        """Native ternary less-than-or-equal: NULL-aware with propagation."""
        raise NotImplementedError(f"{self.get_backend_name()} does not support ternary comparisons")
    
    def native_ternary_in(self, value: Any, collection: Any) -> Any:
        """Native ternary membership test: NULL-aware with propagation."""
        raise NotImplementedError(f"{self.get_backend_name()} does not support ternary comparisons")
```

## Universal Visitor Implementation

With ExpressionParameter handling all type dispatch, the universal visitor implementation becomes clean while supporting all logic types:

```python
# core/visitor/universal_visitor.py
from .base import ExpressionVisitor

class UniversalExpressionVisitor(ExpressionVisitor):
    """
    Universal visitor supporting all logic types for any backend.
    
    All type dispatch is handled by ExpressionParameter,
    leaving visitor methods clean and focused on logic semantics.
    """
    
    # ========================================
    # Boolean Logic Operations
    # ========================================
    
    def visit_boolean_logical_and(self, node):
        """Boolean AND: NULLs treated as False."""
        if len(node.operands) < 2:
            raise ValueError("AND requires at least 2 operands")
        
        # Process all operands through ExpressionParameter
        native_operands = self._process_operands(node.operands)
        
        # Chain boolean AND operations - NULLs become False
        result = native_operands[0]
        for operand in native_operands[1:]:
            result = self.expression_system.native_and(result, operand)
        
        return result
    
    def visit_boolean_logical_or(self, node):
        """Boolean OR: NULLs treated as False."""
        if len(node.operands) < 2:
            raise ValueError("OR requires at least 2 operands")
        
        native_operands = self._process_operands(node.operands)
        
        result = native_operands[0]
        for operand in native_operands[1:]:
            result = self.expression_system.native_or(result, operand)
        
        return result
    
    # ========================================
    # Boolean Comparison Operations  
    # ========================================
    
    def visit_boolean_comparison_eq(self, node):
        """Boolean equality: NULLs treated as False."""
        left = self._process_operand(node.left)
        right = self._process_operand(node.right)
        return self.expression_system.native_eq(left, right)
    
    def visit_boolean_comparison_gt(self, node):
        """Boolean greater-than: NULLs treated as False."""
        left = self._process_operand(node.left)
        right = self._process_operand(node.right)
        return self.expression_system.native_gt(left, right)
    
    def visit_boolean_comparison_is_null(self, node):
        """Boolean null check."""
        operand = self._process_operand(node.operand)
        return self.expression_system.native_is_null(operand)
    
    # ========================================
    # Ternary Logic Operations
    # ========================================
    
    def visit_ternary_logical_and(self, node):
        """Ternary AND: NULL-aware Kleene logic."""
        if len(node.operands) < 2:
            raise ValueError("AND requires at least 2 operands")
        
        native_operands = self._process_operands(node.operands)
        
        # Chain ternary AND operations - NULL-aware
        result = native_operands[0]
        for operand in native_operands[1:]:
            result = self.expression_system.native_ternary_and(result, operand)
        
        return result
    
    def visit_ternary_logical_or(self, node):
        """Ternary OR: NULL-aware Kleene logic."""
        if len(node.operands) < 2:
            raise ValueError("OR requires at least 2 operands")
        
        native_operands = self._process_operands(node.operands)
        
        result = native_operands[0]
        for operand in native_operands[1:]:
            result = self.expression_system.native_ternary_or(result, operand)
        
        return result
    
    # ========================================
    # Ternary Comparison Operations
    # ========================================
    
    def visit_ternary_comparison_eq(self, node):
        """Ternary equality: NULL-aware with propagation."""
        left = self._process_operand(node.left)
        right = self._process_operand(node.right)
        return self.expression_system.native_ternary_eq(left, right)
    
    def visit_ternary_comparison_gt(self, node):
        """Ternary greater-than: NULL-aware with propagation."""
        left = self._process_operand(node.left)
        right = self._process_operand(node.right)
        return self.expression_system.native_ternary_gt(left, right)
    
    def visit_ternary_comparison_is_null(self, node):
        """Ternary null check (same as boolean)."""
        operand = self._process_operand(node.operand)
        return self.expression_system.native_is_null(operand)
    
    # ========================================
    # Logic-Agnostic Operations
    # ========================================
    
    def visit_logical_not(self, node):
        """Logic-agnostic NOT implementation."""
        operand = self._process_operand(node.operand)
        return self.expression_system.native_not(operand)
    
    def visit_logical_xor(self, node):
        """Logic-agnostic XOR implementation."""
        left = self._process_operand(node.left)
        right = self._process_operand(node.right)
        return self.expression_system.native_xor(left, right)
    
    # ========================================
    # Basic Nodes
    # ========================================
    
    def visit_column(self, node):
        """Direct column reference."""
        return self.expression_system.col(node.name)
    
    def visit_literal(self, node):
        """Direct literal value."""
        return self.expression_system.lit(node.value)
```

## Benefits of Refined Architecture

### 1. Clean Separation of Concerns
- **ExpressionParameter**: Handles ALL type dispatch
- **ExpressionSystem**: Provides backend operations
- **Visitor**: Traverses tree and orchestrates conversion
- **Nodes**: Represent operations with no logic

### 2. Extensibility
- Add new operators: Create node type and visitor method
- Add new parameter types: Extend ExpressionParameter
- Add new backends: Implement ExpressionSystem interface
- Add new logic types: Create new visitor class

### 3. No Magical Thinking
- No "OptimizedExpressionSystem" classes
- No hidden caching layers
- No premature optimization
- Efficiency emerges from clean type dispatch

### 4. Type Safety
- Strong typing throughout
- Clear parameter type detection
- Explicit conversion paths
- Good error messages

### 5. Testability
- Each component can be tested in isolation
- ExpressionParameter tests type detection
- ExpressionSystem tests backend operations
- Visitor tests traversal logic
- Integration tests verify full pipeline

## Example Usage

### Creating Logic-Specific Expression Trees

```python
# Boolean logic expression: NULLs treated as False throughout
boolean_expression = BooleanLogicalAndNode([
    BooleanComparisonGtNode(ColumnNode("age"), 25),       # age > 25, NULL age → False
    BooleanComparisonEqNode("status", "active"),          # status == "active", NULL status → False
    BooleanLogicalOrNode([
        BooleanComparisonIsNullNode("premium"),           # premium IS NULL
        BooleanComparisonInNode(ColumnNode("tier"), [1, 2, 3])  # tier IN [1,2,3], NULL tier → False
    ])
])

# Ternary logic expression: Users get NULL-aware semantics automatically
ternary_expression = TernaryLogicalAndNode([
    TernaryComparisonGtNode(ColumnNode("age"), 25),       # age > 25 OR age IS NULL → NULL
    TernaryComparisonEqNode("status", "active"),          # status == "active" OR status IS NULL → NULL
    TernaryLogicalOrNode([
        TernaryComparisonIsNullNode("premium"),           # premium IS NULL
        TernaryComparisonInNode(ColumnNode("tier"), [1, 2, 3])  # tier IN [1,2,3] OR tier IS NULL → NULL
    ])
])
```

### Backend Compilation

```python
# Create backend systems
narwhals_system = NarwhalsExpressionSystem()
polars_system = PolarsExpressionSystem()
ibis_system = IbisExpressionSystem()

# Create universal visitor for each backend
narwhals_visitor = UniversalExpressionVisitor(narwhals_system)
polars_visitor = UniversalExpressionVisitor(polars_system)
ibis_visitor = UniversalExpressionVisitor(ibis_system)

# Boolean logic compilation across all backends
boolean_narwhals = boolean_expression.accept(narwhals_visitor)
boolean_polars = boolean_expression.accept(polars_visitor)
boolean_ibis = boolean_expression.accept(ibis_visitor)

# Ternary logic compilation across all backends
ternary_narwhals = ternary_expression.accept(narwhals_visitor)
ternary_polars = ternary_expression.accept(polars_visitor)
ternary_ibis = ternary_expression.accept(ibis_visitor)

# ExpressionParameter handles all the type dispatch automatically!
# Same visitor works with all backends - true backend orthogonality!
```

### Key Architectural Benefits

```python
# 1. Explicit logic semantics
BooleanComparisonGtNode(col("age"), 25)   # Clear: NULLs become False
TernaryComparisonGtNode(col("age"), 25)   # Clear: NULL-aware with propagation

# 2. Automatic NULL handling in ternary logic
# Boolean: Manual NULL handling required
BooleanLogicalOrNode([
    BooleanComparisonGtNode(col("age"), 25),
    BooleanComparisonIsNullNode(col("age"))  # Explicit NULL check
])

# Ternary: Automatic NULL handling
TernaryComparisonGtNode(col("age"), 25)  # Automatically returns NULL for NULL age

# 3. Backend independence with logic preservation
same_expression = TernaryLogicalAndNode([...])

# Same semantic meaning across all backends
narwhals_result = same_expression.accept(UniversalVisitor(NarwhalsExpressionSystem()))
polars_result = same_expression.accept(UniversalVisitor(PolarsExpressionSystem()))
ibis_result = same_expression.accept(UniversalVisitor(IbisExpressionSystem()))
```

This refined architecture provides a clean, extensible, and maintainable foundation for the universal expression system.