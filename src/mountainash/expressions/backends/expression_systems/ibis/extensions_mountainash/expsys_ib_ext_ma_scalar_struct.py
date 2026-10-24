"""Ibis backend for mountainash struct operations."""
from __future__ import annotations

from mountainash.core.dtypes import TypeTarget
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

from mountainash.typespec.converters import resolve_native_type
from mountainash.typespec.spec import FieldDefinition
class MountainAshIbisScalarStructExpressionSystem(IbisBaseExpressionSystem, MountainAshScalarStructExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of struct field access."""
    def cast_struct(
        self,
        x,
        /,
        *converted_fields,
        fields: Mapping[str, FieldDefinition],
        failure_behavior: str = "throw",
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
        dtype = resolve_native_type(FieldDefinition(fields=fields), TypeTarget.IBIS)
        if converted_fields:
            import ibis
            count = len(fields)
            value = ibis.struct(dict(zip(
                fields, converted_fields[:count], strict=True,
            ))).cast(dtype)
            valid = x.notnull()
            if len(converted_fields) > count:
                valid = valid & converted_fields[count]
            return ibis.ifelse(valid, value, ibis.null().cast(dtype))
        return x.cast(dtype)
    def struct_field(self, x, /, *, field_name: str):
        return x[field_name]
