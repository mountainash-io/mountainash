"""Mountainash extension comparison operations APIBuilder.

Stub class for future Mountainash-specific comparison extensions.
Standard comparison operations are handled by SubstraitScalarComparisonAPIBuilder.
"""

from __future__ import annotations

from ..api_builder_base import BaseExpressionAPIBuilder


class MountainAshScalarComparisonAPIBuilder(BaseExpressionAPIBuilder):
    """Mountainash extension comparison operations.

    Stub for future comparison extensions beyond Substrait standard.
    Standard comparison operations live in SubstraitScalarComparisonAPIBuilder.
    """

    pass
