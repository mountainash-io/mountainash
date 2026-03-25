"""Boolean operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarBooleanBuilderProtocol for logical operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder
from ....expression_nodes import ScalarFunctionNode, LiteralNode, SingularOrListNode
from ....expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_COMPARISON,
    FKEY_SUBSTRAIT_SCALAR_BOOLEAN,
    FKEY_MOUNTAINASH_SCALAR_COMPARISON,
    FKEY_MOUNTAINASH_SCALAR_BOOLEAN,
    FKEY_MOUNTAINASH_SCALAR_TERNARY,
)

# from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_BOOLEAN
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode
from mountainash_expressions.core.expression_protocols.api_builders.extensions_mountainash import MountainAshScalarBooleanAPIBuilderProtocol


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class MountainAshScalarBooleanAPIBuilder(BaseExpressionAPIBuilder, MountainAshScalarBooleanAPIBuilderProtocol):
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
                function_key=FKEY_MOUNTAINASH_SCALAR_BOOLEAN.XOR_PARITY,
                arguments=[result, operand],
            )
        return self._build(result)
