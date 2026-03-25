"""Substrait aggregate operations APIBuilder.

Stub class — aggregate operations are not yet wired into the flat namespace.
Uncomment in BooleanExpressionAPI._FLAT_NAMESPACES when ready.
"""

from __future__ import annotations

from ..api_builder_base import BaseExpressionAPIBuilder


class SubstraitScalarAggregateAPIBuilder(BaseExpressionAPIBuilder):
    """Substrait aggregate operations.

    Stub — not yet active. Aggregate operations (count, any_value)
    will be enabled when wired into BooleanExpressionAPI._FLAT_NAMESPACES.
    """

    pass
