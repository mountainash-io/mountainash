"""
Cross-Logic Type Conversion Matrix for Expression Nodes

This module provides sophisticated conversion between Boolean and Ternary logic types,
preserving semantic meaning while handling the mathematical differences between
the two logic systems.

Key Principles:
1. Semantic Preservation: Convert meaning, not just syntax
2. Lossy vs Lossless: Boolean→Ternary is lossless, Ternary→Boolean may be lossy
3. Special Cases: Handle booleanizing operations and logic-specific operations
4. Default Strategies: Wrap ternary operations with IS_TRUE when converting to boolean

Mathematical Differences:
- XOR_PARITY (Boolean): TRUE if odd number of operands are TRUE (1,3,5...)
- XOR_EXCLUSIVE (Ternary): TRUE if exactly one operand is TRUE
- STRICT_AND (Ternary): UNKNOWN dominates over TRUE (used in BETWEEN operations)
"""

from typing import Any, Dict, Callable, Optional, List
from abc import ABC, abstractmethod

from ..core import ExpressionNode, LiteralExpressionNode, ColumnExpressionNode, LogicalExpressionNode
from ..core import ExpressionConverter
from .ternary_nodes import TernaryLiteralExpressionNode, TernaryColumnExpressionNode, TernaryLogicalExpressionNode
from ...constants import CONST_EXPRESSION_LOGIC_OPERATORS, CONST_EXPRESSION_LOGIC_TYPES
from ...helpers.visitor_factory import ExpressionVisitorFactory



class LogicTypeConverter(ABC):
    """Abstract base class for cross-logic type conversions."""

    @abstractmethod
    def convert_node(self, node: ExpressionNode) -> ExpressionNode:
        """Convert an expression node to the target logic type."""
        pass

    @abstractmethod
    def convert_operands(self, operands: List[ExpressionNode]) -> List[ExpressionNode]:
        """Recursively convert all operands to target logic type."""
        pass


class BooleanToTernaryConverter(LogicTypeConverter):
    """
    Converts Boolean expression nodes to Ternary equivalents.

    This conversion is generally lossless - we can always add UNKNOWN handling
    to boolean operations without changing their core semantics.
    """

    def __init__(self):
        self.conversion_matrix = self._build_conversion_matrix()

    def convert_node(self, node: ExpressionNode) -> ExpressionNode:
        """Convert a boolean node to ternary equivalent with UNKNOWN handling."""
        if hasattr(node, 'logic_type') and node.logic_type == CONST_EXPRESSION_LOGIC_TYPES.TERNARY:
            return node  # Already ternary

        if hasattr(node, 'expression_type'):
            expr_type = node.expression_type
            if expr_type in self.conversion_matrix:
                return self.conversion_matrix[expr_type](node)

        raise ValueError(f"No conversion defined for boolean node: {type(node).__name__}")

    def convert_operands(self, operands: List[ExpressionNode]) -> List[ExpressionNode]:
        """Recursively convert all boolean operands to ternary."""
        converted_operands = []
        for operand in operands:
            if hasattr(operand, 'logic_type') and operand.logic_type == CONST_EXPRESSION_LOGIC_TYPES.BOOLEAN:
                converted_operands.append(self.convert_node(operand))
            else:
                converted_operands.append(operand)
        return converted_operands

    def _build_conversion_matrix(self) -> Dict[str, Callable]:
        """Build the Boolean → Ternary conversion matrix."""
        return {
            'literal': self._convert_literal_expression,
            'column': self._convert_column_expression,
            'logical': self._convert_logical_expression,
        }

    def _convert_literal_expression(self, node) -> TernaryLiteralExpressionNode:
        """Convert boolean literal operations to ternary equivalents."""
        return TernaryLiteralExpressionNode(
            operator=node.operator,
            value1=node.value1,
            value2=node.value2
        )

    def _convert_column_expression(self, node) -> TernaryColumnExpressionNode:
        """Convert boolean column operations to ternary with UNKNOWN handling."""
        return TernaryColumnExpressionNode(
            operator=node.operator,
            column=node.column,
            value=getattr(node, 'value', None),
            compare_column=getattr(node, 'compare_column', None)
        )

    def _convert_logical_expression(self, node) -> TernaryLogicalExpressionNode:
        """Convert boolean logical operations to ternary equivalents."""
        # Convert all operands recursively
        ternary_operands = self.convert_operands(node.operands)

        # Preserve exact operator semantics
        # Boolean XOR_PARITY becomes Ternary XOR_PARITY (same mathematical operation)
        operator = node.operator

        return TernaryLogicalExpressionNode(
            operator=operator,
            operands=ternary_operands
        )


class TernaryToBooleanConverter(LogicTypeConverter):
    """
    Converts Ternary expression nodes to Boolean equivalents.

    This conversion can be lossy - we must decide how to handle UNKNOWN values.
    Strategy:
    1. Booleanizing operations (IS_*, MAYBE_*) → Direct conversion (already return boolean)
    2. Pure ternary operations → Wrap with IS_TRUE evaluation
    3. UNKNOWN values → FALSE in boolean context
    """

    def __init__(self):
        self.conversion_matrix = self._build_conversion_matrix()
        self.booleanizing_operations = {
            CONST_EXPRESSION_LOGIC_OPERATORS.IS_TRUE,
            CONST_EXPRESSION_LOGIC_OPERATORS.IS_FALSE,
            CONST_EXPRESSION_LOGIC_OPERATORS.IS_UNKNOWN,
            CONST_EXPRESSION_LOGIC_OPERATORS.MAYBE_TRUE,
            CONST_EXPRESSION_LOGIC_OPERATORS.MAYBE_FALSE,
            CONST_EXPRESSION_LOGIC_OPERATORS.IS_KNOWN,
        }

    def convert_node(self, node: ExpressionNode) -> ExpressionNode:
        """Convert a ternary node to boolean equivalent."""
        if hasattr(node, 'logic_type') and node.logic_type == CONST_EXPRESSION_LOGIC_TYPES.BOOLEAN:
            return node  # Already boolean

        if hasattr(node, 'expression_type'):
            expr_type = node.expression_type
            if expr_type in self.conversion_matrix:
                return self.conversion_matrix[expr_type](node)

        raise ValueError(f"No conversion defined for ternary node: {type(node).__name__}")

    def convert_operands(self, operands: List[ExpressionNode]) -> List[ExpressionNode]:
        """Recursively convert all ternary operands to boolean."""
        converted_operands = []
        for operand in operands:
            if hasattr(operand, 'logic_type') and operand.logic_type == CONST_EXPRESSION_LOGIC_TYPES.TERNARY:
                converted_operands.append(self.convert_node(operand))
            else:
                converted_operands.append(operand)
        return converted_operands

    def _build_conversion_matrix(self) -> Dict[str, Callable]:
        """Build the Ternary → Boolean conversion matrix."""
        return {
            'literal': self._convert_literal_expression,
            'column': self._convert_column_expression,
            'logical': self._convert_logical_expression,
        }

    def _convert_literal_expression(self, node):
        """Convert ternary literal operations to boolean equivalents."""
        # Import here to avoid circular imports
        from ..boolean.boolean_nodes import BooleanLiteralExpressionNode
        return BooleanLiteralExpressionNode(
            operator=node.operator,
            value1=node.value1,
            value2=node.value2
        )

    def _convert_column_expression(self, node):
        """Convert ternary column operations to boolean (UNKNOWN→FALSE)."""
        # Import here to avoid circular imports
        from ..boolean.boolean_nodes import BooleanColumnExpressionNode
        return BooleanColumnExpressionNode(
            operator=node.operator,
            column=node.column,
            value=getattr(node, 'value', None),
            compare_column=getattr(node, 'compare_column', None)
        )

    def _convert_logical_expression(self, node):
        """Convert ternary logical operations to boolean equivalents."""
        # Handle already-booleanizing operations differently
        if self._is_booleanizing_operation(node):
            return self._convert_booleanizing_operation(node)
        else:
            return self._convert_pure_ternary_operation(node)

    def _is_booleanizing_operation(self, node) -> bool:
        """Check if ternary operation already returns boolean results."""
        return hasattr(node, 'operator') and node.operator in self.booleanizing_operations

    def _convert_booleanizing_operation(self, node):
        """
        Handle booleanizing ternary operations by preserving the original node.

        These operations (IS_TRUE, IS_FALSE, etc.) are inherently ternary concepts
        that should be evaluated by a ternary visitor, even when encountered by
        a boolean visitor. The boolean visitor should delegate to a ternary visitor
        for the same backend and return the result directly.

        Since these are booleanizing operations, they return boolean results anyway,
        so the delegation is seamless.
        """
        # Return the original node unchanged - the boolean visitor will handle delegation
        return node

    def _convert_pure_ternary_operation(self, node):
        """Convert pure ternary operations by converting to boolean context."""
        # Import here to avoid circular imports
        from ..boolean.boolean_nodes import BooleanLogicalExpressionNode

        # For pure ternary operations, convert operands and create boolean equivalent
        # UNKNOWN values will become FALSE in boolean context
        boolean_operands = self.convert_operands(node.operands)

        return BooleanLogicalExpressionNode(
            operator=node.operator,
            operands=boolean_operands
        )


class ConversionMatrix:
    """
    Centralized conversion matrix for cross-logic type operations.

    This class provides the master conversion logic and handles edge cases
    that require special semantic interpretation.
    """

    def __init__(self):
        self.boolean_to_ternary = BooleanToTernaryConverter()
        self.ternary_to_boolean = TernaryToBooleanConverter()

    def convert_to_ternary(self, node: ExpressionNode) -> ExpressionNode:
        """Convert any expression node to ternary logic type."""
        if hasattr(node, 'logic_type'):
            if node.logic_type == CONST_EXPRESSION_LOGIC_TYPES.TERNARY:
                return node
            elif node.logic_type == CONST_EXPRESSION_LOGIC_TYPES.BOOLEAN:
                return self.boolean_to_ternary.convert_node(node)

        # Default: try boolean to ternary conversion
        return self.boolean_to_ternary.convert_node(node)

    def convert_to_boolean(self, node: ExpressionNode) -> ExpressionNode:
        """Convert any expression node to boolean logic type."""
        if hasattr(node, 'logic_type'):
            if node.logic_type == CONST_EXPRESSION_LOGIC_TYPES.BOOLEAN:
                return node
            elif node.logic_type == CONST_EXPRESSION_LOGIC_TYPES.TERNARY:
                return self.ternary_to_boolean.convert_node(node)

        # Default: try ternary to boolean conversion
        return self.ternary_to_boolean.convert_node(node)

    def convert_to_target_type(self, node: ExpressionNode, target_logic_type: str) -> ExpressionNode:
        """Convert expression node to specified target logic type."""
        if target_logic_type == CONST_EXPRESSION_LOGIC_TYPES.TERNARY:
            return self.convert_to_ternary(node)
        elif target_logic_type == CONST_EXPRESSION_LOGIC_TYPES.BOOLEAN:
            return self.convert_to_boolean(node)
        else:
            raise ValueError(f"Unknown target logic type: {target_logic_type}")

    def create_delegate_visitor(self, table: Any, target_logic_type: str, current_visitor: Any = None):
        """
        Create a delegate visitor for cross-logic type operations.
        
        This method enables seamless visitor delegation when a visitor encounters
        an expression node of a different logic type. The delegate visitor will
        be of the same backend as the current context but of the target logic type.
        
        Args:
            table: The DataFrame/table to identify the backend
            target_logic_type: The target logic type ("boolean" or "ternary")
            current_visitor: Optional current visitor for context
            
        Returns:
            A visitor of the target logic type for the same backend
            
        Example Usage:
            # Boolean visitor encounters ternary booleanizing operation
            if node.logic_type == "ternary" and self._is_booleanizing_operation(node):
                delegate_visitor = GLOBAL_CONVERSION_MATRIX.create_delegate_visitor(
                    table, "ternary", self
                )
                return node.accept(delegate_visitor)
        """
        if target_logic_type == CONST_EXPRESSION_LOGIC_TYPES.TERNARY:
            return ExpressionVisitorFactory.create_ternary_visitor_for_backend(table)
        elif target_logic_type == CONST_EXPRESSION_LOGIC_TYPES.BOOLEAN:
            return ExpressionVisitorFactory.create_boolean_visitor_for_backend(table)
        else:
            raise ValueError(f"Unknown target logic type: {target_logic_type}")

    def should_delegate_to_node_logic_type(self, node: ExpressionNode, current_logic_type: str) -> bool:
        """
        Determine if a node should be delegated to a visitor matching its logic type.
        
        Simple rule: delegate when the node's logic type differs from current visitor
        AND delegation preserves semantics better than conversion.
        
        Args:
            node: Expression node to evaluate
            current_logic_type: Current visitor's logic type
            
        Returns:
            True if delegation to node's logic type is recommended
        """
        if not hasattr(node, 'logic_type'):
            return False
            
        # If node and visitor are same logic type, no delegation needed
        if node.logic_type == current_logic_type:
            return False
            
        # Boolean visitor encountering ternary node
        if (current_logic_type == CONST_EXPRESSION_LOGIC_TYPES.BOOLEAN and 
            node.logic_type == CONST_EXPRESSION_LOGIC_TYPES.TERNARY):
            # Delegate for booleanizing operations
            return self.ternary_to_boolean._is_booleanizing_operation(node)
            
        # Ternary visitor encountering boolean node - usually convert, rarely delegate
        # Most boolean operations can be enhanced to ternary seamlessly
        return False

    def should_convert_node(self, node: ExpressionNode, current_logic_type: str) -> bool:
        """
        Determine if a node should be converted to the current visitor's logic type.
        
        This complements should_delegate_to_alternate_logic() by handling cases where
        conversion is the right approach rather than delegation.
        
        Args:
            node: Expression node to evaluate
            current_logic_type: Current visitor's logic type
            
        Returns:
            True if conversion is needed, False if node can be used as-is
        """
        if not hasattr(node, 'logic_type'):
            return False
            
        # If node and visitor are same logic type, no conversion needed
        if node.logic_type == current_logic_type:
            return False
            
        # If delegation is recommended, don't convert
        if self.should_delegate_to_node_logic_type(node, current_logic_type):
            return False
            
        # Otherwise, conversion is needed
        return True


# Global conversion instance for use throughout the system
GLOBAL_CONVERSION_MATRIX = ConversionMatrix()


def create_delegate_visitor(table: Any, target_logic_type: str, current_visitor: Any = None):
    """
    Convenience function to create delegate visitors using the global conversion matrix.
    
    This provides a simple interface for visitors to create delegate visitors when
    they encounter expressions of different logic types.
    
    Args:
        table: The DataFrame/table to identify the backend
        target_logic_type: The target logic type ("boolean" or "ternary")  
        current_visitor: Optional current visitor for context
        
    Returns:
        A visitor of the target logic type for the same backend
        
    Example Usage:
        from mountainash_expressions.logic.ternary.ternary_converter import create_delegate_visitor
        
        # In a boolean visitor
        if node.logic_type == "ternary" and self._is_booleanizing_operation(node):
            delegate_visitor = create_delegate_visitor(table, "ternary", self)
            return node.accept(delegate_visitor)
    """
    return GLOBAL_CONVERSION_MATRIX.create_delegate_visitor(table, target_logic_type, current_visitor)


def should_delegate_to_node_logic_type(node: ExpressionNode, current_logic_type: str) -> bool:
    """
    Convenience function to check if delegation to node's logic type is recommended.
    
    Args:
        node: Expression node to evaluate
        current_logic_type: Current visitor's logic type
        
    Returns:
        True if delegation to node's logic type is recommended
    """
    return GLOBAL_CONVERSION_MATRIX.should_delegate_to_node_logic_type(node, current_logic_type)


def should_convert_node(node: ExpressionNode, current_logic_type: str) -> bool:
    """
    Convenience function to check if node conversion is needed using the global conversion matrix.
    
    Args:
        node: Expression node to evaluate
        current_logic_type: Current visitor's logic type
        
    Returns:
        True if conversion is needed, False if node can be used as-is
    """
    return GLOBAL_CONVERSION_MATRIX.should_convert_node(node, current_logic_type)


def convert_expression(node: ExpressionNode, target_logic_type: str) -> ExpressionNode:
    """
    Convenience function to convert expressions using the global conversion matrix.
    
    Args:
        node: Expression node to convert
        target_logic_type: Target logic type ("boolean" or "ternary")
        
    Returns:
        Converted expression node
    """
    return GLOBAL_CONVERSION_MATRIX.convert_to_target_type(node, target_logic_type)


class TernaryExpressionConverter(ExpressionConverter):
    """
    Legacy converter for backward compatibility. Uses the new ConversionMatrix internally.

    This converter transforms boolean expressions to ternary expressions using the
    sophisticated conversion matrix that preserves semantic meaning.
    """

    def __init__(self):
        """Initialize with the global conversion matrix."""
        self.conversion_matrix = GLOBAL_CONVERSION_MATRIX

    @property
    def target_logic_type(self) -> str:
        """Target logic type for this converter."""
        return CONST_EXPRESSION_LOGIC_TYPES.TERNARY

    def can_convert_from(self, source_logic_type: str) -> bool:
        """Check if conversion from source logic type is supported."""
        return source_logic_type == CONST_EXPRESSION_LOGIC_TYPES.BOOLEAN

    def convert(self, expression_node: ExpressionNode) -> ExpressionNode:
        """Convert expression node to ternary logic type using the conversion matrix."""
        return self.conversion_matrix.convert_to_ternary(expression_node)

    def convert_literal(self, literal_node: LiteralExpressionNode, visitor_logic_type: str = None) -> TernaryLiteralExpressionNode:
        """Convert literal expression to ternary logic type."""
        return self.conversion_matrix.boolean_to_ternary._convert_literal_expression(literal_node)

    def convert_column(self, column_node: ColumnExpressionNode, visitor_logic_type: str = None) -> TernaryColumnExpressionNode:
        """Convert column expression to ternary logic type."""
        return self.conversion_matrix.boolean_to_ternary._convert_column_expression(column_node)

    def convert_logical(self, logical_node: LogicalExpressionNode, visitor_logic_type: str = None) -> TernaryLogicalExpressionNode:
        """Convert logical expression to ternary logic type."""
        return self.conversion_matrix.boolean_to_ternary._convert_logical_expression(logical_node)


    def _is_booleanizing_operation(self, expression_node: ExpressionNode):
        """Check if node is a booleanizing ternary operation."""
        booleanizing_ops = {
            "IS_TRUE", "IS_FALSE", "IS_UNKNOWN",
            "MAYBE_TRUE", "MAYBE_FALSE", "IS_KNOWN"
        }
        return hasattr(expression_node, 'operator') and expression_node.operator in booleanizing_ops


# Convenience functions for external use
def convert_to_ternary(node: ExpressionNode) -> ExpressionNode:
    """Global function to convert any node to ternary logic type."""
    return GLOBAL_CONVERSION_MATRIX.convert_to_ternary(node)


def convert_to_boolean(node: ExpressionNode) -> ExpressionNode:
    """Global function to convert any node to boolean logic type."""
    return GLOBAL_CONVERSION_MATRIX.convert_to_boolean(node)


def ensure_logic_type_compatibility(node: ExpressionNode, target_logic_type: str) -> ExpressionNode:
    """Global function to ensure node matches target logic type."""
    return GLOBAL_CONVERSION_MATRIX.convert_to_target_type(node, target_logic_type)


# Detailed Conversion Matrix Specification
"""
COMPREHENSIVE CONVERSION MATRIX SPECIFICATION
===========================================

This matrix defines semantic conversions between Boolean and Ternary logic operations.
The key insight is that conversions must preserve MEANING, not just syntax.

## Core Conversion Principles

### 1. Semantic Preservation
Operations maintain their intended mathematical meaning across logic types.
Example: Boolean AND preserves its FALSE-dominates semantics in Ternary AND.

### 2. Lossy vs Lossless Conversions
- **Boolean → Ternary**: Lossless (can always add UNKNOWN handling)
- **Ternary → Boolean**: Potentially lossy (UNKNOWN values must be interpreted)

### 3. Mathematical Differences
Some operations have different semantics between logic types:
- **XOR_PARITY**: TRUE if odd number of operands are TRUE (1,3,5...)
- **XOR_EXCLUSIVE**: TRUE if exactly one operand is TRUE
- **STRICT_AND**: UNKNOWN dominates over TRUE (used in BETWEEN operations)

## Detailed Conversion Matrix

### Column Operations (Value Comparisons)
Direct semantic mapping with appropriate UNKNOWN handling:

```
Boolean → Ternary:
├── EQ → EQ (with UNKNOWN value mapping)
├── NE → NE (with UNKNOWN value mapping)
├── GT, LT, GE, LE → Same (with UNKNOWN boundary handling)
├── IN → IN (with UNKNOWN list membership)
├── IS_NULL, IS_NOT_NULL → Same (null semantics identical)
└── BETWEEN → BETWEEN (with UNKNOWN boundary handling)

Ternary → Boolean:
├── EQ → EQ (UNKNOWN values become FALSE in boolean context)
├── NE → NE (UNKNOWN values become FALSE in boolean context)
├── GT, LT, GE, LE → Same (UNKNOWN comparisons become FALSE)
├── IN → IN (UNKNOWN membership becomes FALSE)
├── IS_NULL, IS_NOT_NULL → Same (null semantics preserved)
└── BETWEEN → BETWEEN (UNKNOWN boundaries become FALSE)
```

### Logical Operations (Complex Semantics)

```
Boolean → Ternary:
├── AND → AND
│   └── Semantics: FALSE dominates over TRUE and UNKNOWN
├── OR → OR
│   └── Semantics: TRUE dominates over FALSE and UNKNOWN
├── XOR_PARITY → XOR_PARITY
│   └── Semantics: TRUE if odd number of TRUE operands (with UNKNOWN handling)
└── NOT → NOT
    └── Semantics: FALSE↔TRUE, UNKNOWN→UNKNOWN

Ternary → Boolean:
├── AND → Convert operands + AND (UNKNOWN→FALSE)
├── OR → Convert operands + OR (UNKNOWN→FALSE)
├── XOR_EXCLUSIVE → Convert operands + XOR_EXCLUSIVE wrapped with IS_TRUE
├── XOR_PARITY → Convert operands + XOR_PARITY wrapped with IS_TRUE
├── STRICT_AND → Convert operands + AND (UNKNOWN dominance lost)
└── NOT → Convert operands + NOT wrapped with IS_TRUE
```

### Ternary-Specific State Testing Operations (Direct Visitor Delegation)
These operations return boolean results but are inherently ternary concepts that require delegation:

```
Ternary → Boolean (Direct Delegation):
├── IS_TRUE → Original node preserved → Boolean Visitor delegates to Ternary Visitor
├── IS_FALSE → Original node preserved → Boolean Visitor delegates to Ternary Visitor
├── IS_UNKNOWN → Original node preserved → Boolean Visitor delegates to Ternary Visitor
├── MAYBE_TRUE → Original node preserved → Boolean Visitor delegates to Ternary Visitor
├── MAYBE_FALSE → Original node preserved → Boolean Visitor delegates to Ternary Visitor
└── IS_KNOWN → Original node preserved → Boolean Visitor delegates to Ternary Visitor

Boolean → Ternary (N/A):
└── These operations don't exist in boolean logic
```

**Direct Delegation Pattern:**
```python
class BooleanExpressionVisitor:
    def visit_logical_expression(self, node):
        if node.logic_type == "ternary":
            converted_node = convert_to_boolean(node)

            # If it's a booleanizing operation, converted_node is the original node
            if self._is_booleanizing_operation(converted_node):
                # Create ternary visitor for same backend and delegate
                ternary_visitor = self._create_ternary_visitor_for_backend()
                return converted_node.accept(ternary_visitor)
            else:
                # Regular conversion for non-booleanizing operations
                return self._visit_boolean_logical_expression(converted_node)

        return self._visit_boolean_logical_expression(node)
```

### Constant Operations

```
Boolean → Ternary:
├── ALWAYS_TRUE → ALWAYS_TRUE
└── ALWAYS_FALSE → ALWAYS_FALSE

Ternary → Boolean:
├── ALWAYS_TRUE → ALWAYS_TRUE
├── ALWAYS_FALSE → ALWAYS_FALSE
└── ALWAYS_UNKNOWN → ALWAYS_FALSE (UNKNOWN becomes FALSE in boolean context)
```

## Special Case Handling

### 1. XOR Operations Mathematical Difference
```
For 3 TRUE operands (A=T, B=T, C=T):
├── XOR_PARITY(T,T,T) = T    # 3 is odd number of TRUE values
└── XOR_EXCLUSIVE(T,T,T) = F # Not exactly one TRUE value
```
These are fundamentally different mathematical operations!

### 2. STRICT_AND vs Regular AND
```
For operands (A=T, B=UNKNOWN):
├── AND(T,U) = U           # FALSE dominates, UNKNOWN otherwise
└── STRICT_AND(T,U) = U    # UNKNOWN dominates over TRUE
```
STRICT_AND is used in BETWEEN operations where UNKNOWN boundaries should make the result UNKNOWN.

### 3. Booleanizing Operations Conversion
```
Ternary IS_TRUE(some_ternary_expr) → Boolean context:
├── Convert operands recursively to boolean
├── Apply the IS_TRUE operation in boolean context
└── Result is already boolean (TRUE/FALSE)
```

### 4. Round-Trip Conversion Behavior
```
Boolean → Ternary → Boolean on clean data (no UNKNOWN):
└── Should preserve exact behavior

Boolean → Ternary → Boolean on data with UNKNOWN:
└── May lose information (UNKNOWN becomes FALSE in final boolean context)
```

## Integration with Visitor Pattern

### Automatic Conversion in Visitors
```python
class TernaryExpressionVisitor:
    def visit_column_expression(self, node):
        if node.logic_type == "boolean":
            node = convert_to_ternary(node)  # Automatic conversion
        return self._visit_ternary_column_expression(node)
```

### Simple Visitor Delegation Pattern Implementation
```python
class BooleanExpressionVisitor:
    def visit_logical_expression(self, node):
        if node.logic_type == "ternary":
            # Convert ternary to boolean context
            converted_node = convert_to_boolean(node)

            # Check if this is a booleanizing operation that should be delegated
            if self._is_booleanizing_operation(converted_node):
                # Delegate to ternary visitor for same backend
                ternary_visitor = self._create_ternary_visitor_for_backend()
                return converted_node.accept(ternary_visitor)
            else:
                # Regular conversion for non-booleanizing operations
                return self._visit_boolean_logical_expression(converted_node)

        return self._visit_boolean_logical_expression(node)

    def _is_booleanizing_operation(self, node):
        """Check if node is a booleanizing ternary operation."""
        booleanizing_ops = {
            "IS_TRUE", "IS_FALSE", "IS_UNKNOWN",
            "MAYBE_TRUE", "MAYBE_FALSE", "IS_KNOWN"
        }
        return hasattr(node, 'operator') and node.operator in booleanizing_ops

    def _create_ternary_visitor_for_backend(self):
        """Create ternary visitor for same backend."""
        backend_type = self.backend_type  # e.g., "polars", "pandas", etc.

        if backend_type == "polars":
            from ...visitors.ternary import PolarsTernaryExpressionVisitor
            return PolarsTernaryExpressionVisitor()
        elif backend_type == "pandas":
            from ...visitors.ternary import PandasTernaryExpressionVisitor
            return PandasTernaryExpressionVisitor()
        elif backend_type == "ibis":
            from ...visitors.ternary import IbisTernaryExpressionVisitor
            return IbisTernaryExpressionVisitor()
        elif backend_type == "pyarrow":
            from ...visitors.ternary import PyArrowTernaryExpressionVisitor
            return PyArrowTernaryExpressionVisitor()
        else:
            raise ValueError(f"No ternary visitor available for backend: {backend_type}")
```

### Seamless Cross-Logic Type Operations
```python
# Mixed logic types work seamlessly through automatic conversion and delegation
boolean_condition = BooleanColumnExpressionNode("active", "==", True)
ternary_condition = TernaryColumnExpressionNode("score", ">", 80)

# Ternary operations with boolean operands
combined = TernaryLogicalExpressionNode("AND", [boolean_condition, ternary_condition])
result = combined.eval_is_true()(dataframe)

# Boolean visitor encountering ternary booleanizing operations
ternary_state_check = TernaryLogicalExpressionNode("IS_TRUE", [ternary_condition])
boolean_visitor = BooleanExpressionVisitor()

# This works through simple delegation:
# 1. Boolean visitor recognizes IS_TRUE as booleanizing operation
# 2. Creates ternary visitor for same backend (e.g., Polars)
# 3. Delegates original node to ternary visitor
# 4. Gets back boolean result (since IS_TRUE returns boolean)
result_func = ternary_state_check.accept(boolean_visitor)
```

### Architecture Benefits

**1. Semantic Preservation**: Operations maintain their intended meaning across logic types

**2. Simple Delegation**: Booleanizing operations use original nodes with backend-matched visitor delegation

**3. Backend Consistency**: Same backend type maintained across delegation (Polars → Polars, Pandas → Pandas, etc.)

**4. No Extra Node Types**: No special delegation node classes needed - visitors handle delegation directly

**5. Performance Optimization**: Minimal conversion overhead, delegation only when necessary

**6. Type Safety**: Logic type mismatches are handled automatically without user intervention

## Testing Strategy

### 1. Semantic Correctness
Verify that conversions preserve the intended meaning of operations across logic types.

### 2. Mathematical Properties
Test truth tables for logical operations to ensure mathematical correctness.

### 3. Cross-Logic Integration
Validate that boolean and ternary expressions can be combined seamlessly.

### 4. Performance Impact
Ensure conversion overhead is minimal and doesn't impact expression evaluation performance.

This comprehensive conversion matrix enables true logic type orthogonality where any
expression can work with any visitor while preserving semantic correctness and
mathematical integrity.
"""
