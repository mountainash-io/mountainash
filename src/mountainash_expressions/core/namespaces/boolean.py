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
        operands = [self._node] + [self._to_node_or_value(other) for other in others]
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
        operands = [self._node] + [self._to_node_or_value(other) for other in others]
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
        operands = [self._node] + [self._to_node_or_value(other) for other in others]
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
        operands = [self._node] + [self._to_node_or_value(other) for other in others]
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
        node = BooleanUnaryExpressionNode(
            ENUM_BOOLEAN_OPERATORS.NOT,
            self._node,
        )
        return self._build(node)

    def is_true(self) -> BaseExpressionAPI:
        """
        Check if expression evaluates to TRUE (for ternary logic).

        Returns:
            New ExpressionAPI with IS_TRUE node.
        """
        node = BooleanUnaryExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_TRUE,
            self._node,
        )
        return self._build(node)

    def is_false(self) -> BaseExpressionAPI:
        """
        Check if expression evaluates to FALSE (for ternary logic).

        Returns:
            New ExpressionAPI with IS_FALSE node.
        """
        node = BooleanUnaryExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_FALSE,
            self._node,
        )
        return self._build(node)
