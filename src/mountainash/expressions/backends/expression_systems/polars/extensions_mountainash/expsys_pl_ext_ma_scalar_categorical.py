"""Polars backend for categorical operations."""
from __future__ import annotations

import polars as pl

from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarCategoricalExpressionSystemProtocol


class MountainAshPolarsScalarCategoricalExpressionSystem(
    PolarsBaseExpressionSystem,
    MountainAshScalarCategoricalExpressionSystemProtocol[pl.Expr],
):
    """Categorical casts retain the declared base scalar type."""

    def cast_categorical(
        self,
        x,
        /,
        *,
        value_type: str,
        categories: tuple[object, ...],
        ordered: bool,
        failure_behavior: str = "throw",
    ):
        target = pl.String if value_type == "string" else pl.Int64
        return x.cast(target, strict=failure_behavior != "null")
