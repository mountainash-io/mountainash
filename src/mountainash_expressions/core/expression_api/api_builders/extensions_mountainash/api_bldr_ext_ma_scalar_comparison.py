"""Mountainash extension comparison operations APIBuilder.

Polars-compatible aliases for standard comparison operations.
Standard comparison operations are handled by SubstraitScalarComparisonAPIBuilder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainAshScalarComparisonAPIBuilder(BaseExpressionAPIBuilder):
    """Mountainash extension comparison operations.

    Provides Polars-compatible aliases for standard comparison operations.
    Standard comparison operations live in SubstraitScalarComparisonAPIBuilder.
    """

    def is_between(self, low, high, closed: str = "both") -> BaseExpressionAPI:
        """Alias for between() — Polars compatibility."""
        low_node = self._to_substrait_node(low)
        high_node = self._to_substrait_node(high)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.BETWEEN,
            arguments=[self._node, low_node, high_node],
            options={"closed": closed},
        )
        return self._build(node)
