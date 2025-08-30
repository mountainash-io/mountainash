"""
Boolean logic type converter.

This module provides conversion from other logic types (e.g., ternary) to boolean logic.
The converter handles the structural transformation of expression nodes while preserving
the original data values and operation semantics.

Note: Converting from ternary to boolean is potentially lossy since ternary logic
includes UNKNOWN states that have no direct boolean equivalent.
"""

from .boolean_nodes import ExpressionNode, LiteralExpressionNode, ColumnExpressionNode, LogicalExpressionNode
from ..expression_converter import ExpressionConverter
from .boolean_nodes import BooleanLiteralExpressionNode, BooleanColumnExpressionNode, BooleanLogicalExpressionNode


class BooleanExpressionConverter(ExpressionConverter):
    """Converter that transforms expression nodes to boolean logic type.

    This converter can transform ternary expressions (and potentially other logic types)
    to boolean expressions. It preserves the original data values and operations,
    only changing the expression node type and logic classification.

    Key principles:
    - Structural transformation of classes (node type changes)
    - Comparison values and column names are preserved as-is
    - Operators may need to be mapped where differences exist between logic types
        - Some loss of information may occur when converting operators that rely on ternary logic. ie: XOR_PARITY -> XOR, MAYBE_TRUE -> IS_TRUE
        - May need to support smart wrapping in intermediary nodes to avoid such losses!
        - EG: Ternary IS_TRUE, IS_FALSE, IS_UNKNOWN are booleans living in a ternary world. They could wrap a TernaryCheckExpressionNode that preserves the ternary logic check while allowing conversion to boolean logic.
    - Operands are preserved as-is; they will convert themselves just-in-time when visited, if needed
    - Logic evaluation happens at execution time, not during conversion
    - No recursive conversion (operands convert themselves just-in-time)
    """

    @property
    def target_logic_type(self) -> str:
        """Target logic type for this converter."""
        return "boolean"

    def can_convert_from(self, source_logic_type: str) -> bool:
        """Check if conversion from source logic type is supported.

        Args:
            source_logic_type: Source logic type to convert from

        Returns:
            True if conversion is supported
        """
        # Currently supports conversion from ternary logic
        return source_logic_type == "ternary"

    def convert(self, expression_node: ExpressionNode) -> ExpressionNode:
        """Convert expression node to boolean logic type.

        Args:
            expression_node: Expression node to convert

        Returns:
            Converted boolean expression node

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

    def convert_literal(self, literal_node: LiteralExpressionNode) -> BooleanLiteralExpressionNode:
        """Convert literal expression to boolean logic type.

        Values are preserved as-is since they represent data values or column references,
        not logical truth values. Logic evaluation happens at execution time.

        Args:
            literal_node: Literal expression node to convert

        Returns:
            Boolean literal expression node
        """
        return BooleanLiteralExpressionNode(
            operator=literal_node.operator,
            value1=literal_node.value1,
            value2=literal_node.value2
        )

    def convert_column(self, column_node: ColumnExpressionNode) -> BooleanColumnExpressionNode:
        """Convert column expression to boolean logic type.

        Column names and comparison values are preserved as-is since they represent
        data references and values, not logical truth values.

        Args:
            column_node: Column expression node to convert

        Returns:
            Boolean column expression node
        """
        return BooleanColumnExpressionNode(
            column=column_node.column,
            operator=column_node.operator,
            value=getattr(column_node, 'value', None),
            compare_column=getattr(column_node, 'compare_column', None)
        )

    def convert_logical(self, logical_node: LogicalExpressionNode) -> BooleanLogicalExpressionNode:
        """Convert logical expression to boolean logic type.

        Operands are preserved as-is since they will convert themselves on a
        just-in-time basis when visited. No recursive conversion needed.

        Note: This conversion may be semantically lossy when converting from
        ternary logic, as UNKNOWN states lose their semantic meaning in boolean logic.

        Args:
            logical_node: Logical expression node to convert

        Returns:
            Boolean logical expression node
        """
        return BooleanLogicalExpressionNode(
            operator=logical_node.operator,
            operands=logical_node.operands
        )
