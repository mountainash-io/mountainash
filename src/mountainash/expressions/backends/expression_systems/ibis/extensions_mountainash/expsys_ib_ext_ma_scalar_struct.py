"""Ibis backend for mountainash struct operations."""
from __future__ import annotations

from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem


class MountainAshIbisScalarStructExpressionSystem(IbisBaseExpressionSystem):
    """Ibis implementation of struct field access."""

    def struct_field(self, x, /, *, field_name: str):
        return x[field_name]
