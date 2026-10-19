"""Ibis backend for mountainash struct operations."""
from __future__ import annotations

from typing import TYPE_CHECKING

from mountainash.core.dtypes import TypeTarget
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT
from mountainash.typespec.converters import _resolve_field_native
from mountainash.typespec.spec import FieldSpec

if TYPE_CHECKING:
    from collections.abc import Mapping


class MountainAshIbisScalarStructExpressionSystem(IbisBaseExpressionSystem, MountainAshScalarStructExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of struct field access."""
    def cast_struct(
        self,
        x,
        /,
        *converted_fields,
        fields: Mapping[str, FieldSpec],
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
        field = FieldSpec(fields=fields)
        dtype = _resolve_field_native(field, TypeTarget.IBIS, field_name="struct")
        if converted_fields:
            import ibis
            names = tuple(fields)
            value = ibis.struct(dict(zip(
                names, converted_fields[:len(names)], strict=True,
            ))).cast(dtype)
            valid = x.notnull()
            if len(converted_fields) > len(names):
                valid = valid & converted_fields[len(names)]
            return ibis.ifelse(valid, value, ibis.null().cast(dtype))
        return x.cast(dtype)
    def struct_field(self, x, /, *, field_name: str):
        return x[field_name]
