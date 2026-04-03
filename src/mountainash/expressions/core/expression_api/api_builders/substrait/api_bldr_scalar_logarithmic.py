"""Logarithmic operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarLogarithmicBuilderProtocol for logarithmic operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.expressions.core.expression_protocols.api_builders.substrait import SubstraitScalarLogarithmicAPIBuilderProtocol


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class SubstraitScalarLogarithmicAPIBuilder(BaseExpressionAPIBuilder, SubstraitScalarLogarithmicAPIBuilderProtocol):
    """
    Logarithmic operations APIBuilder (Substrait-aligned).

    Provides logarithmic operations.

    Methods:
        ln: Natural logarithm (base e)
        log10: Logarithm base 10
        log2: Logarithm base 2
        log: Logarithm with custom base
    """

    def ln(self) -> BaseExpressionAPI:
        """
        Natural logarithm (base e).

        Substrait: ln

        Returns:
            New ExpressionAPI with ln node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOG,
            arguments=[self._node],
        )
        return self._build(node)

    def log10(self) -> BaseExpressionAPI:
        """
        Logarithm base 10.

        Substrait: log10

        Returns:
            New ExpressionAPI with log10 node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOG10,
            arguments=[self._node],
        )
        return self._build(node)

    def log2(self) -> BaseExpressionAPI:
        """
        Logarithm base 2.

        Substrait: log2

        Returns:
            New ExpressionAPI with log2 node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOG2,
            arguments=[self._node],
        )
        return self._build(node)

    def log(
        self,
        base: Union[BaseExpressionAPI, "ExpressionNode", Any, float],
    ) -> BaseExpressionAPI:
        """
        Logarithm with custom base.

        Substrait: logb

        Args:
            base: The logarithm base.

        Returns:
            New ExpressionAPI with log node.
        """
        base_node = self._to_substrait_node(base)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOGB,
            arguments=[self._node, base_node],
        )
        return self._build(node)
