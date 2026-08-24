"""Narwhals backend for categorical operations."""
from __future__ import annotations

import narwhals as nw

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarCategoricalExpressionSystemProtocol


class MountainAshNarwhalsScalarCategoricalExpressionSystem(
    NarwhalsBaseExpressionSystem,
    MountainAshScalarCategoricalExpressionSystemProtocol[nw.Expr],
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
        target = nw.String if value_type == "string" else nw.Int64
        return x.cast(target, strict=failure_behavior != "null")
