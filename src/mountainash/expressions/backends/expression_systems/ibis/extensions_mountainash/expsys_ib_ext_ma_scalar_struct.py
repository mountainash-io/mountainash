"""Ibis backend for mountainash struct operations."""
from __future__ import annotations

from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol
from mountainash.typespec.converters import _resolve_field_native
from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.core.dtypes import TypeTarget
class MountainAshIbisScalarStructExpressionSystem(IbisBaseExpressionSystem, MountainAshScalarStructExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of struct field access."""
    def cast_struct(
        self,
        x,
        /,
        *,
        fields: tuple[FieldSpec, ...],
        failure_behavior: str = "throw",
    ):
        field = FieldSpec(name="_struct", type=UniversalType.OBJECT, object_fields=list(fields))
        dtype = _resolve_field_native(field, TypeTarget.IBIS)
        return x.try_cast(dtype) if failure_behavior == "null" else x.cast(dtype)

    def struct_field(self, x, /, *, field_name: str):
        return x[field_name]
