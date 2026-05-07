"""Polars backend for mountainash struct operations."""
from __future__ import annotations

import polars as pl

from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol


class MountainAshPolarsScalarStructExpressionSystem(PolarsBaseExpressionSystem, MountainAshScalarStructExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of struct field access."""

    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)
