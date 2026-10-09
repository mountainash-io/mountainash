"""Polars backend for mountainash struct operations."""
from __future__ import annotations

import polars as pl

from mountainash.core.dtypes import TypeTarget
from mountainash.core.dtypes.errors import NumericConversionError
from mountainash.core.dtypes.numeric import convert_nested_numeric, has_nested_numeric_fields
from mountainash.core.transit import BoundaryKey, transit_call
from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol
from mountainash.typespec.converters import _resolve_field_native
from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.universal_types import UniversalType


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


def _numeric_intermediate_dtype(source_dtype, field: FieldSpec):
    """Keep ordinary leaves in their source dtype until the native cast."""
    children = field.object_fields or field.item_object_fields
    if children:
        is_list = field.type is UniversalType.ARRAY
        if is_list:
            source_dtype = source_dtype.inner if isinstance(source_dtype, pl.List) else pl.Null
        source_fields = (
            {child.name: child.dtype for child in source_dtype.fields}
            if isinstance(source_dtype, pl.Struct) else {}
        )
        dtype = pl.Struct([
            pl.Field(
                child.name,
                _numeric_intermediate_dtype(source_fields.get(child.name, pl.Null), child),
            )
            for child in children
        ])
        return pl.List(dtype) if is_list else dtype
    if has_nested_numeric_fields((field,)):
        return _resolve_field_native(field, TypeTarget.POLARS)
    return source_dtype


def _cast_numeric_batch(batch, values, field: FieldSpec, dtype, failure_behavior):
    # A constructor with the final dtype can silently null ordinary leaves.
    # Only exact numeric leaves have been converted; cast the rest natively.
    converted = transit_call(
        BoundaryKey.EXPRESSION_POLARS_STRUCTURED_CALLBACK,
        pl.Series,
        batch.name,
        values,
        dtype=_numeric_intermediate_dtype(batch.dtype, field),
        trace_source=batch,
    )
    expr = pl.col(batch.name)
    result = expr.cast(dtype, strict=failure_behavior != "null")
    if failure_behavior == "null":
        invalid = _invalid_nested(expr, field)
        result = pl.when(expr.is_null()).then(None).when(invalid).then(None).otherwise(result)
    return converted.to_frame().select(result.alias(batch.name)).to_series()


def _convert_struct_batch(batch: pl.Series, field: FieldSpec, dtype, failure_behavior):
    fields = tuple(field.object_fields or ())
    values = []
    for value in batch:
        if value is None:
            values.append(None)
            continue
        try:
            values.append(convert_nested_numeric(value, fields))
        except NumericConversionError:
            if failure_behavior == "null":
                values.append(None)
            else:
                raise
    return _cast_numeric_batch(batch, values, field, dtype, failure_behavior)


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
        if has_nested_numeric_fields(fields):
            return x.map_batches(
                lambda batch: _convert_struct_batch(batch, field, dtype, failure_behavior),
                return_dtype=dtype,
                is_elementwise=True,
            )
        result = x.cast(dtype, strict=failure_behavior != "null")
        if failure_behavior == "null":
            invalid = _invalid_nested(x, field)
            result = pl.when(x.is_null()).then(None).when(invalid).then(None).otherwise(result)
        return result

    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)
