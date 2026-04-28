"""Narwhals backend for mountainash struct operations."""
from __future__ import annotations

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem


class MountainAshNarwhalsScalarStructExpressionSystem(NarwhalsBaseExpressionSystem):
    """Narwhals implementation of struct field access."""

    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)
