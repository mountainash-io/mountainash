"""Ibis backend for categorical operations."""
from __future__ import annotations


from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarCategoricalExpressionSystemProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_CATEGORICAL


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
        if self.dialect == "ibis-sqlite" and value_type == "integer":
            raise BackendCapabilityError(
                "Ibis SQLite integer categorical casts cannot preserve the requested failure behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_MOUNTAINASH_SCALAR_CATEGORICAL.CAST,
            )
        target = "string" if value_type == "string" else "int64"
        return x.try_cast(target) if failure_behavior == "null" else x.cast(target)
