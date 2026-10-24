"""Container casts for Polars-native expressions.

Strict container casts are the native cast. Non-strict container casts keep the
existing atomic-null semantics: a non-null container with any invalid nested
value becomes null as a whole.
"""
from __future__ import annotations

import polars as pl

from .temporal_cast import cast_temporal_compatible


def _items(x: pl.Expr, source: pl.DataType, body: pl.Expr) -> pl.Expr:
    return x.arr.eval(body) if isinstance(source, pl.Array) else x.list.eval(body)


def invalid_conversion(x: pl.Expr, source: pl.DataType, target: pl.DataType) -> pl.Expr:
    """True where a non-null value (at any depth) fails the non-strict conversion."""
    if isinstance(source, (pl.List, pl.Array)) and isinstance(target, (pl.List, pl.Array)):
        item = invalid_conversion(pl.element(), source.inner, target.inner)
        evaluated = _items(x, source, item)
        anyed = evaluated.arr.any() if isinstance(source, pl.Array) else evaluated.list.any()
        return x.is_not_null() & anyed.fill_null(False)
    if isinstance(source, pl.Struct) and isinstance(target, pl.Struct):
        source_fields = dict(source.to_schema())
        invalid = pl.lit(False)
        for f in target.fields:
            if f.name in source_fields:
                invalid = invalid | invalid_conversion(
                    x.struct.field(f.name), source_fields[f.name], f.dtype,
                )
        return x.is_not_null() & invalid.fill_null(False)
    return x.is_not_null() & cast_temporal_compatible(x, target, strict=False).is_null()


def cast_container(x: pl.Expr, target: pl.DataType, *, strict: bool) -> pl.Expr:
    """Direct container cast; under non-strict, any invalid nested value nulls the whole container."""
    if strict:
        return cast_temporal_compatible(x, target, strict=True)

    def build(expr: pl.Expr, source: pl.DataType) -> pl.Expr:
        result = cast_temporal_compatible(expr, target, strict=False)
        invalid = invalid_conversion(expr, source, target)
        return pl.when(expr.is_null()).then(None).when(invalid).then(None).otherwise(result)
    return x.pipe_with_dtype(build)
