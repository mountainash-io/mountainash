"""Boolean operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarBooleanBuilderProtocol for logical operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder
from ....expression_nodes import ScalarFunctionNode, LiteralNode, SingularOrListNode
from ....expression_system.function_keys.enums import (
    KEY_SCALAR_COMPARISON,
    KEY_SCALAR_BOOLEAN,
    MOUNTAINASH_COMPARISON,
    MOUNTAINASH_TERNARY,
)

from mountainash_expressions.core.expression_system.function_keys.enums import KEY_SCALAR_STRING
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode
from mountainash_expressions.core.expression_protocols.api_builders.extensions_mountainash import SubstraitCastAPIBuilderProtocol


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class MountainAshScalarBooleanAPIBuilder(BaseExpressionAPIBuilder, ScalarBooleanBuilderProtocol):
    """
    Boolean operations APIBuilder (Substrait-aligned).

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

    Auto-Coercion:
        When ternary expressions (t_gt, t_and, etc.) are used with boolean
        operations (and_, or_, not_), they are automatically converted to
        boolean via is_true().
    """

    # ========================================
    # Ternary → Boolean Coercion Hook
    # ========================================

    def _coerce_if_needed(
        self,
        node: "ExpressionNode",
    ) -> "ExpressionNode":
        """
        Coerce ternary expressions to boolean via is_true().

        This hook is called automatically by _to_substrait_node() for all
        arguments passed to boolean operations. Non-terminal ternary nodes
        (which produce -1/0/1 values) are wrapped with is_true() to convert
        to boolean True/False for use with boolean logical operators.

        Args:
            node: The expression node to potentially coerce.

        Returns:
            The original node, or a wrapped is_true() node for ternary expressions.
        """
        if isinstance(node, ScalarFunctionNode) and node.is_ternary_non_terminal:
            return ScalarFunctionNode(
                function_key=MOUNTAINASH_TERNARY.IS_TRUE,
                arguments=[node],
            )
        return node

    # ========================================
    # Comparison Operations
    # ========================================

    def eq(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
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
            function_key=KEY_SCALAR_COMPARISON.EQUAL,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def ne(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Not equal to (!=)."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_COMPARISON.NOT_EQUAL,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def gt(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Greater than (>)."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_COMPARISON.GT,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def lt(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Less than (<)."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_COMPARISON.LT,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def ge(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Greater than or equal (>=)."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_COMPARISON.GTE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def le(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Less than or equal (<=)."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_COMPARISON.LTE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def is_close(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
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
        lower: Union[BaseExpressionAPI, "ExpressionNode", Any],
        upper: Union[BaseExpressionAPI, "ExpressionNode", Any],
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
            function_key=KEY_SCALAR_COMPARISON.BETWEEN,
            arguments=[self._node, lower_node, upper_node],
            options={"closed": closed},
        )
        return self._build(node)

    # ========================================
    # Collection Operations
    # ========================================

    def is_in(
        self,
        values: Union[BaseExpressionAPI, "ExpressionNode", Any],
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
        values: Union[BaseExpressionAPI, "ExpressionNode", Any],
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

    def and_(
        self,
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Logical AND operation.

        Automatically coerces ternary expressions to boolean via is_true().

        Args:
            *others: Other expressions to AND with this one.

        Returns:
            New ExpressionAPI with AND node.
        """
        if not others:
            return self._build(self._coerce_if_needed(self._node))

        # Build pairwise AND chain: ((a AND b) AND c) AND d ...
        # _to_substrait_node() automatically applies coercion via hook
        operands = [self._coerce_if_needed(self._node)] + [
            self._to_substrait_node(o) for o in others
        ]

        # Chain: reduce((a, b) -> ScalarFunctionNode("and", [a, b]), operands)
        result = operands[0]
        for operand in operands[1:]:
            result = ScalarFunctionNode(
                function_key=KEY_SCALAR_BOOLEAN.AND,
                arguments=[result, operand],
            )
        return self._build(result)

    def or_(
        self,
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Logical OR operation.

        Automatically coerces ternary expressions to boolean via is_true().

        Args:
            *others: Other expressions to OR with this one.

        Returns:
            New ExpressionAPI with OR node.
        """
        if not others:
            return self._build(self._coerce_if_needed(self._node))

        # _to_substrait_node() automatically applies coercion via hook
        operands = [self._coerce_if_needed(self._node)] + [
            self._to_substrait_node(o) for o in others
        ]
        result = operands[0]
        for operand in operands[1:]:
            result = ScalarFunctionNode(
                function_key=KEY_SCALAR_BOOLEAN.OR,
                arguments=[result, operand],
            )
        return self._build(result)

    def and_not(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Logical AND NOT operation.

        Returns (self AND NOT other) using Kleene logic.
        Equivalent to self.and_(other.not_()) but more efficient.

        Automatically coerces ternary expressions to boolean via is_true().

        Substrait: and_not

        Args:
            other: Expression to negate and AND with this one.

        Returns:
            New ExpressionAPI with AND_NOT node.
        """
        # _to_substrait_node() automatically applies coercion via hook
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_BOOLEAN.AND_NOT,
            arguments=[self._coerce_if_needed(self._node), other_node],
        )
        return self._build(node)

    def xor(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Logical XOR operation (exclusive or).

        Automatically coerces ternary expressions to boolean via is_true().

        Substrait: xor

        Args:
            other: Expression to XOR with this one.

        Returns:
            New ExpressionAPI with XOR node.
        """
        # _to_substrait_node() automatically applies coercion via hook
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_BOOLEAN.XOR,
            arguments=[self._coerce_if_needed(self._node), other_node],
        )
        return self._build(node)

    def xor_(
        self,
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Variadic logical XOR operation (exclusive or).

        Automatically coerces ternary expressions to boolean via is_true().

        Args:
            *others: Other expressions to XOR with this one.

        Returns:
            New ExpressionAPI with XOR node.
        """
        if not others:
            return self._build(self._coerce_if_needed(self._node))

        # _to_substrait_node() automatically applies coercion via hook
        operands = [self._coerce_if_needed(self._node)] + [
            self._to_substrait_node(o) for o in others
        ]
        result = operands[0]
        for operand in operands[1:]:
            result = ScalarFunctionNode(
                function_key=KEY_SCALAR_BOOLEAN.XOR,
                arguments=[result, operand],
            )
        return self._build(result)

    def xor_parity(
        self,
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.

        Automatically coerces ternary expressions to boolean via is_true().

        Args:
            *others: Other expressions to check parity with.

        Returns:
            New ExpressionAPI with XOR_PARITY node.
        """
        if not others:
            return self._build(self._coerce_if_needed(self._node))

        # _to_substrait_node() automatically applies coercion via hook
        operands = [self._coerce_if_needed(self._node)] + [
            self._to_substrait_node(o) for o in others
        ]
        result = operands[0]
        for operand in operands[1:]:
            result = ScalarFunctionNode(
                function_key=MOUNTAINASH_COMPARISON.XOR_PARITY,
                arguments=[result, operand],
            )
        return self._build(result)

    # ========================================
    # Unary Operators
    # ========================================

    def not_(self) -> BaseExpressionAPI:
        """
        Logical NOT operation.

        Automatically coerces ternary expressions to boolean via is_true().

        Returns:
            New ExpressionAPI with NOT node.
        """
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_BOOLEAN.NOT,
            arguments=[self._coerce_if_needed(self._node)],
        )
        return self._build(node)


# Alias for consistency with other scalar APIBuilders
ScalarBooleanAPIBuilder = BooleanAPIBuilder
