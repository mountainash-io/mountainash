"""Comparison operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarComparisonBuilderProtocol for comparison operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode
from mountainash_expressions.core.expression_protocols.api_builders.substrait import SubstraitScalarComparisonAPIBuilderProtocol


if TYPE_CHECKING:
    from mountainash_expressions.core.expression_nodes import ExpressionNode, ScalarFunctionNode
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class SubstraitScalarComparisonAPIBuilder(BaseExpressionAPIBuilder, SubstraitScalarComparisonAPIBuilderProtocol):
    """
    Comparison operations APIBuilder (Substrait-aligned).

    Provides comparison operators that produce boolean results.

    Binary Comparisons:
        equal, not_equal: Equality checks
        lt, gt, lte, gte: Ordering comparisons
        between: Range check

    State Checks:
        is_true, is_not_true, is_false, is_not_false: Boolean state
        is_null, is_not_null: Null state
        is_nan, is_finite, is_infinite: Numeric state

    Null Handling:
        nullif: Return null if equal
        coalesce: First non-null value

    Min/Max:
        least, greatest: With null propagation
        least_skip_null, greatest_skip_null: Ignoring nulls
    """

    # ========================================
    # Binary Comparisons
    # ========================================

    def equal(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Equal comparison (==).

        Substrait: equal

        Args:
            other: Value or expression to compare with.

        Returns:
            New ExpressionAPI with comparison node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def not_equal(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Not equal comparison (!=).

        Substrait: not_equal

        Args:
            other: Value or expression to compare with.

        Returns:
            New ExpressionAPI with comparison node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.NOT_EQUAL,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def lt(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Less than comparison (<).

        Substrait: lt

        Args:
            other: Value or expression to compare with.

        Returns:
            New ExpressionAPI with comparison node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.LT,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def gt(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Greater than comparison (>).

        Substrait: gt

        Args:
            other: Value or expression to compare with.

        Returns:
            New ExpressionAPI with comparison node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def lte(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Less than or equal comparison (<=).

        Substrait: lte

        Args:
            other: Value or expression to compare with.

        Returns:
            New ExpressionAPI with comparison node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.LTE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def gte(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Greater than or equal comparison (>=).

        Substrait: gte

        Args:
            other: Value or expression to compare with.

        Returns:
            New ExpressionAPI with comparison node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GTE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def between(
        self,
        low: Union[BaseExpressionAPI, "ExpressionNode", Any],
        high: Union[BaseExpressionAPI, "ExpressionNode", Any],
        closed: str = "both",

    ) -> BaseExpressionAPI:
        """
        Check if value is between low and high (inclusive).

        Substrait: between

        Args:
            low: Lower bound.
            high: Upper bound.
            closed: Which bounds are inclusive ("left", "right", "both", "neither").

        Returns:
            New ExpressionAPI with between node.
        """
        low_node = self._to_substrait_node(low)
        high_node = self._to_substrait_node(high)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.BETWEEN,
            arguments=[self._node, low_node, high_node],
            options={"closed": closed},

        )
        return self._build(node)

    # ========================================
    # Boolean State Checks
    # ========================================

    def is_true(self) -> BaseExpressionAPI:
        """
        Whether value is true.

        Substrait: is_true

        Returns:
            New ExpressionAPI with is_true node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_TRUE,
            arguments=[self._node],
        )
        return self._build(node)

    def is_not_true(self) -> BaseExpressionAPI:
        """
        Whether value is not true (false or null).

        Substrait: is_not_true

        Returns:
            New ExpressionAPI with is_not_true node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NOT_TRUE,
            arguments=[self._node],
        )
        return self._build(node)

    def is_false(self) -> BaseExpressionAPI:
        """
        Whether value is false.

        Substrait: is_false

        Returns:
            New ExpressionAPI with is_false node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_FALSE,
            arguments=[self._node],
        )
        return self._build(node)

    def is_not_false(self) -> BaseExpressionAPI:
        """
        Whether value is not false (true or null).

        Substrait: is_not_false

        Returns:
            New ExpressionAPI with is_not_false node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NOT_FALSE,
            arguments=[self._node],
        )
        return self._build(node)

    # ========================================
    # Null State Checks
    # ========================================

    def is_null(self) -> BaseExpressionAPI:
        """
        Whether value is null. NaN is not null.

        Substrait: is_null

        Returns:
            New ExpressionAPI with is_null node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NULL,
            arguments=[self._node],
        )
        return self._build(node)

    def is_not_null(self) -> BaseExpressionAPI:
        """
        Whether value is not null. NaN is not null.

        Substrait: is_not_null

        Returns:
            New ExpressionAPI with is_not_null node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NOT_NULL,
            arguments=[self._node],
        )
        return self._build(node)

    # ========================================
    # Numeric State Checks
    # ========================================

    def is_nan(self) -> BaseExpressionAPI:
        """
        Whether value is NaN (not a number).

        Substrait: is_nan

        Returns:
            New ExpressionAPI with is_nan node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NAN,
            arguments=[self._node],
        )
        return self._build(node)

    def is_finite(self) -> BaseExpressionAPI:
        """
        Whether value is finite (neither infinite nor NaN).

        Substrait: is_finite

        Returns:
            New ExpressionAPI with is_finite node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_FINITE,
            arguments=[self._node],
        )
        return self._build(node)

    def is_infinite(self) -> BaseExpressionAPI:
        """
        Whether value is infinite.

        Substrait: is_infinite

        Returns:
            New ExpressionAPI with is_infinite node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_INFINITE,
            arguments=[self._node],
        )
        return self._build(node)

    # ========================================
    # Null Handling
    # ========================================

    def nullif(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Return null if values are equal, otherwise return first value.

        Substrait: nullif

        Args:
            other: Value to compare with.

        Returns:
            New ExpressionAPI with nullif node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.NULL_IF,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def coalesce(
        self,
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Return first non-null value.

        Substrait: coalesce

        Args:
            *others: Additional values to consider.

        Returns:
            New ExpressionAPI with coalesce node.
        """
        operands = [self._node] + [self._to_substrait_node(o) for o in others]
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.COALESCE,
            arguments=operands,
        )
        return self._build(node)

    # ========================================
    # Min/Max Operations
    # ========================================

    def least(
        self,
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Return smallest value. Returns null if any argument is null.

        Substrait: least

        Args:
            *others: Additional values to compare.

        Returns:
            New ExpressionAPI with least node.
        """
        operands = [self._node] + [self._to_substrait_node(o) for o in others]
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.LEAST,
            arguments=operands,
        )
        return self._build(node)

    def least_skip_null(
        self,
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Return smallest value, skipping nulls.

        Returns null only if all arguments are null.

        Substrait: least_skip_null

        Args:
            *others: Additional values to compare.

        Returns:
            New ExpressionAPI with least_skip_null node.
        """
        operands = [self._node] + [self._to_substrait_node(o) for o in others]
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.LEAST_SKIP_NULL,
            arguments=operands,
        )
        return self._build(node)

    def greatest(
        self,
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Return largest value. Returns null if any argument is null.

        Substrait: greatest

        Args:
            *others: Additional values to compare.

        Returns:
            New ExpressionAPI with greatest node.
        """
        operands = [self._node] + [self._to_substrait_node(o) for o in others]
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GREATEST,
            arguments=operands,
        )
        return self._build(node)

    def greatest_skip_null(
        self,
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Return largest value, skipping nulls.

        Returns null only if all arguments are null.

        Substrait: greatest_skip_null

        Args:
            *others: Additional values to compare.

        Returns:
            New ExpressionAPI with greatest_skip_null node.
        """
        operands = [self._node] + [self._to_substrait_node(o) for o in others]
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GREATEST_SKIP_NULL,
            arguments=operands,
        )
        return self._build(node)
