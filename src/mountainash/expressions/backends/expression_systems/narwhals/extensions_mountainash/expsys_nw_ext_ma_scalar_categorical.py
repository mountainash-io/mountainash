"""Narwhals backend for categorical operations."""
from __future__ import annotations

import narwhals as nw

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarCategoricalExpressionSystemProtocol


def _cast_integer_null(series):
    """Cast integer-like values without raising for invalid values."""
    import numpy as np

    values = []
    for value in series.to_numpy():
        if value is None:
            values.append(None)
            continue
        try:
            if value != value:
                values.append(None)
                continue
        except (TypeError, ValueError):
            pass
        if isinstance(value, str):
            if not value.lstrip("+-").isdigit():
                values.append(None)
                continue
            values.append(int(value))
            continue
        try:
            converted = int(value)
        except (TypeError, ValueError, OverflowError):
            values.append(None)
        else:
            values.append(converted if converted == value else None)
    return np.asarray(values, dtype=object)


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
        if (
            self.dialect == "narwhals-pandas"
            and value_type == "integer"
            and failure_behavior == "null"
        ):
            return x.map_batches(_cast_integer_null)
        return x.cast(target)
