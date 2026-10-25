"""Ibis backend for mountainash struct operations."""
from __future__ import annotations

from typing import Literal

from mountainash.core.dtypes import CastTarget, TypeTarget, registry
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT


class MountainAshIbisScalarStructExpressionSystem(IbisBaseExpressionSystem, MountainAshScalarStructExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of struct field access."""
    def cast_struct(
        self,
        x,
        /,
        *converted_fields,
        dtype: CastTarget,
        field_names: tuple[str, ...] = (),
        failure_behavior: Literal["throw", "null"] = "throw",
    ):
        if self.dialect == "ibis-sqlite":
            raise BackendCapabilityError(
                "Ibis SQLite does not support struct casts.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_MOUNTAINASH_SCALAR_STRUCT.CAST,
            )
        if failure_behavior == "null":
            raise BackendCapabilityError(
                "Ibis struct casts cannot produce an atomic null on conversion failure.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_MOUNTAINASH_SCALAR_STRUCT.CAST,
            )
        native_target = registry.to_native_cast(dtype, TypeTarget.IBIS)
        if converted_fields:
            import ibis
            value = ibis.struct(dict(zip(
                field_names, converted_fields, strict=True,
            ))).cast(native_target)
            return ibis.ifelse(x.notnull(), value, ibis.null().cast(native_target))
        return x.cast(native_target)
    def struct_field(self, x, /, *, field_name: str):
        return x[field_name]
