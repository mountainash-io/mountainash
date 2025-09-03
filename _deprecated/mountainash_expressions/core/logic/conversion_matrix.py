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

from typing import Dict, Callable, List
from abc import ABC, abstractmethod

from . import ExpressionNode, LiteralExpressionNode, ColumnExpressionNode, LogicalExpressionNode
from .expression_converter import ExpressionConverter
from .ternary.ternary_nodes import TernaryLiteralExpressionNode, TernaryColumnExpressionNode, TernaryLogicalExpressionNode
from ..constants import CONST_EXPRESSION_LOGIC_OPERATORS, CONST_LOGIC_TYPES



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
        if hasattr(node, 'logic_type') and node.logic_type == CONST_LOGIC_TYPES.TERNARY:
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
            if hasattr(operand, 'logic_type') and operand.logic_type == CONST_LOGIC_TYPES.BOOLEAN:
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
        if hasattr(node, 'logic_type') and node.logic_type == CONST_LOGIC_TYPES.BOOLEAN:
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
            if hasattr(operand, 'logic_type') and operand.logic_type == CONST_LOGIC_TYPES.TERNARY:
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
        from .boolean.boolean_nodes import BooleanLiteralExpressionNode
        return BooleanLiteralExpressionNode(
            operator=node.operator,
            value1=node.value1,
            value2=node.value2
        )

    def _convert_column_expression(self, node):
        """Convert ternary column operations to boolean (UNKNOWN→FALSE)."""
        # Import here to avoid circular imports
        from .boolean.boolean_nodes import BooleanColumnExpressionNode
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
        from .boolean.boolean_nodes import BooleanLogicalExpressionNode

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
        if node.logic_type == CONST_LOGIC_TYPES.TERNARY:
            return node
        elif node.logic_type == CONST_LOGIC_TYPES.BOOLEAN:
            return self.boolean_to_ternary.convert_node(node)

        # Default: try boolean to ternary conversion
        return self.boolean_to_ternary.convert_node(node)

    def convert_to_boolean(self, node: ExpressionNode) -> ExpressionNode:
        """Convert any expression node to boolean logic type."""
        if node.logic_type == CONST_LOGIC_TYPES.BOOLEAN:
            return node
        elif node.logic_type == CONST_LOGIC_TYPES.TERNARY:
            return self.ternary_to_boolean.convert_node(node)

        # Default: try ternary to boolean conversion
        return self.ternary_to_boolean.convert_node(node)

    def convert_to_target_type(self, node: ExpressionNode, target_logic_type: str) -> ExpressionNode:
        """Convert expression node to specified target logic type."""
        if target_logic_type == CONST_LOGIC_TYPES.TERNARY:
            return self.convert_to_ternary(node)
        elif target_logic_type == CONST_LOGIC_TYPES.BOOLEAN:
            return self.convert_to_boolean(node)
        else:
            raise ValueError(f"Unknown target logic type: {target_logic_type}")


# Global conversion instance for use throughout the system
GLOBAL_CONVERSION_MATRIX = ConversionMatrix()


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
        return CONST_LOGIC_TYPES.TERNARY

    def can_convert_from(self, source_logic_type: str) -> bool:
        """Check if conversion from source logic type is supported."""
        return source_logic_type == CONST_LOGIC_TYPES.BOOLEAN

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
