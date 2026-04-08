"""Substrait scalar aggregate APIBuilder — exposes count() and future sum/min/max/etc."""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
)
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_scalar_aggregate import (
    SubstraitScalarAggregateAPIBuilderProtocol,
)

from ..api_builder_base import BaseExpressionAPIBuilder

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class SubstraitScalarAggregateAPIBuilder(
    BaseExpressionAPIBuilder,
    SubstraitScalarAggregateAPIBuilderProtocol,
):
    """Substrait-standard aggregate operations exposed as instance methods on col().

    Extend this class (or add sibling classes) for future Substrait aggregates
    (sum, min, max, mean, first_value, last_value, any_value, etc.).
    """

    def count(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Count non-null values. Corresponds to Substrait ``count(x)``."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT,
            arguments=[self._node],
            options={"overflow": overflow} if overflow is not None else {},
        )
        return self._build(node)
