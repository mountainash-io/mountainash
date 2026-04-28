"""Polars backend for mountainash struct operations."""
from __future__ import annotations

from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem


class MountainAshPolarsScalarStructExpressionSystem(PolarsBaseExpressionSystem):
    """Polars implementation of struct field access."""

    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)
