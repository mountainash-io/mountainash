"""Rounding operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarRoundingBuilderProtocol for rounding operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ROUNDING
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode
from mountainash.expressions.core.expression_protocols.api_builders.substrait import SubstraitScalarRoundingAPIBuilderProtocol


if TYPE_CHECKING:
    from mountainash.expressions.core.expression_nodes import ExpressionNode, ScalarFunctionNode
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class SubstraitScalarRoundingAPIBuilder(BaseExpressionAPIBuilder, SubstraitScalarRoundingAPIBuilderProtocol):
    """
    Rounding operations APIBuilder (Substrait-aligned).

    Provides numeric rounding operations.

    Methods:
        ceil: Round up to nearest integer
        floor: Round down to nearest integer
        round: Round to specified decimal places
    """

    def ceil(self) -> BaseExpressionAPI:
        """
        Round up to the nearest integer.

        Substrait: ceil

        Returns:
            New ExpressionAPI with ceil node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ROUNDING.CEIL,
            arguments=[self._node],
        )
        return self._build(node)

    def floor(self) -> BaseExpressionAPI:
        """
        Round down to the nearest integer.

        Substrait: floor

        Returns:
            New ExpressionAPI with floor node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ROUNDING.FLOOR,
            arguments=[self._node],
        )
        return self._build(node)

    def round(
        self,
        decimals: Optional[Union[BaseExpressionAPI, "ExpressionNode", Any, int]] = None,
    ) -> BaseExpressionAPI:
        """
        Round to the specified number of decimal places.

        Substrait: round

        Args:
            decimals: Number of decimal places (default: 0).

        Returns:
            New ExpressionAPI with round node.
        """
        if decimals is None:
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_ROUNDING.ROUND,
                arguments=[self._node],
            )
        else:
            decimals_node = self._to_substrait_node(decimals)
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_ROUNDING.ROUND,
                arguments=[self._node, decimals_node],
            )
        return self._build(node)
