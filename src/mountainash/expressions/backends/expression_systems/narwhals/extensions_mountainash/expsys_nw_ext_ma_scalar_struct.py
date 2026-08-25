"""Narwhals backend for mountainash struct operations."""
from __future__ import annotations
import narwhals as nw

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol
from mountainash.typespec.converters import _resolve_field_native
from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.core.dtypes import TypeTarget

class MountainAshNarwhalsScalarStructExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshScalarStructExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of struct field access."""
    def cast_struct(
        self,
        x,
        /,
        *,
        fields: tuple[FieldSpec, ...],
        failure_behavior: str = "throw",
    ):
        field = FieldSpec(name="_struct", type=UniversalType.OBJECT, object_fields=list(fields))
        dtype = _resolve_field_native(field, TypeTarget.NARWHALS)
        return x.cast(dtype)

    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)
