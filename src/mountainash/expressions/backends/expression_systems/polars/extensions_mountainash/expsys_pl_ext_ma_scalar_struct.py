"""Polars backend for mountainash struct operations."""
from __future__ import annotations

import polars as pl

from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol
from mountainash.typespec.converters import _resolve_field_native
from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.core.dtypes import TypeTarget

def _invalid_nested(expr, field: FieldSpec):
    if field.type is UniversalType.OBJECT and field.object_fields:
        invalid = pl.lit(False)
        for child in field.object_fields:
            invalid = invalid | _invalid_nested(expr.struct.field(child.name), child)
        return expr.is_not_null() & invalid
    if field.type is UniversalType.ARRAY and field.item_object_fields:
        item_invalid = pl.lit(False)
        element = pl.element()
        for child in field.item_object_fields:
            item_invalid = item_invalid | _invalid_nested(element.struct.field(child.name), child)
        return expr.is_not_null() & expr.list.eval(item_invalid).list.any().fill_null(False)
    dtype = _resolve_field_native(field, TypeTarget.POLARS)
    return expr.is_not_null() & expr.cast(dtype, strict=False).is_null()

class MountainAshPolarsScalarStructExpressionSystem(PolarsBaseExpressionSystem, MountainAshScalarStructExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of struct field access."""
    def cast_struct(
        self,
        x,
        /,
        *,
        fields: tuple[FieldSpec, ...],
        failure_behavior: str = "throw",
    ):
        field = FieldSpec(name="_struct", type=UniversalType.OBJECT, object_fields=list(fields))
        dtype = _resolve_field_native(field, TypeTarget.POLARS)
        result = x.cast(dtype, strict=failure_behavior != "null")
        if failure_behavior == "null":
            invalid = _invalid_nested(x, field)
            result = pl.when(x.is_null()).then(None).when(invalid).then(None).otherwise(result)
        return result

    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)
