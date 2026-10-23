"""Polars backend for mountainash struct operations."""
from __future__ import annotations

from collections.abc import Mapping

import polars as pl

from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol
from mountainash.typespec.converters import resolve_native_type
from mountainash.typespec.spec import FieldDefinition
from mountainash.core.dtypes import TypeTarget
from ..temporal_cast import cast_temporal_compatible


def _declared_children(field: FieldDefinition) -> Mapping[str, FieldDefinition]:
    return field.fields if isinstance(field.fields, Mapping) else {}


def _invalid_nested(expr, field: FieldDefinition):
    children = _declared_children(field)
    if children:
        invalid = pl.lit(False)
        for name, child in children.items():
            invalid = invalid | _invalid_nested(expr.struct.field(name), child)
        return expr.is_not_null() & invalid
    if isinstance(field.element, FieldDefinition):
        item_invalid = _invalid_nested(pl.element(), field.element)
        if field.dimensions is not None:
            evaluated = expr.arr.eval(item_invalid).arr.any()
        else:
            evaluated = expr.list.eval(item_invalid).list.any()
        return expr.is_not_null() & evaluated.fill_null(False)
    dtype = resolve_native_type(field, TypeTarget.POLARS)
    return expr.is_not_null() & cast_temporal_compatible(expr, dtype, strict=False).is_null()

class MountainAshPolarsScalarStructExpressionSystem(PolarsBaseExpressionSystem, MountainAshScalarStructExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of struct field access."""
    def cast_struct(
        self,
        x,
        /,
        *converted_fields,
        fields: Mapping[str, FieldDefinition],
        failure_behavior: str = "throw",
    ):
        field = FieldDefinition(fields=fields)
        dtype = resolve_native_type(field, TypeTarget.POLARS)
        if converted_fields:
            validity = converted_fields[len(fields)] if len(converted_fields) > len(fields) else None
            result = pl.struct([
                value.alias(name)
                for name, value in zip(fields, converted_fields[:len(fields)], strict=True)
            ]).cast(dtype, strict=failure_behavior != "null")
            result = pl.when(x.is_null()).then(pl.lit(None, dtype=dtype)).otherwise(result)
            if validity is not None:
                result = pl.when(validity).then(result).otherwise(pl.lit(None, dtype=dtype))
        else:
            result = cast_temporal_compatible(x, dtype, strict=failure_behavior != "null")
        if failure_behavior == "null" and not converted_fields:
            invalid = _invalid_nested(x, field)
            result = pl.when(x.is_null()).then(None).when(invalid).then(None).otherwise(result)
        return result
    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)
