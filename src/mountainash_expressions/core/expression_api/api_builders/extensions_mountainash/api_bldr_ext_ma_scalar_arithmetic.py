"""Arithmetic operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarArithmeticBuilderProtocol for arithmetic operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_ARITHMETIC, FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode
from mountainash_expressions.core.expression_protocols.api_builders.extensions_mountainash import MountainAshScalarArithmeticAPIBuilderProtocol


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class MountainAshScalarArithmeticAPIBuilder(BaseExpressionAPIBuilder, MountainAshScalarArithmeticAPIBuilderProtocol):
    """
    Arithmetic operations APIBuilder (Substrait-aligned).

    Provides arithmetic operators as named methods.
    Python operators (__add__, __sub__, etc.) are on the main API class.

    Methods:
        add: Addition (+)
        subtract: Subtraction (-)
        multiply: Multiplication (*)
        divide: Division (/)
        modulo: Modulo (%)
        power: Exponentiation (**)
        floor_divide: Floor division (//)
    """

    def floor_divide(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Floor division: self // other.

        Args:
            other: Value or expression to divide by.

        Returns:
            New ExpressionAPI with floor division node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_ARITHMETIC.FLOOR_DIVIDE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def rfloor_divide(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Reverse floor division: other // self.

        Used by __rfloordiv__ when self is on the right side of //.

        Args:
            other: Value or expression to be divided.

        Returns:
            New ExpressionAPI with floor division node (other // self).
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_ARITHMETIC.FLOOR_DIVIDE,
            arguments=[other_node, self._node],
        )
        return self._build(node)
