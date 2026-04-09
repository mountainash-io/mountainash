"""Boolean operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarBooleanBuilderProtocol for logical operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_BOOLEAN, FKEY_MOUNTAINASH_SCALAR_TERNARY
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode
from mountainash.expressions.core.expression_protocols.api_builders.substrait import SubstraitScalarBooleanAPIBuilderProtocol
from ....expression_nodes import ScalarFunctionNode


if TYPE_CHECKING:
    # from mountainash.expressions.core.expression_nodes import ExpressionNode, ScalarFunctionNode
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class SubstraitScalarBooleanAPIBuilder(BaseExpressionAPIBuilder, SubstraitScalarBooleanAPIBuilderProtocol):
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
                function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_TRUE,
                arguments=[node],
            )
        return node



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
                function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.AND,
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
                function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.OR,
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
            function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.AND_NOT,
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
            function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.XOR,
            arguments=[self._coerce_if_needed(self._node), other_node],
        )
        return self._build(node)

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
            function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.NOT,
            arguments=[self._coerce_if_needed(self._node)],
        )
        return self._build(node)
