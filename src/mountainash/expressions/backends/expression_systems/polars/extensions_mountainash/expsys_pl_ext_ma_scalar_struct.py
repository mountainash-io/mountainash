"""Polars backend for mountainash struct operations."""
from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol
from mountainash.typespec.converters import _collection_item, _resolve_field_native, declared_fields
from mountainash.typespec.spec import FieldSpec
from mountainash.core.dtypes import TypeTarget
from ..temporal_cast import cast_temporal_compatible

if TYPE_CHECKING:
    from collections.abc import Mapping


def _invalid_nested(expr, field: FieldSpec, *, field_name: str):
    children = declared_fields(field)
    if children:
        invalid = pl.lit(False)
        for name, child in children.items():
            invalid = invalid | _invalid_nested(
                expr.struct.field(name), child, field_name=name,
            )
        return expr.is_not_null() & invalid
    element = _collection_item(field)
    if element is not None:
        item_invalid = _invalid_nested(pl.element(), element, field_name=field_name)
        def reduce_invalid(value, native):
            fixed = isinstance(native, pl.Array)
            mapped = value.arr.eval(item_invalid) if fixed else value.list.eval(item_invalid)
            return (mapped.arr.any() if fixed else mapped.list.any()).fill_null(False)

        return expr.is_not_null() & expr.pipe_with_dtype(reduce_invalid)
    dtype = _resolve_field_native(field, TypeTarget.POLARS, field_name=field_name)
    return expr.is_not_null() & cast_temporal_compatible(expr, dtype, strict=False).is_null()

class MountainAshPolarsScalarStructExpressionSystem(PolarsBaseExpressionSystem, MountainAshScalarStructExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of struct field access."""
    def cast_struct(
        self,
        x,
        /,
        *converted_fields,
        fields: Mapping[str, FieldSpec],
        failure_behavior: str = "throw",
    ):
        field = FieldSpec(fields=fields)
        dtype = _resolve_field_native(field, TypeTarget.POLARS, field_name="struct")
        if converted_fields:
            names = tuple(fields)
            validity = converted_fields[len(names)] if len(converted_fields) > len(names) else None
            result = pl.struct([
                value.alias(name)
                for name, value in zip(names, converted_fields[:len(names)], strict=True)
            ]).cast(dtype, strict=failure_behavior != "null")
            result = pl.when(x.is_null()).then(pl.lit(None, dtype=dtype)).otherwise(result)
            if validity is not None:
                result = pl.when(validity).then(result).otherwise(pl.lit(None, dtype=dtype))
        else:
            result = cast_temporal_compatible(x, dtype, strict=failure_behavior != "null")
        if failure_behavior == "null" and not converted_fields:
            invalid = _invalid_nested(x, field, field_name="struct")
            result = pl.when(x.is_null()).then(None).when(invalid).then(None).otherwise(result)
        return result
    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)
