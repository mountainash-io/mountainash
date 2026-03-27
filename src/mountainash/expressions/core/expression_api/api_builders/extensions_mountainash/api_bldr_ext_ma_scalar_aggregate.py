"""Mountainash extension aggregate operations APIBuilder.

Stub class for future Mountainash-specific aggregate extensions.
Standard aggregate operations are handled by SubstraitScalarAggregateAPIBuilder.
"""

from __future__ import annotations

from ..api_builder_base import BaseExpressionAPIBuilder


class MountainAshScalarAggregateAPIBuilder(BaseExpressionAPIBuilder):
    """Mountainash extension aggregate operations.

    Stub for future aggregate extensions beyond Substrait standard.
    Standard aggregate operations live in SubstraitScalarAggregateAPIBuilder.
    """

    pass
