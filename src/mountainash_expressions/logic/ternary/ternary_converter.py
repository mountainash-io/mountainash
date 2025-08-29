"""
Ternary logic type converter.

This module provides conversion from other logic types (e.g., boolean) to ternary logic.
The converter handles the structural transformation of expression nodes while preserving
the original data values and operation semantics.
"""

from typing import Any
from ..core import ExpressionNode, LiteralExpressionNode, ColumnExpressionNode, LogicalExpressionNode
from ..core import ExpressionConverter
from .ternary_nodes import TernaryLiteralExpressionNode, TernaryColumnExpressionNode, TernaryLogicalExpressionNode


class TernaryLogicTypeConverter(ExpressionConverter):
    """Converter that transforms expression nodes to ternary logic type.

    This converter can transform boolean expressions (and potentially other logic types)
    to ternary expressions. It preserves the original data values and operations,
    only changing the expression node type and logic classification.

    Key principles:
    - Values are preserved as-is (no boolean-to-ternary value conversion)
    - Logic evaluation happens at execution time, not during conversion
    - Structural transformation only (node type changes)
    - No recursive conversion (operands convert themselves just-in-time)
    """

    @property
    def target_logic_type(self) -> str:
        """Target logic type for this converter."""
        return "ternary"

    def can_convert_from(self, source_logic_type: str) -> bool:
        """Check if conversion from source logic type is supported.

        Args:
            source_logic_type: Source logic type to convert from

        Returns:
            True if conversion is supported
        """
        # Currently supports conversion from boolean logic
        return source_logic_type == "boolean"

    def convert(self, expression_node: ExpressionNode) -> ExpressionNode:
        """Convert expression node to ternary logic type.

        Args:
            expression_node: Expression node to convert

        Returns:
            Converted ternary expression node

        Raises:
            ValueError: If expression type is not supported for conversion
        """
        if not hasattr(expression_node, 'expression_type'):
            raise ValueError(f"Expression node missing expression_type attribute: {type(expression_node)}")

        if expression_node.expression_type == "literal":
            return self.convert_literal(expression_node)
        elif expression_node.expression_type == "column":
            return self.convert_column(expression_node)
        elif expression_node.expression_type == "logical":
            return self.convert_logical(expression_node)
        else:
            raise ValueError(f"Unknown expression type for conversion: {expression_node.expression_type}")

    def convert_literal(self, literal_node: LiteralExpressionNode) -> TernaryLiteralExpressionNode:
        """Convert literal expression to ternary logic type.

        Values are preserved as-is since they represent data values or column references,
        not logical truth values. Logic evaluation happens at execution time.

        Args:
            literal_node: Literal expression node to convert

        Returns:
            Ternary literal expression node
        """
        return TernaryLiteralExpressionNode(
            value1=literal_node.value1,
            operator=literal_node.operator,
            value2=literal_node.value2
        )

    def convert_column(self, column_node: ColumnExpressionNode) -> TernaryColumnExpressionNode:
        """Convert column expression to ternary logic type.

        Column names and comparison values are preserved as-is since they represent
        data references and values, not logical truth values.

        Args:
            column_node: Column expression node to convert

        Returns:
            Ternary column expression node
        """
        return TernaryColumnExpressionNode(
            column=column_node.column,
            operator=column_node.operator,
            value=getattr(column_node, 'value', None),
            compare_column=getattr(column_node, 'compare_column', None)
        )

    def convert_logical(self, logical_node: LogicalExpressionNode) -> TernaryLogicalExpressionNode:
        """Convert logical expression to ternary logic type.

        Operands are preserved as-is since they will convert themselves on a
        just-in-time basis when visited. No recursive conversion needed.

        Args:
            logical_node: Logical expression node to convert

        Returns:
            Ternary logical expression node
        """
        return TernaryLogicalExpressionNode(
            operator=logical_node.operator,
            operands=logical_node.operands
        )
