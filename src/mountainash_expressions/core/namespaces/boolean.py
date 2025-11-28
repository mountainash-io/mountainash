"""Boolean operations namespace (comparison and logical)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .base import BaseNamespace
from ..protocols import ENUM_BOOLEAN_OPERATORS, BooleanBuilderProtocol
from ..expression_nodes import (
    BooleanComparisonExpressionNode,
    BooleanCollectionExpressionNode,
    BooleanConstantExpressionNode,
    BooleanIsCloseExpressionNode,
    BooleanBetweenExpressionNode,
    BooleanIterableExpressionNode,
    BooleanUnaryExpressionNode,
)
from ..expression_nodes.ternary_expression_nodes import (
    TernaryExpressionNode,
    TernaryUnaryExpressionNode,
)
from ..constants import TERNARY_NON_TERMINAL_OPERATORS, ENUM_TERNARY_OPERATORS

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ..expression_nodes.base_expression_node import ExpressionNode


class BooleanNamespace(BaseNamespace, BooleanBuilderProtocol):
    """
    Boolean operations namespace.

    Provides comparison operators that produce boolean results,
    and logical operators that combine boolean values.

    Comparison Operations:
        eq: Equal to (==)
        ne: Not equal to (!=)
        gt: Greater than (>)
        lt: Less than (<)
        ge: Greater than or equal (>=)
        le: Less than or equal (<=)
        is_close: Approximately equal within precision
        between: Value within range
        is_in: Value in collection
        is_not_in: Value not in collection
        always_true: Constant TRUE
        always_false: Constant FALSE

    Logical Operations:
        and_: Logical AND
        or_: Logical OR
        xor_: Logical XOR (exclusive or)
        xor_parity: XOR parity (odd number of TRUE)
        not_: Logical NOT
        is_true: Check if TRUE (for ternary logic)
        is_false: Check if FALSE (for ternary logic)
    """

    # ========================================
    # Ternary → Boolean Coercion
    # ========================================

    def _coerce_if_needed(
        self,
        node_or_value: Union[ExpressionNode, Any],
    ) -> Union[ExpressionNode, Any]:
        """
        Auto-coerce non-terminal ternary expressions to boolean.

        When a ternary expression (e.g., t_gt result) is used as an operand
        in a boolean operation (e.g., and_()), automatically wrap it with
        is_true() to convert the -1/0/1 sentinel values to boolean.

        This enables natural chaining like:
            ma.col("score").t_gt(70).and_(ma.col("active").eq(True))

        Args:
            node_or_value: The node or value to potentially coerce.

        Returns:
            The original input or a TernaryUnaryExpressionNode(IS_TRUE, ...).
        """
        # Check if this is a non-terminal ternary node
        if isinstance(node_or_value, TernaryExpressionNode):
            if node_or_value.operator in TERNARY_NON_TERMINAL_OPERATORS:
                # Auto-wrap with is_true() to convert to boolean
                return TernaryUnaryExpressionNode(
                    ENUM_TERNARY_OPERATORS.IS_TRUE,
                    node_or_value,
                )

        return node_or_value

    def _get_self_operand(self) -> ExpressionNode:
        """
        Get self._node for use as operand, with ternary coercion if needed.

        When the current node is a non-terminal ternary expression (e.g., t_gt
        result), it needs to be coerced to boolean before use in boolean
        operations like and_(), or_(), etc.

        Returns:
            The self node, potentially wrapped with is_true() if ternary.
        """
        return self._coerce_if_needed(self._node)

    # ========================================
    # Comparison Operations
    # ========================================

    def eq(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Equal to (==).

        Args:
            other: Value or expression to compare with.

        Returns:
            New ExpressionAPI with comparison node.
        """
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.EQ,
            self._node,
            other_node,
        )
        return self._build(node)

    def ne(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Not equal to (!=)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.NE,
            self._node,
            other_node,
        )
        return self._build(node)

    def gt(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Greater than (>)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.GT,
            self._node,
            other_node,
        )
        return self._build(node)

    def lt(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Less than (<)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.LT,
            self._node,
            other_node,
        )
        return self._build(node)

    def ge(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Greater than or equal (>=)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.GE,
            self._node,
            other_node,
        )
        return self._build(node)

    def le(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Less than or equal (<=)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.LE,
            self._node,
            other_node,
        )
        return self._build(node)

    def is_close(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
        precision: float = 1e-5,
    ) -> BaseExpressionAPI:
        """
        Check if values are approximately equal within precision.

        Args:
            other: Value to compare with.
            precision: Maximum allowed difference (default: 1e-5).

        Returns:
            New ExpressionAPI with is_close node.
        """
        other_node = self._to_node_or_value(other)
        node = BooleanIsCloseExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_CLOSE,
            self._node,
            other_node,
            precision,
        )
        return self._build(node)

    def between(
        self,
        lower: Union[BaseExpressionAPI, ExpressionNode, Any],
        upper: Union[BaseExpressionAPI, ExpressionNode, Any],
        closed: str = "both",
    ) -> BaseExpressionAPI:
        """
        Check if value is between bounds.

        Args:
            lower: Lower bound.
            upper: Upper bound.
            closed: Which bounds are inclusive ("left", "right", "both", "neither").

        Returns:
            New ExpressionAPI with between node.
        """
        lower_node = self._to_node_or_value(lower)
        upper_node = self._to_node_or_value(upper)
        node = BooleanBetweenExpressionNode(
            ENUM_BOOLEAN_OPERATORS.BETWEEN,
            self._node,  # value to check
            lower_node,
            closed,
        )
        return self._build(node)

    # ========================================
    # Collection Operations
    # ========================================

    def is_in(
        self,
        values: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Check if value is in a collection.

        Args:
            values: Collection to check membership in.

        Returns:
            New ExpressionAPI with is_in node.
        """
        values_node = self._to_node_or_value(values)
        node = BooleanCollectionExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_IN,
            None,  # operand (not used by visitor)
            self._node,  # element (used by visitor)
            values_node,  # container
        )
        return self._build(node)

    def is_not_in(
        self,
        values: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Check if value is not in a collection.

        Args:
            values: Collection to check membership in.

        Returns:
            New ExpressionAPI with is_not_in node.
        """
        values_node = self._to_node_or_value(values)
        node = BooleanCollectionExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_NOT_IN,
            None,  # operand (not used by visitor)
            self._node,  # element (used by visitor)
            values_node,  # container
        )
        return self._build(node)

    # ========================================
    # Boolean Constants
    # ========================================

    def always_true(self) -> BaseExpressionAPI:
        """Return a constant TRUE value."""
        node = BooleanConstantExpressionNode(
            ENUM_BOOLEAN_OPERATORS.ALWAYS_TRUE,
        )
        return self._build(node)

    def always_false(self) -> BaseExpressionAPI:
        """Return a constant FALSE value."""
        node = BooleanConstantExpressionNode(
            ENUM_BOOLEAN_OPERATORS.ALWAYS_FALSE,
        )
        return self._build(node)

    # ========================================
    # Logical Operators (Iterable)
    # ========================================

    def and_(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Logical AND operation.

        Args:
            *others: Other expressions to AND with this one.

        Returns:
            New ExpressionAPI with AND node.
        """
        # Use _get_self_operand() to auto-coerce ternary self._node to boolean
        operands = [self._get_self_operand()] + [self._to_node_or_value(other) for other in others]
        node = BooleanIterableExpressionNode(
            ENUM_BOOLEAN_OPERATORS.AND,
            *operands,
        )
        return self._build(node)

    def or_(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Logical OR operation.

        Args:
            *others: Other expressions to OR with this one.

        Returns:
            New ExpressionAPI with OR node.
        """
        # Use _get_self_operand() to auto-coerce ternary self._node to boolean
        operands = [self._get_self_operand()] + [self._to_node_or_value(other) for other in others]
        node = BooleanIterableExpressionNode(
            ENUM_BOOLEAN_OPERATORS.OR,
            *operands,
        )
        return self._build(node)

    def xor_(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Logical XOR operation (exclusive or).

        Args:
            *others: Other expressions to XOR with this one.

        Returns:
            New ExpressionAPI with XOR node.
        """
        # Use _get_self_operand() to auto-coerce ternary self._node to boolean
        operands = [self._get_self_operand()] + [self._to_node_or_value(other) for other in others]
        node = BooleanIterableExpressionNode(
            ENUM_BOOLEAN_OPERATORS.XOR,
            *operands,
        )
        return self._build(node)

    def xor_parity(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.

        Args:
            *others: Other expressions to check parity with.

        Returns:
            New ExpressionAPI with XOR_PARITY node.
        """
        # Use _get_self_operand() to auto-coerce ternary self._node to boolean
        operands = [self._get_self_operand()] + [self._to_node_or_value(other) for other in others]
        node = BooleanIterableExpressionNode(
            ENUM_BOOLEAN_OPERATORS.XOR_PARITY,
            *operands,
        )
        return self._build(node)

    # ========================================
    # Unary Operators
    # ========================================

    def not_(self) -> BaseExpressionAPI:
        """
        Logical NOT operation.

        Returns:
            New ExpressionAPI with NOT node.
        """
        # Use _get_self_operand() to auto-coerce ternary self._node to boolean
        node = BooleanUnaryExpressionNode(
            ENUM_BOOLEAN_OPERATORS.NOT,
            self._get_self_operand(),
        )
        return self._build(node)
