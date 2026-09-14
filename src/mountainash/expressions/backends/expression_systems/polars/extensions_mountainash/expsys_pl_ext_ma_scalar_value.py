"""Polars lowering for Mountainash scalar value classification."""
from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from mountainash.core.value_classification import (
    boolean_value as scalar_boolean_value,
)
from mountainash.core.value_classification import (
    text_value as scalar_text_value,
)
from mountainash.core.value_classification import (
    value_kind as scalar_value_kind,
)
from mountainash.expressions.backends.expression_systems.polars.base import (
    PolarsBaseExpressionSystem,
)
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshScalarValueExpressionSystemProtocol,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from mountainash.expressions.types import PolarsExpr


class MountainAshPolarsScalarValueExpressionSystem(
    PolarsBaseExpressionSystem,
    MountainAshScalarValueExpressionSystemProtocol[pl.Expr],
):
    """Polars implementation of original-value classification and projections."""

    def value_kind(self, x: PolarsExpr, /) -> PolarsExpr:
        """Return a null-first label for the original scalar domain."""
        operand = self.operand_type("x")
        if operand.storage_kind == "polars_object":
            return _object_map(x, lambda value: scalar_value_kind(value).value, pl.String)
        return _kind_for_typed_operand(x, operand.logical_kind)

    def boolean_value(
        self,
        x: PolarsExpr,
        /,
        *,
        source: str = "boolean",
    ) -> PolarsExpr:
        """Project one explicitly selected Boolean-producing domain."""
        operand = self.operand_type("x")
        if operand.storage_kind == "polars_object":
            return _object_map(
                x,
                lambda value: scalar_boolean_value(value, source=source),
                pl.Boolean,
            )

        kind = operand.logical_kind
        if source == "boolean" and kind == "boolean":
            return x
        if source == "binary_number" and kind in {"integer", "float"}:
            return _binary_number_candidate(x)
        if source == "finite_number":
            if kind == "integer":
                return x.ne(0)
            if kind == "float":
                return pl.when(x.is_finite()).then(x.ne(0)).otherwise(
                    pl.lit(None, dtype=pl.Boolean)
                )
        return _null_like(x, pl.Boolean)

    def text_value(self, x: PolarsExpr, /) -> PolarsExpr:
        """Preserve only actual text as a nullable Polars string projection."""
        operand = self.operand_type("x")
        if operand.storage_kind == "polars_object":
            return _object_map(x, scalar_text_value, pl.String)
        if operand.logical_kind == "text":
            return x
        return _null_like(x, pl.String)


def _kind_for_typed_operand(x: PolarsExpr, logical_kind: str) -> PolarsExpr:
    label = {
        "boolean": "boolean",
        "integer": "integer",
        "float": "float",
        "text": "text",
        "null": "absent",
    }.get(logical_kind, "unsupported")
    return pl.when(x.is_null()).then(pl.lit("absent")).otherwise(pl.lit(label))


def _binary_number_candidate(x: PolarsExpr) -> PolarsExpr:
    return (
        pl.when(x.is_null())
        .then(pl.lit(None, dtype=pl.Boolean))
        .when(x.eq(0))
        .then(pl.lit(False))
        .when(x.eq(1))
        .then(pl.lit(True))
        .otherwise(pl.lit(None, dtype=pl.Boolean))
    )


def _null_like(x: PolarsExpr, dtype: pl.DataType | type[pl.DataType]) -> PolarsExpr:
    """Produce a typed null expression with the operand's row shape."""
    return pl.when(x.is_null()).then(pl.lit(None, dtype=dtype)).otherwise(
        pl.lit(None, dtype=dtype)
    )


def _object_map(
    x: PolarsExpr,
    projection: Callable[[object], object],
    dtype: pl.DataType | type[pl.DataType],
) -> PolarsExpr:
    """Apply shared scalar semantics to original Object values at execution time."""

    def project_batch(batch: pl.Series) -> pl.Series:
        return pl.Series(
            batch.name,
            [projection(batch[index]) for index in range(len(batch))],
            dtype=dtype,
        )

    return x.map_batches(
        project_batch,
        return_dtype=dtype,
        is_elementwise=True,
    )
