"""Narwhals backend for categorical operations."""
from __future__ import annotations

import narwhals as nw

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarCategoricalExpressionSystemProtocol
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_CATEGORICAL,
)



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
        if failure_behavior == "null" and value_type == "integer":
            raise BackendCapabilityError(
                "Narwhals cannot implement failure_behavior='null' for "
                "categorical integer casts. Use Polars or Ibis backend.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_MOUNTAINASH_SCALAR_CATEGORICAL.CAST,
            )
        target = nw.String if value_type == "string" else nw.Int64
        return x.cast(target)
