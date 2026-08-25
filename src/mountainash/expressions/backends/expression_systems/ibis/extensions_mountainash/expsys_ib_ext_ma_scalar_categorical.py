"""Ibis backend for categorical operations."""
from __future__ import annotations


from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarCategoricalExpressionSystemProtocol


class MountainAshIbisScalarCategoricalExpressionSystem(
    IbisBaseExpressionSystem,
    MountainAshScalarCategoricalExpressionSystemProtocol["IbisValueExpr"],
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
        target = "string" if value_type == "string" else "int64"
        return x.try_cast(target) if failure_behavior == "null" else x.cast(target)
