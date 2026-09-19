"""Ibis backend for mountainash struct operations."""
from __future__ import annotations

from mountainash.core.dtypes import TypeTarget
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT
from mountainash.typespec.converters import _resolve_field_native
from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.universal_types import UniversalType
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
        field = FieldSpec(name="_struct", type=UniversalType.OBJECT, object_fields=list(fields))
        dtype = _resolve_field_native(field, TypeTarget.IBIS)
        return x.cast(dtype)

    def struct_field(self, x, /, *, field_name: str):
        return x[field_name]
