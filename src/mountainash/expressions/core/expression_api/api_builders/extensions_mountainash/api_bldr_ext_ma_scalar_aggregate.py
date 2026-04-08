"""Mountainash extension aggregate operations APIBuilder.

Hosts short aliases for Substrait aggregates per
``c.api-design/short-aliases.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
)

from ..api_builder_base import BaseExpressionAPIBuilder

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainAshScalarAggregateAPIBuilder(BaseExpressionAPIBuilder):
    """Mountainash short aliases for Substrait aggregate operations."""

    def mean(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Short alias for :meth:`SubstraitScalarAggregateAPIBuilder.avg`.

        Matches the Polars / pandas idiom; semantically identical to ``avg``.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.AVG,
            arguments=[self._node],
            options={"overflow": overflow} if overflow is not None else {},
        )
        return self._build(node)
