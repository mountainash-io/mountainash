"""Boolean operations namespace (comparison and logical).

Substrait-aligned implementation using ScalarFunctionNode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union
from functools import reduce

from .base import BaseExpressionNamespace
from ...expression_nodes import (
    ScalarFunctionNode,
    LiteralNode,
    SingularOrListNode,
    SUBSTRAIT_COMPARISON,
    SUBSTRAIT_BOOLEAN,
    MOUNTAINASH_COMPARISON,
)




if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ..substrait_nodes import SubstraitNode


class ScalarComparisonNamespace(BaseExpressionNamespace):
    """
    Boolean operations namespace (Substrait-aligned).

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
    """

    # ========================================
    # Comparison Operations
    # ========================================

    def eq(
        self,
        other: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Equal to (==).

        Args:
            other: Value or expression to compare with.

        Returns:
            New ExpressionAPI with comparison node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_COMPARISON.EQ,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def ne(
        self,
        other: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """Not equal to (!=)."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_COMPARISON.NE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def gt(
        self,
        other: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """Greater than (>)."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_COMPARISON.GT,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def lt(
        self,
        other: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """Less than (<)."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_COMPARISON.LT,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def ge(
        self,
        other: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """Greater than or equal (>=)."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_COMPARISON.GE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def le(
        self,
        other: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """Less than or equal (<=)."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_COMPARISON.LE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def is_close(
        self,
        other: Union[BaseExpressionAPI, SubstraitNode, Any],
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
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=MOUNTAINASH_COMPARISON.IS_CLOSE,
            arguments=[self._node, other_node],
            options={"precision": precision},
        )
        return self._build(node)

    def between(
        self,
        lower: Union[BaseExpressionAPI, SubstraitNode, Any],
        upper: Union[BaseExpressionAPI, SubstraitNode, Any],
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
        lower_node = self._to_substrait_node(lower)
        upper_node = self._to_substrait_node(upper)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_COMPARISON.BETWEEN,
            arguments=[self._node, lower_node, upper_node],
            options={"closed": closed},
        )
        return self._build(node)

    # ========================================
    # Collection Operations
    # ========================================

    def is_in(
        self,
        values: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Check if value is in a collection.

        Args:
            values: Collection to check membership in.

        Returns:
            New ExpressionAPI with is_in node.
        """
        # Convert values list to LiteralNodes if needed
        if isinstance(values, (list, tuple, set)):
            options = [LiteralNode(value=v) for v in values]
        else:
            # Single value or expression
            options = [self._to_substrait_node(values)]

        node = SingularOrListNode(
            value=self._node,
            options=options,
        )
        return self._build(node)

    def is_not_in(
        self,
        values: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Check if value is not in a collection.

        Args:
            values: Collection to check membership in.

        Returns:
            New ExpressionAPI with is_not_in node.
        """
        # is_not_in is just NOT(is_in(...))
        is_in_result = self.is_in(values)
        return is_in_result.not_()

    # ========================================
    # Boolean Constants
    # ========================================

    def always_true(self) -> BaseExpressionAPI:
        """Return a constant TRUE value."""
        node = LiteralNode(value=True)
        return self._build(node)

    def always_false(self) -> BaseExpressionAPI:
        """Return a constant FALSE value."""
        node = LiteralNode(value=False)
        return self._build(node)

    # ========================================
    # Logical Operators
    # ========================================


    # ========================================
    # Unary Operators
    # ========================================



    def is_null(self) -> BaseExpressionAPI:
        """
        Check if expression evaluates to NULL.

        Returns:
            New ExpressionAPI with is_null node.
        """
        node = ScalarFunctionNode(
            function_key=SCALAR_COMPARISON.IS_NULL,
            arguments=[self._node],
        )
        return self._build(node)

    def is_not_null(self) -> BaseExpressionAPI:
        """
        Check if expression evaluates to NOT NULL.

        Returns:
            New ExpressionAPI with is_not_null node.
        """
        node = ScalarFunctionNode(
            function_key=SCALAR_COMPARISON.IS_NOT_NULL,
            arguments=[self._node],
        )
        return self._build(node)

    # Alias for backwards compatibility
    def not_null(self) -> BaseExpressionAPI:
        """
        Check if expression evaluates to NOT NULL.

        Alias for is_not_null() for backwards compatibility.

        Returns:
            New ExpressionAPI with is_not_null node.
        """
        return self.is_not_null()
